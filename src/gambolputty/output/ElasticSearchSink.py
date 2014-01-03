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
class ElasticSearchSink(BaseModule.BaseModule):
    """
    Store the data dictionary in an elasticsearch index.

    The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
    Requests will the be loadbalanced via round robin.

    nodes: configures the elasticsearch nodes.
    index_prefix: es index prefix to use, will be appended with '%Y.%m.%d'.
    index_name: sets a fixed name for the es index.
    doc_id: sets the es document id for the committed event data.
    replication: can be either 'sync' or 'async'.
    store_interval_in_secs: sending data to es in x seconds intervals.
    max_waiting_events: sending data to es if event count is above even if store_interval_in_secs is not reached.
    backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration example:

    - module: ElasticSearchSink
        configuration:
          nodes: ["localhost:9200"]             # <type: list; is: required>
          index_prefix: agora_access-               # <default: 'gambolputty-'; type: string; is: required if index_name is False else optional>
          index_name: "Fixed index name"            # <default: ""; type: string; is: required if index_prefix is False else optional>
          doc_id: 'data'                            # <default: "data"; type: string; is: optional>
          replication: 'sync'                       # <default: "sync"; type: string; is: optional>
          store_interval_in_secs: 1                 # <default: 1; type: integer; is: optional>
          max_waiting_events: 500                   # <default: 500; type: integer; is: optional>
          backlog_size: 5000                        # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.events_container = []
        self.max_waiting_events = self.getConfigurationValue('max_waiting_events')
        self.backlog_size = self.getConfigurationValue('backlog_size')
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
        #elasticsearch.connection.Urllib3HttpConnection(maxsize=100)
        try:
            es = elasticsearch.Elasticsearch(self.getConfigurationValue('nodes'), sniff_on_start=True)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sNo index servers configured or none could be reached.Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            es = False
        return es

    def handleEvent(self, event):
        # Wait till a running store is finished to avoid strange race conditions.
        while self.is_storing:
            time.sleep(.01)
        if len(self.events_container) >= self.backlog_size:
            self.logger.warning("%sMaximum number of events (%s) in backlog reached. Dropping event.%s" % (Utils.AnsiColors.WARNING, self.backlog_size, Utils.AnsiColors.ENDC))
        self.events_container.append(event)
        if len(self.events_container) >= self.max_waiting_events:
            self.storeData(self.events_container)
        yield event

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
                doc_id = event[self.getConfigurationValue("doc_id", event)]
            except KeyError:
                doc_id = self.getConfigurationValue("doc_id", event)
            if not doc_id:
                self.logger.error("%sCould not find doc_id %s for event %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("doc_id"), event, Utils.AnsiColors.ENDC))
                continue
            doc_id = json.dumps(doc_id.strip())
            es_index = '{"index": {"_index": "%s", "_type": "%s", "_id": %s}}\n' % (index_name, event_type, doc_id)
            try:
                json_data += "%s%s\n" % (es_index,json.dumps(event))
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not json encode %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, event, etype, evalue, Utils.AnsiColors.ENDC))
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
            self.destroyEvent(event_list=events)
            self.events_container = []
        except elasticsearch.exceptions.ConnectionError:
            try:
                self.logger.warning("%sLost connection to %s. Trying to reconnect.%s" % (Utils.AnsiColors.WARNING, (self.getConfigurationValue("nodes"),index_name), Utils.AnsiColors.ENDC))
                self.es = self.connect()
            except:
                time.sleep(.5)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sServer cummunication error. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            self.logger.debug("Payload: %s" % json_data)
            time.sleep(.1)
        finally:
            self.is_storing = False