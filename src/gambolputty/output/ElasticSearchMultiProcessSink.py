# -*- coding: utf-8 -*-
import pprint
import sys
import datetime
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

    format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send.
    nodes: configures the elasticsearch nodes.
    connection_type: one of: 'thrift', 'http'
    http_auth: 'user:password'
    use_ssl: one of: True, False
    index_prefix: es index prefix to use, will be appended with '%Y.%m.%d'.
    index_name: sets a fixed name for the es index.
    doc_id: sets the es document id for the committed event data.
    ttl: When set, documents will be automatically deleted after ttl expired.
         Can either set time in microseconds or elasticsearch date format, e.g.: 1d, 15m etc.
         This feature needs to be enabled for the index.
         @See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-ttl-field.html
    consistency: one of: 'one', 'quorum', 'all'
    replication: one of: 'sync', 'async'.
    store_interval_in_secs: sending data to es in x seconds intervals.
    batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration example:

    - ElasticSearchMultiProcessSink:
        format:                                   # <default: None; type: None||string; is: optional>
        nodes:                                    # <type: list; is: required>
        connection_type:                          # <default: "http"; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_prefix:                             # <default: 'gambolputty-'; type: string; is: required if index_name is False else optional>
        index_name:                               # <default: ""; type: string; is: required if index_prefix is False else optional>
        doc_id:                                   # <default: "%(gambolputty.event_id)s"; type: string; is: optional>
        ttl:                                      # <default: None; type: None||string; is: optional>
        consistency:                              # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication:                              # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs:                   # <default: 5; type: integer; is: optional>
        batch_size:                               # <default: 500; type: integer; is: optional>
        backlog_size:                             # <default: 5000; type: integer; is: optional>
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
        try:
            # Connect to es node and round-robin between them.
            es = elasticsearch.Elasticsearch(self.getConfigurationValue('nodes'),
                                             connection_class=self.connection_class,
                                             sniff_on_start=True, sniff_timeout=1, maxsize=20,
                                             use_ssl=self.getConfigurationValue('use_ssl'),
                                             http_auth=self.getConfigurationValue('http_auth'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sNo index servers configured or none could be reached.Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
            es = False
        return es

    def handleEvent(self, event):
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
        if UnicodeBuilder:
            json_data = UnicodeBuilder()
        else:
            json_data = []
        for event in events:
            try:
                event_type = event['event_type']
            except KeyError:
                event_type = 'Unknown'
            doc_id = self.getConfigurationValue("doc_id", event)
            if not doc_id:
                self.logger.error("%sCould not find doc_id %s for event %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("doc_id"), event, Utils.AnsiColors.ENDC))
                continue
            doc_id = json.dumps(doc_id.strip())
            if self.ttl:
                event['_ttl'] = self.ttl
            header = '{"index": {"_index": "%s", "_type": "%s", "_id": %s}}' % (index_name, event_type, doc_id)
            json_data.append("\n".join((header, json.dumps(event), "\n")))
        if UnicodeBuilder:
            json_data = json_data.build()
        else:
            try:
                json_data = "".join(json_data)
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not json encode %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, event, etype, evalue, Utils.AnsiColors.ENDC))
        return json_data

    def storeData(self, events):
        if self.getConfigurationValue("index_name"):
            index_name = self.getConfigurationValue("index_name")
        else:
            index_name = "%s%s" % (self.getConfigurationValue("index_prefix"), datetime.date.today().strftime('%Y.%m.%d'))
        json_data = self.dataToElasticSearchJson(index_name, events)
        try:
            #started = time.time()
            # Bulk update of 500 events took 0.139621019363.
            self.es.bulk(body=json_data, consistency=self.consistency, replication=self.replication)
            #print "Bulk update of %s events took %s." % (len(events), time.time() - started)
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
                tries = 0
                self.es = False
                while tries < 5 and not self.es:
                    time.sleep(7)
                    self.logger.warning("%sLost connection to %s.Trying to reconnect...%s" % (Utils.AnsiColors.WARNING, self.getConfigurationValue("nodes"), Utils.AnsiColors.ENDC))
                    # Try to reconnect.
                    self.es = self.connect()
                    tries += 1
                if not self.es:
                    self.logger.error("%sReconnect failed. Shutting down.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
                else:
                    self.logger.info("%sReconnection to %s successful.%s" % (Utils.AnsiColors.LIGHTBLUE, self.getConfigurationValue("nodes"), Utils.AnsiColors.ENDC))

    def shutDown(self, silent=False):
        try:
            self.buffer.flush()
        except:
            pass
        BaseMultiProcessModule.BaseMultiProcessModule.shutDown(self, silent)