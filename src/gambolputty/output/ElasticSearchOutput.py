# -*- coding: utf-8 -*-
from hashlib import md5
import pprint
import sys
import datetime
import time
import simplejson as json
import elasticsearch
import BaseModule
import Utils
import Decorators

@Decorators.ModuleDocstringParser
class ElasticSearchOutput(BaseModule.BaseModule):
    """
    Store the data dictionary in an elasticsearch index.

    The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
    Requests will the be loadbalanced via round robin.

    Configuration example:

    - module: ElasticSearchOutput
        configuration:
          nodes: ["es-01.dbap.de:9200"]             # <type: list; is: required>
          index_prefix: agora_access-               # <default: 'gambolputty-'; type: string; is: required if index_name is False else optional>
          index_name: "Fixed index name"            # <default: ""; type: string; is: required if index_prefix is False else optional>
          doc_id: 'data'                            # <default: "data"; type: string; is: optional>
          replication: 'sync'                       # <default: "sync"; type: string; is: optional>
          store_interval_in_secs: 1                 # <default: 1; type: integer; is: optional>
          max_waiting_events: 500                   # <default: 500; type: integer; is: optional>
      receivers:
        - NextModule
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.events_container = []
        self.max_waiting_events = self.getConfigurationValue('max_waiting_events')
        self.es = self.connect()
        if not self.es:
            self.gp.shutDown()
            return
        self.is_storing = False
        self.timed_store_func = self.getTimedStoreFunc()
        self.timed_store_func(self)

    def getTimedStoreFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('store_interval_in_secs'))
        def timedStoreData(self):
            while self.is_storing:
                time.sleep(.01)
            self.storeData(self.events_container)
        return timedStoreData

    def connect(self):
        es = False
        # Connect to es node and round-robin between them.
        elasticsearch.connection.Urllib3HttpConnection(maxsize=100)
        try:
            es = elasticsearch.Elasticsearch(self.getConfigurationValue('nodes'), niff_on_start=True)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sNo index servers configured or none could be reached.Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            es = False
        return es

    def handleEvent(self, event):
        # Wait till a running store is finished to avoid strange race conditions.
        while self.is_storing:
            time.sleep(.01)
        # Append event to internal data container
        self.events_container.append(event)
        if len(self.events_container) >= self.max_waiting_events:
            self.storeData(self.events_container)

    def dataToElasticSearchJson(self, index_name, events):
        """
        Format data for elasticsearch bulk update
        """
        json_data = ""
        for event in events:
            try:
                event_type = event['event_type']
            except KeyError:
                event_type = 'Unknown'
            try:
                doc_id = event[self.getConfigurationValue("doc_id", event)].strip()
            except KeyError:
                doc_id = self.getConfigurationValue("doc_id", event).strip()
            doc_id = json.dumps(doc_id)
            es_index = '{"index": {"_index": "%s", "_type": "%s", "_id": %s}}\n' % (index_name, event_type, doc_id)
            try:
                json_data += "%s%s\n" % (es_index,json.dumps(event))
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not json encode %s. Exception: %s, Error: %s." % (event, etype, evalue))
        return json_data

    def storeData(self, events):
        if len(events) == 0:
            return
        self.is_storing = True
        if self.getConfigurationValue("index_name"):
            index_name = self.getConfigurationValue("index_name")
        else:
            index_name = "%s%s" % (self.getConfigurationValue("index_prefix"), datetime.date.today().strftime('%Y.%m.%d'))

        json_data = self.dataToElasticSearchJson(index_name, events)
        try:
            self.es.bulk(body=json_data, replication=self.getConfigurationValue("replication"))
        except Exception, e:
            try:
                self.logger.error("Server cummunication error: %s" % e[1])
                self.logger.error("%s/%s" % (self.getConfigurationValue("nodes"),index_name))
                self.logger.error("Payload: %s" % json_data)
            except:
                self.logger.error("Server cummunication error: %s" % e)
            finally:
                # Try to reconnect
                self.es = self.connect()
                time.sleep(.1)
        finally:
            self.events_container = []
            self.is_storing = False