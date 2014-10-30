# -*- coding: utf-8 -*-
import os
import sys
import time
import elasticsearch
import BaseMultiProcessModule
import Utils
import Decorators
try:
    from __pypy__.builders import UnicodeBuilder
except ImportError:
    UnicodeBuilder = None

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

@Decorators.ModuleDocstringParser
class ElasticSearchMultiProcessSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Store the data dictionary in an elasticsearch index.

    The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
    Requests will the be loadbalanced via round robin.

    format:     Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'.
                If not set the whole event dict is send.
    nodes:      Configures the elasticsearch nodes.
    connection_type:    One of: 'thrift', 'http'
    http_auth:  'user:password'
    use_ssl:    One of: True, False
    index_name: Sets the index name. Timepatterns like %Y.%m.%d are allowed here.
    doc_id:     Sets the es document id for the committed event data.
    routing:    Sets a routing value (@see: http://www.elasticsearch.org/blog/customizing-your-document-routing/)
                Timepatterns like %Y.%m.%d are allowed here.
    ttl:        When set, documents will be automatically deleted after ttl expired.
                Can either set time in microseconds or elasticsearch date format, e.g.: 1d, 15m etc.
                This feature needs to be enabled for the index.
                @See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-ttl-field.html
    consistency:    One of: 'one', 'quorum', 'all'
    replication:    One of: 'sync', 'async'.
    store_interval_in_secs:     Send data to es in x seconds intervals.
    batch_size: Sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size:   Maximum count of events waiting for transmission. If backlog size is exceeded no new events will be processed.

    Configuration template:

    - ElasticSearchMultiProcessSink:
        format:                                   # <default: None; type: None||string; is: optional>
        nodes:                                    # <type: list; is: required>
        connection_type:                          # <default: "http"; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_name:                               # <default: 'gambolputty-%Y.%m.%d'; type: string; is: optional>
        doc_id:                                   # <default: "%(gambolputty.event_id)s"; type: string; is: optional>
        routing:                                  # <default: None; type: None||string; is: optional>
        ttl:                                      # <default: None; type: None||string; is: optional>
        consistency:                              # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication:                              # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs:                   # <default: 5; type: integer; is: optional>
        batch_size:                               # <default: 500; type: integer; is: optional>
        backlog_size:                             # <default: 1000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.format = self.getConfigurationValue('format')
        self.replication = self.getConfigurationValue("replication")
        self.consistency = self.getConfigurationValue("consistency")
        self.ttl = self.getConfigurationValue("ttl")
        self.index_name_pattern = self.getConfigurationValue("index_name")
        self.routing_pattern = self.getConfigurationValue("routing")
        self.doc_id_pattern = self.getConfigurationValue("doc_id")
        self.connection_class = elasticsearch.connection.ThriftConnection
        if self.getConfigurationValue("connection_type") == 'http':
            self.connection_class = elasticsearch.connection.Urllib3HttpConnection
        self.es = self.connect()
        if not self.es:
            self.gp.shutDown()
            return

    def run(self):
        self.buffer = Utils.Buffer(self.getConfigurationValue('batch_size'), self.storeData, self.getConfigurationValue('store_interval_in_secs'), maxsize=self.getConfigurationValue('backlog_size'))
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def connect(self):
        es = False
        tries = 0
        while tries < 5 and not es:
            try:
                # Connect to es node and round-robin between them.
                self.logger.debug("%sConnecting to %s.%s" % (Utils.AnsiColors.LIGHTBLUE, self.getConfigurationValue("nodes"), Utils.AnsiColors.ENDC))
                es = elasticsearch.Elasticsearch(self.getConfigurationValue('nodes'),
                                                 connection_class=self.connection_class,
                                                 sniff_on_start=True,
                                                 sniff_on_connection_fail=True,
                                                 sniff_timeout=10,
                                                 maxsize=20,
                                                 use_ssl=self.getConfigurationValue('use_ssl'),
                                                 http_auth=self.getConfigurationValue('http_auth'))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("%sConnection to %s failed. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, self.getConfigurationValue("nodes"),  etype, evalue, Utils.AnsiColors.ENDC))
                self.logger.warning("%sWaiting %s seconds before retring to connect.%s" % (Utils.AnsiColors.WARNING, (4 + tries), Utils.AnsiColors.ENDC))
                time.sleep(4 + tries)
                tries += 1
                continue
        if not es:
            self.logger.error("%sConnection to %s failed. Shutting down.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("nodes"), Utils.AnsiColors.ENDC))
            self.gp.shutDown()
        else:
            self.logger.debug("%sConnection to %s successful.%s" % (Utils.AnsiColors.LIGHTBLUE, self.getConfigurationValue("nodes"), Utils.AnsiColors.ENDC))
        return es

    def handleEvent(self, event):
        event['gambolputty']['modpid'] = os.getpid()
        if self.format:
            publish_data = self.getConfigurationValue('format', event)
        else:
            publish_data = event
        self.buffer.append(publish_data)
        yield None

    def dataToElasticSearchJson(self, index_name, events):
        """
        Format data for elasticsearch bulk update
        """
        json_data = []
        for event in events:
            event_type = event['gambolputty']['event_type'] if 'event_type' in event['gambolputty'] else 'Unknown'
            doc_id = Utils.mapDynamicValue(self.doc_id_pattern, event)
            routing = Utils.mapDynamicValue(self.routing_pattern, use_strftime=True)
            if not doc_id:
                self.logger.error("%sCould not find doc_id %s for event %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("doc_id"), event, Utils.AnsiColors.ENDC))
                continue
            doc_id = json.dumps(doc_id.strip())
            if self.ttl:
                event['_ttl'] = self.ttl
            if not self.routing_pattern:
                header = '{"index": {"_index": "%s", "_type": "%s", "_id": %s}}' % (index_name, event_type, doc_id)
            else:
                header = '{"index": {"_index": "%s", "_type": "%s", "_id": %s, "_routing": "%s"}}' % (index_name, event_type, doc_id, routing)
            try:
                json_data.append("\n".join((header, json.dumps(event), "\n")))
            except:
                pass
        try:
            json_data = "".join(json_data)
        except UnicodeDecodeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not json encode %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, event, etype, evalue, Utils.AnsiColors.ENDC))
        return json_data

    def storeData(self, events):
        index_name = Utils.mapDynamicValue(self.index_name_pattern, use_strftime=True)
        json_data = self.dataToElasticSearchJson(index_name, events)
        try:
            #started = time.time()
            # Bulk update of 500 events took 0.139621019363.
            self.es.bulk(body=json_data, consistency=self.consistency, replication=self.replication)
            #print("%s(%s): Bulk update of %s events took %s." % (self, self.process_id, len(events), time.time() - started))
            return True
        except elasticsearch.exceptions.ConnectionError:
            try:
                self.logger.warning("%sLost connection to %s. Trying to reconnect.%s" % (Utils.AnsiColors.WARNING, (self.getConfigurationValue("nodes"),index_name), Utils.AnsiColors.ENDC))
                self.es = self.connect()
            except:
                time.sleep(.5)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sServer communication error. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            self.logger.debug("Payload: %s" % json_data)
            if "Broken pipe" in evalue or "Connection reset by peer" in evalue:
                self.es = self.connect()

    def shutDown(self):
        try:
            self.buffer.flush()
        except:
            pass
        BaseMultiProcessModule.BaseMultiProcessModule.shutDown(self)