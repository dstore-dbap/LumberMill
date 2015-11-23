# -*- coding: utf-8 -*-
import sys
import time
import types

import pprint
from elasticsearch import Elasticsearch, helpers, connection
import BaseThreadedModule
import Utils
import Decorators

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
class ElasticSearch(BaseThreadedModule.BaseThreadedModule):
    """
    Get documents from ElasticSearch.

    The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
    Requests will the be loadbalanced via round robin.

    query:              The query to be executed, in json format.
    search_type:        The default search type just will return all found documents. If set to 'scan' it will return
                        'batch_size' number of found documents, emit these as new events and then continue until all
                        documents have been sent.
    field_mappings:     Which fields from the result document to add to the new event.
                        If set to 'all' the whole document will be sent unchanged.
                        If a list is provided, these fields will be copied to the new event with the same field name.
                        If a dictionary is provided, these fields will be copied to the new event with a new field name.
                        E.g. if you want "_source.data" to be copied into the events "data" field, use a mapping like:
                        "{'_source.data': 'data'}.
                        For nested values use the dot syntax as described in:
                        http://gambolputty.readthedocs.org/en/latest/introduction.html#event-field-notation
    nodes:              Configures the elasticsearch nodes.
    connection_type:    One of: 'thrift', 'http'.
    http_auth:          'user:password'.
    use_ssl:            One of: True, False.
    index_name:         Sets the index name. Timepatterns like %Y.%m.%d are allowed here.
    sniff_on_start:     The client can be configured to inspect the cluster state to get a list of nodes upon startup.
                        Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
    sniff_on_connection_fail: The client can be configured to inspect the cluster state to get a list of nodes upon failure.
                              Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
    query_interval_in_secs:   Get data to es in x seconds intervals. NOT YET IMPLEMENTED!!

    Configuration template:

    - ElasticSearch:
        query:                                    # <default: '{"query": {"match_all": {}}}'; type: string; is: optional>
        search_type:                              # <default: 'normal'; type: string; is: optional; values: ['normal', 'scan']>
        field_mappings:                           # <default: 'all'; type: string||list||dict; is: optional;>
        nodes:                                    # <type: string||list; is: required>
        connection_type:                          # <default: 'http'; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_name:                               # <default: 'gambolputty-%Y.%m.%d'; type: string; is: optional>
        sniff_on_start:                           # <default: True; type: boolean; is: optional>
        sniff_on_connection_fail:                 # <default: True; type: boolean; is: optional>
        query_interval_in_secs:                   # <default: 5; type: integer; is: optional>
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.query = self.getConfigurationValue('query')
        # Test if query is valid json.
        try:
            json.loads(self.query)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Parsing json query %s failed. Exception: %s, Error: %s." % (self.query, etype, evalue))
            self.gp.shutDown()
        self.es_nodes = self.getConfigurationValue("nodes")
        if not isinstance(self.es_nodes, list):
            self.es_nodes = [self.es_nodes]
        self.search_type = self.getConfigurationValue("search_type")
        self.field_mappings = self.getConfigurationValue("field_mappings")
        self.index_name_pattern = self.getConfigurationValue("index_name")
        self.connection_class = connection.Urllib3HttpConnection
        if self.getConfigurationValue("connection_type") == 'thrift':
            self.connection_class = connection.ThriftConnection
        self.es = self.connect()
        if not self.es:
            self.gp.shutDown()
            return

    def connect(self):
        es = False
        tries = 0
        while tries < 5 and not es:
            try:
                # Connect to es node and round-robin between them.
                self.logger.debug("Connecting to %s." % self.es_nodes)
                es = Elasticsearch(self.es_nodes,
                                     connection_class=self.connection_class,
                                     sniff_on_start=self.getConfigurationValue('sniff_on_start'),
                                     sniff_on_connection_fail=self.getConfigurationValue('sniff_on_connection_fail'),
                                     sniff_timeout=5,
                                     maxsize=20,
                                     use_ssl=self.getConfigurationValue('use_ssl'),
                                     http_auth=self.getConfigurationValue('http_auth'))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Connection to %s failed. Exception: %s, Error: %s." % (self.es_nodes,  etype, evalue))
                self.logger.warning("Waiting %s seconds before retring to connect." % ((4 + tries)))
                time.sleep(4 + tries)
                tries += 1
                continue
        if not es:
            self.logger.error("Connection to %s failed. Shutting down." % self.es_nodes)
            self.gp.shutDown()
        else:
            self.logger.debug("Connection to %s successful." % self.es_nodes)
        return es

    def run(self):
        found_documents = self.executeQuery()
        for doc in found_documents:
            # No special fields were selected.
            # Merge _source field and all other elasticsearch fields to one level.
            doc.update(doc.pop('_source'))
            if isinstance(self.field_mappings, types.ListType):
                doc = self.extractFieldsFromResultDocument(self.field_mappings, doc)
            elif isinstance(self.field_mappings, types.DictType):
                doc = self.extractFieldsFromResultDocumentWithMapping(self.field_mappings, doc)
            event = Utils.getDefaultEventDict(dict=doc, caller_class_name=self.__class__.__name__)
            self.sendEvent(event)
        self.gp.shutDown()

    def executeQuery(self):
        found_documents = []
        try:
            if self.search_type == 'scan':
                found_documents = helpers.scan(client=self.es, index=self.index_name_pattern, query=self.query, scroll="5m", timeout="5m")
            else:
                found_documents = self.es.search(index=self.index_name_pattern, body=self.query)['hits']['hits']
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Elasticsearch query %s failed. Exception: %s, Error: %s." % (self.query, etype, evalue))
        return found_documents

    def extractFieldsFromResultDocument(self, fields, document):
        document = Utils.KeyDotNotationDict(document)
        new_document = Utils.KeyDotNotationDict()
        for field in fields:
            if field not in document:
                continue
            new_document[field] = document[field]
        return new_document

    def extractFieldsFromResultDocumentWithMapping(self, field_mapping, document):
        document = Utils.KeyDotNotationDict(document)
        new_document = Utils.KeyDotNotationDict()
        for source_field, target_field in field_mapping.iteritems():
            if source_field not in document:
                continue
            new_document[target_field] = document[source_field]
        return new_document