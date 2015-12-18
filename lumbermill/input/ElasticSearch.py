# -*- coding: utf-8 -*-
import logging
import sys
import time
import types
import requests
from elasticsearch import Elasticsearch, connection
from ctypes import c_char_p
from multiprocessing import Manager, Lock

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.constants import IS_PYPY
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DynamicValues import mapDynamicValue

# For pypy the default json module is the fastest.
if IS_PYPY:
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
class ElasticSearch(BaseThreadedModule):
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
                        http://lumbermill.readthedocs.org/en/latest/introduction.html#event-field-notation
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
       query:                           # <default: '{"query": {"match_all": {}}}'; type: string; is: optional>
       search_type:                     # <default: 'normal'; type: string; is: optional; values: ['normal', 'scan']>
       batch_size:                      # <default: 1000; type: integer; is: optional>
       field_mappings:                  # <default: 'all'; type: string||list||dict; is: optional;>
       nodes:                           # <type: string||list; is: required>
       connection_type:                 # <default: 'urllib3'; type: string; values: ['urllib3', 'requests']; is: optional>
       http_auth:                       # <default: None; type: None||string; is: optional>
       use_ssl:                         # <default: False; type: boolean; is: optional>
       index_name:                      # <default: 'lumbermill-%Y.%m.%d'; type: string; is: optional>
       sniff_on_start:                  # <default: True; type: boolean; is: optional>
       sniff_on_connection_fail:        # <default: True; type: boolean; is: optional>
       query_interval_in_secs:          # <default: 5; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method.
        BaseThreadedModule.configure(self, configuration)
        # Set log level for elasticsarch library if configured to other than default.
        if self.getConfigurationValue('log_level') != 'info':
            logging.getLogger('elasticsearch').setLevel(self.logger.level)
            logging.getLogger('requests').setLevel(self.logger.level)
        else:
            logging.getLogger('elasticsearch').setLevel(logging.WARN)
            logging.getLogger('requests').setLevel(logging.WARN)
        self.query = self.getConfigurationValue('query')
        # Test if query is valid json.
        try:
            json.loads(self.query)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Parsing json query %s failed. Exception: %s, Error: %s." % (self.query, etype, evalue))
            self.lumbermill.shutDown()
        self.search_type = self.getConfigurationValue('search_type')
        self.batch_size = self.getConfigurationValue('batch_size')
        self.field_mappings = self.getConfigurationValue('field_mappings')
        self.es_nodes = self.getConfigurationValue('nodes')
        if not isinstance(self.es_nodes, list):
            self.es_nodes = [self.es_nodes]
        self.index_name_pattern = self.getConfigurationValue('index_name')
        self.index_name = mapDynamicValue(self.index_name_pattern, use_strftime=True).lower()
        if self.getConfigurationValue("connection_type") == 'urllib3':
            self.connection_class = connection.Urllib3HttpConnection
        elif self.getConfigurationValue('connection_type') == 'requests':
            self.connection_class = connection.RequestsHttpConnection
        self.lock = Lock()
        self.manager = Manager()
        if self.search_type == 'scan':
            self.can_run_forked = True
            scroll_id = self.getInitalialScrollId()
            if not scroll_id:
                self.lumbermill.shutDown()
            self.shared_scroll_id = self.manager.Value(c_char_p, scroll_id)
        elif self.search_type == 'normal':
            self.query_from = 0
            self.query = json.loads(self.query)
            self.query['size'] = self.batch_size

    def getInitalialScrollId(self):
        scroll_id = None
        try:
            response = requests.get('http://%s/%s/_search?search_type=scan&scroll=1m&size=%s' % (self.es_nodes[0], self.index_name, self.batch_size), data=self.query)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not initialize scan search. Exception: %s, Error: %s." % (etype, evalue))
        try:
            results = json.loads(response.text)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not parse query response. Exception: %s, Error: %s." % (etype, evalue))
        if '_scroll_id' in results:
            scroll_id = results['_scroll_id']
        else:
            self.logger.error("Could not get initial scroll id. Response: %s." % results)
        return scroll_id

    def initAfterFork(self):
        BaseThreadedModule.initAfterFork(self)
        if self.search_type == 'scan':
            self.simple_es_client = requests.Session()
        elif self.search_type == 'normal':
            self.es = self.connect()

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
            self.lumbermill.shutDown()
        else:
            self.logger.debug("Connection to %s successful." % self.es_nodes)
        return es

    def run(self):
        while self.alive:
            if self.search_type == 'scan':
                found_documents = self.executeScrollQuery()
            elif self.search_type == 'normal':
                found_documents = self.executeQuery()
            if not found_documents:
                self.alive = False
                break
            for doc in found_documents:
                # No special fields were selected.
                # Merge _source field and all other elasticsearch fields to one level.
                doc.update(doc.pop('_source'))
                if isinstance(self.field_mappings, types.ListType):
                    doc = self.extractFieldsFromResultDocument(self.field_mappings, doc)
                elif isinstance(self.field_mappings, types.DictType):
                    doc = self.extractFieldsFromResultDocumentWithMapping(self.field_mappings, doc)
                event = DictUtils.getDefaultEventDict(dict=doc, caller_class_name=self.__class__.__name__)
                self.sendEvent(event)
        self.lumbermill.shutDown()

    def executeScrollQuery(self):
        """ We do not use the elasticsearch client here, since we want to exploit all cores when running multiporcessed"""
        with self.lock:
            try:
               scroll_id = self.shared_scroll_id.value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it.
                return []
            try:
                response = self.simple_es_client.get('http://%s/_search/scroll?scroll=1m' % self.es_nodes[0], data=scroll_id)
                result = json.loads(response.text)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Elasticsearch scroll query failed. Exception: %s, Error: %s." % (etype, evalue))
                return []
            # When no more hits are returned, we have processed all matching documents.
            # If an error was returned also exit.
            if not 'hits' in result or 'error' in result:
                if 'error' in result:
                    self.logger.error('Elasticsearch scroll query returned an error: %s.' % (result['error']))
                return []
            try:
                self.shared_scroll_id.value = result['_scroll_id']
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it.
                pass
        return result['hits']['hits']

    def executeQuery(self):
        self.query['from'] = self.query_from
        self.query_from = self.query_from + self.batch_size
        found_documents = []
        try:
            found_documents = self.es.search(index=self.index_name, body=self.query)['hits']['hits']
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Elasticsearch query %s failed. Exception: %s, Error: %s." % (self.query, etype, evalue))
        return found_documents

    def extractFieldsFromResultDocument(self, fields, document):
        document = DictUtils.KeyDotNotationDict(document)
        new_document = DictUtils.KeyDotNotationDict()
        for field in fields:
            if field not in document:
                continue
            new_document[field] = document[field]
        return new_document

    def extractFieldsFromResultDocumentWithMapping(self, field_mapping, document):
        document = DictUtils.KeyDotNotationDict(document)
        new_document = DictUtils.KeyDotNotationDict()
        for source_field, target_field in field_mapping.iteritems():
            if source_field not in document:
                continue
            new_document[target_field] = document[source_field]
        return new_document