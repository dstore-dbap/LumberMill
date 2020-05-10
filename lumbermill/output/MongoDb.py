# -*- coding: utf-8 -*-
import pymongo
import sys

import time

from constants import IS_PYPY
from BaseThreadedModule import BaseThreadedModule
from utils.Buffers import Buffer
from utils.Decorators import ModuleDocstringParser
from utils.DynamicValues import mapDynamicValue, mapDynamicValueInString


@ModuleDocstringParser
class MongoDb(BaseThreadedModule):
    """
    Store incoming events in a mongodb.

    host: Mongodb server.
    database: Mongodb database name.
    collection: Mongodb collection name. Timepatterns like %Y.%m.%d and dynamic values like $(bar) are allowed here.
    optinonal_connection_params: Other optional parameters as documented in https://api.mongodb.org/python/current/api/pymongo/mongo_client.html
    format:     Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'.
                If not set the whole event dict is send.
    doc_id:     Sets the document id for the committed event data.
    store_interval_in_secs:     Send data to es in x seconds intervals.
    batch_size: Sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size:   Maximum count of events waiting for transmission. If backlog size is exceeded no new events will be processed.

    Configuration template:

    - output.MongoDb:
       host:                            # <default: 'localhost:27017'; type: string; is: optional>
       database:                        # <default: 'lumbermill'; type: string; is: optional>
       collection:                      # <default: 'lumbermill-%Y.%m.%d'; type: string; is: optional>
       optinonal_connection_params:     # <default: {'serverSelectionTimeoutMS': 5}; type: dictionary; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
       doc_id:                          # <default: '$(lumbermill.event_id)'; type: string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        self.collection = self.getConfigurationValue('collection')
        self.database = self.getConfigurationValue('database')
        self.doc_id_pattern = self.getConfigurationValue("doc_id")

    def getStartMessage(self):
        return "DB: %s. Max buffer size: %d" % (self.getConfigurationValue('database'), self.getConfigurationValue('backlog_size'))

    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        # Init monogdb client after fork.
        self.mongodb = self.connect()
        if not self.mongodb:
            self.lumbermill.shutDown()
            return
        # As the buffer uses a threaded timed function to flush its buffer and thread will not survive a fork, init buffer here.
        self.buffer = Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))

    def connect(self):
        try:
            mongodb_client = pymongo.MongoClient(self.getConfigurationValue('host'), **self.getConfigurationValue('optinonal_connection_params'))
            self.logger.debug(str(mongodb_client.server_info()))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Connection to %s failed. Exception: %s, Error: %s." % (self.getConfigurationValue('host'), etype, evalue))
        if not mongodb_client:
            self.logger.error("Connection to %s failed. Shutting down." % self.getConfigurationValue('host'))
            self.lumbermill.shutDown()
        else:
            self.logger.debug("Connection to %s successful." % self.getConfigurationValue('host'))
        return mongodb_client

    def handleEvent(self, event):
        if self.format:
            publish_data = self.getConfigurationValue('format', event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None

    def storeData(self, events):
        mongo_db = self.mongodb[self.database]
        bulk_objects = {}
        for event in events:
            collection_name = mapDynamicValueInString(self.collection, event, use_strftime=True).lower()
            doc_id = mapDynamicValue(self.doc_id_pattern, event)
            if not doc_id:
                self.logger.error("Could not find doc_id %s for event %s." % (self.doc_id_pattern, event))
                continue
            event['_id'] = doc_id
            if collection_name not in bulk_objects.keys():
                bulk_objects[collection_name] = mongo_db[collection_name].initialize_ordered_bulk_op()
            try:
                bulk_objects[collection_name].insert(event)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Server communication error. Exception: %s, Error: %s." % (etype, evalue))
                self.logger.debug("Payload: %s" % event)
                if "Broken pipe" in evalue or "Connection reset by peer" in evalue:
                    self.mongodb = self.connect()
        for collection_name, bulk_object in bulk_objects.items():
            try:
                result = bulk_object.execute()
                self.logger.debug(str(result))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Server communication error. Exception: %s, Error: %s." % (etype, evalue))

    def shutDown(self):
        try:
            self.buffer.flush()
        except:
            pass
        BaseThreadedModule.shutDown(self)
