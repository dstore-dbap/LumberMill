# -*- coding: utf-8 -*-
from hashlib import md5
import sys
import socket
import traceback
import Queue
import datetime
import time
import simplejson as json
import elasticsearch
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class ElasticSearchOutput(BaseThreadedModule.BaseThreadedModule):
    """
    Store the data dictionary in an elasticsearch index.

    The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
    Requests will the be loadbalanced via round robin.

    Configuration example:

    - module: ElasticSearchOutput
        configuration:
          nodes: ["es-01.dbap.de:9200"]             # <type: list; is: required>
          index-prefix: agora_access-               # <default: 'gambolputty-'; type: string; is: optional>
          index-name: "Fixed index name"            # <default: ""; type: string; is: optional>
          store-data-interval: 50                   # <default: 50; type: integer; is: optional>
          store-data-idle: 1                        # <default: 1; type: integer; is: optional>
      receivers:
        - NextModule
    """
    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.events_container = []
        self.store_data_interval = self.getConfigurationValue('store-data-interval')
        self.store_data_idle = self.getConfigurationValue('store-data-idle')
        self.es = self.connect()
        if not self.es:
            self.logger.error("No index servers configured or none could be reached.")
            self.gp.shutDown()
            return False

    def connect(self):
        es = False
        # Connect to es node and round-robin between them.
        try:
            es = elasticsearch.Elasticsearch(self.getConfigurationValue('nodes'), sniff_on_start=True)
        except:
            es = False
        return es

    def run(self):
        socket.setdefaulttimeout(25)
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        if self.getConfigurationValue("index-name"):
            self.logger.info("Started ElasticSearchOutput. ES-Nodes: %s, Index-Name: %s" % (self.getConfigurationValue("nodes"), self.getConfigurationValue("index-name")))
        else:
            self.logger.info("Started ElasticSearchOutput. ES-Nodes: %s, Index-Prefix: %s" % (self.getConfigurationValue("nodes"), self.getConfigurationValue("index-prefix")))
        while self.is_alive:
            try:
                data = self.getEventFromInputQueue(timeout=self.store_data_idle)
                self.handleData(data)
            except Queue.Empty:
                if len(self.events_container) > 0:
                    self.storeData()
                    self.events_container = []
                pass
            except Exception, e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("Could not read data from input queue." )
                traceback.print_exception(exc_type, exc_value, exc_tb)
                time.sleep(.5)
            if self.output_queues and data:
                self.addEventToOutputQueues(data)

    def handleData(self, data):
        # Append event to internal data container
        self.events_container.append(data)
        if len(self.events_container) < self.store_data_interval:
            return
        self.storeData()
        self.events_container = []

    def storeData(self):
        if self.getConfigurationValue("index-name"):
            index_name = self.getConfigurationValue("index-name")
        else:
            index_name = "%s%s" % (self.getConfigurationValue("index-prefix"), datetime.date.today().strftime('%Y.%m.%d'))

        json_data = self.dataToElasticSearchJson(index_name, self.events_container)
        try:
            self.es.bulk(body=json_data)
        except Exception, e:
            try:
                self.logger.error("Server cummunication error: %s" % e[1])
                self.logger.error("%s/%s" % (self.getConfigurationValue("nodes"),index_name))
                self.logger.error("Payload: %s" % json_data)
            except:
                self.logger.error("Server cummunication error: %s" % e)
            finally:
                self.es = self.connect()
                time.sleep(.1)
            return

    def dataToElasticSearchJson(self, index_name, data):
        """
        Format data for elasticsearch bulk update
        """
        json_data = ""
        for datarow in data:
            if 'event_type' not in datarow:
                continue
            es_index = '{"index": {"_index": "%s", "_type": "%s", "_id": "%s"}}\n' % (index_name, datarow['event_type'], md5(datarow['data']).hexdigest())
            try:
                json_data += "%s%s\n" % (es_index,json.dumps(datarow))
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not  json encode %s. Exception: %s, Error: %s." % (datarow, etype, evalue))
        return json_data