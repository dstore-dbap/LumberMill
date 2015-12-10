# -*- coding: utf-8 -*-
import logging
import sys
import time
import elasticsearch

import lumbermill.Utils as Utils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.Decorators import ModuleDocstringParser

# For pypy the default json module is the fastest.
if Utils.is_pypy:
    import json
else:
    json = False
    for module_name in ['ujson', 'yajl', 'simplejson', 'json']:
        try:
            json = __import__(module_name)
            break
        except ImportError:
            pass
    if not json:
        raise ImportError


@ModuleDocstringParser
class ElasticSearchSink(BaseThreadedModule):
    """
    Store the data dictionary in an elasticsearch index.

    The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
    Requests will the be loadbalanced via round robin.

    action:     Either index or update. If update be sure to provide the correct doc_id.
    format:     Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'.
                If not set the whole event dict is send.
    nodes:      Configures the elasticsearch nodes.
    connection_type:    One of: 'thrift', 'http'.
    http_auth:  'user:password'.
    use_ssl:    One of: True, False.
    index_name: Sets the index name. Timepatterns like %Y.%m.%d and dynamic values like $(bar) are allowed here.
    doc_id:     Sets the es document id for the committed event data.
    routing:    Sets a routing value (@see: http://www.elasticsearch.org/blog/customizing-your-document-routing/)
                Timepatterns like %Y.%m.%d are allowed here.
    ttl:        When set, documents will be automatically deleted after ttl expired.
                Can either set time in milliseconds or elasticsearch date format, e.g.: 1d, 15m etc.
                This feature needs to be enabled for the index.
                @See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-ttl-field.html
    sniff_on_start: The client can be configured to inspect the cluster state to get a list of nodes upon startup.
                    Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
    sniff_on_connection_fail: The client can be configured to inspect the cluster state to get a list of nodes upon failure.
                              Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
    consistency:    One of: 'one', 'quorum', 'all'.
    store_interval_in_secs:     Send data to es in x seconds intervals.
    batch_size: Sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size:   Maximum count of events waiting for transmission. If backlog size is exceeded no new events will be processed.

    Configuration template:

    - ElasticSearchSink:
       action:                          # <default: 'index'; type: string; is: optional; values: ['index', 'update']>
       format:                          # <default: None; type: None||string; is: optional>
       nodes:                           # <type: string||list; is: required>
       connection_type:                 # <default: 'urllib3'; type: string; values: ['urllib3', 'requests']; is: optional>
       http_auth:                       # <default: None; type: None||string; is: optional>
       use_ssl:                         # <default: False; type: boolean; is: optional>
       index_name:                      # <default: 'lumbermill-%Y.%m.%d'; type: string; is: optional>
       doc_id:                          # <default: '$(lumbermill.event_id)'; type: string; is: optional>
       routing:                         # <default: None; type: None||string; is: optional>
       ttl:                             # <default: None; type: None||integer||string; is: optional>
       sniff_on_start:                  # <default: False; type: boolean; is: optional>
       sniff_on_connection_fail:        # <default: False; type: boolean; is: optional>
       consistency:                     # <default: 'quorum'; type: string; values: ['one', 'quorum', 'all']; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 500; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        for module_name in ['elasticsearch', 'urllib3', 'requests']:
            if self.getConfigurationValue('log_level') == 'info':
                logging.getLogger(module_name).setLevel(logging.WARN)
            else:
                # Set log level for elasticsarch library if configured to other than default.
                logging.getLogger(module_name).setLevel(self.logger.level)
        self.action = self.getConfigurationValue('action')
        self.format = self.getConfigurationValue('format')
        self.consistency = self.getConfigurationValue("consistency")
        self.ttl = self.getConfigurationValue("ttl")
        self.index_name = None
        self.routing_pattern = self.getConfigurationValue("routing")
        self.doc_id_pattern = self.getConfigurationValue("doc_id")
        self.es_nodes = self.getConfigurationValue("nodes")
        if not isinstance(self.es_nodes, list):
            self.es_nodes = [self.es_nodes]
        if not self.configuration_data['index_name']['contains_dynamic_value']:
            self.index_name = self.getConfigurationValue("index_name")
        else:
            self.index_name_pattern = self.getConfigurationValue("index_name")
        if self.getConfigurationValue("connection_type") == 'urllib3':
            self.connection_class = elasticsearch.connection.Urllib3HttpConnection
        elif self.getConfigurationValue("connection_type") == 'requests':
            self.connection_class = elasticsearch.connection.RequestsHttpConnection

    def getStartMessage(self):
        index_name = self.index_name if self.index_name else self.index_name_pattern
        return "Idx: %s. Max buffer size: %d" % (index_name, self.getConfigurationValue('backlog_size'))

    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        # Init es client after fork as mentioned in https://elasticsearch-py.readthedocs.org/en/master/
        self.es = self.connect()
        if not self.es:
            self.lumbermill.shutDown()
            return
        # As the buffer uses a threaded timed function to flush its buffer and thread will not survive a fork, init buffer here.
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))

    def connect(self):
        es = False
        tries = 0
        while tries < 5 and not es:
            try:
                # Connect to es node and round-robin between them.
                self.logger.debug("Connecting to %s." % self.es_nodes)
                es = elasticsearch.Elasticsearch(self.es_nodes,
                                                 connection_class=self.connection_class,
                                                 sniff_on_start=self.getConfigurationValue('sniff_on_start'),
                                                 sniff_on_connection_fail=self.getConfigurationValue('sniff_on_connection_fail'),
                                                 sniff_timeout=5,
                                                 maxsize=20,
                                                 use_ssl=self.getConfigurationValue('use_ssl'),
                                                 http_auth=self.getConfigurationValue('http_auth'))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Connection to %s failed. Exception: %s, Error: %s." % (self.es_nodes, etype, evalue))
                self.logger.warning("Waiting %s seconds before retring to connect." % ((4 + tries)))
                time.sleep(4 + tries)
                tries += 1
                continue
        if not es:
            self.logger.error("Connection to %s failed. Shutting down." % self.es_nodes)
            self.lumbermill.shutDown()
        else:
            self.logger.debug("Connection to %s successful." % self.es_nodes)
        return es

    def handleEvent(self, event):
        if self.format:
            publish_data = self.getConfigurationValue('format', event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None

    def dataToElasticSearchJson(self, events, index_name=None):
        """
        Format data for elasticsearch bulk update.
        """
        json_data = []
        for event in events:
            if not index_name:
                index_name = Utils.mapDynamicValueInString(self.index_name_pattern, event, use_strftime=True).lower()
            event_type = event['lumbermill']['event_type'] if 'event_type' in event['lumbermill'] else 'Unknown'
            doc_id = Utils.mapDynamicValue(self.doc_id_pattern, event)
            routing = Utils.mapDynamicValue(self.routing_pattern, use_strftime=True)
            if not doc_id:
                self.logger.error("Could not find doc_id %s for event %s." % (self.getConfigurationValue("doc_id"), event))
                continue
            header = {self.action: {'_index': index_name,
                                    '_type': event_type,
                                    '_id': doc_id}}
            if self.routing_pattern:
                header['index']['_routing'] = routing
            if self.ttl:
                header['index']['_ttl'] = self.ttl
            if self.action == 'update':
                event = {'doc': event}
            try:
                json_data.append("\n".join((json.dumps(header), json.dumps(event), "\n")))
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not json encode %s. Exception: %s, Error: %s." % (event, etype, evalue))
        json_data = "".join(json_data)
        return json_data

    def storeData(self, events):
        json_data = self.dataToElasticSearchJson(events, self.index_name)
        try:
            #started = time.time()
            # Bulk update of 500 events took 0.139621019363.
            self.es.bulk(body=json_data, consistency=self.consistency)
            #print("Bulk update of %s events took %s." % (len(events), time.time() - started))
            return True
        except elasticsearch.exceptions.ConnectionError:
            try:
                self.logger.warning("Lost connection to %s. Trying to reconnect." % (self.es_nodes, index_name))
                self.es = self.connect()
            except:
                time.sleep(.5)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Server communication error. Exception: %s, Error: %s." % (etype, evalue))
            self.logger.debug("Payload: %s" % json_data)
            if "Broken pipe" in evalue or "Connection reset by peer" in evalue:
                self.es = self.connect()

    def shutDown(self):
        try:
            self.buffer.flush()
        except:
            pass
        BaseThreadedModule.shutDown(self)