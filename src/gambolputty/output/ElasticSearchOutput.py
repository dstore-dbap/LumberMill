# -*- coding: utf-8 -*-
from hashlib import md5
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
          max_waiting_events: 2500                  # <default: 2500; type: integer; is: optional>
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
            return False
        self.timed_store_func = self.getTimedStoreFunc()
        self.timed_store_func(self)

    def getTimedStoreFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('store_interval_in_secs'))
        def timedStoreData(self):
            self.storeData()
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
        # Append event to internal data container
        self.events_container.append(event)
        if len(self.events_container) >= self.max_waiting_events:
            self.storeData()
        self.sendEventToReceivers(event)

    def dataToElasticSearchJson(self, index_name, events):
        """
        Format data for elasticsearch bulk update
        """
        json_data = ""
        for event in events:
            if 'event_type' not in event:
                continue
            try:
                doc_id = event[self.getConfigurationValue("doc_id", event)]
            except KeyError:
                doc_id = self.getConfigurationValue("doc_id", event)
            try:
                #es_index = '{"index": {"_index": "%s", "_type": "%s", "_id": "%s"}}\n' % (index_name, event['event_type'], md5(event[self.getConfigurationValue("doc_id_field", event)]).hexdigest())
                es_index = '{"index": {"_index": "%s", "_type": "%s", "_id": "%s"}}\n' % (index_name, event['event_type'], doc_id)
            except KeyError:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("%sCould not store data in elastic search. Document id field %s is missing in event.%s" % (Utils.AnsiColors.WARNING, doc_id, Utils.AnsiColors.ENDC))
                self.logger.warning("%sEvent: %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, event, etype, evalue, Utils.AnsiColors.ENDC))
                continue
            try:
                json_data += "%s%s\n" % (es_index,json.dumps(event))
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not json encode %s. Exception: %s, Error: %s." % (event, etype, evalue))
        return json_data

    def storeData(self):
        if len(self.events_container) == 0:
            return
        if self.getConfigurationValue("index_name"):
            index_name = self.getConfigurationValue("index_name")
        else:
            index_name = "%s%s" % (self.getConfigurationValue("index_prefix"), datetime.date.today().strftime('%Y.%m.%d'))

        json_data = self.dataToElasticSearchJson(index_name, self.events_container)
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
            return
        finally:
            self.events_container = []