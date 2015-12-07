import sys
import time
import extendSysPath
import ModuleBaseTestCase
import mock
import elasticsearch
import Utils
import ElasticSearchSink

class TestElasticSearchSink(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestElasticSearchSink, self).setUp(ElasticSearchSink.ElasticSearchSink(gp=mock.Mock()))
        self.es_server = 'localhost'
        self.test_index_name = "test_index"
        self.es = self.connect([self.es_server])
        try:
            self.es.indices.create(index=self.test_index_name) # ignore=[400, 404]
        except elasticsearch.exceptions.RequestError:
            self.logger.error("Could not create index %s on %s." % (self.test_index_name, self.es_server))
            self.fail()
        return

    def connect(self, nodes):
        es = False
        tries = 0
        while tries < 5 and not es:
            try:
                # Connect to es node and round-robin between them.
                es = elasticsearch.Elasticsearch(nodes,
                                                 connection_class=elasticsearch.connection.Urllib3HttpConnection,
                                                 sniff_on_start=False,
                                                 sniff_on_connection_fail=False,
                                                 sniff_timeout=5,
                                                 maxsize=20,
                                                 use_ssl=False,
                                                 http_auth=None)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Connection to %s failed. Exception: %s, Error: %s." % (nodes,  etype, evalue))
                self.logger.warning("Waiting %s seconds before retring to connect." % ((4 + tries)))
                time.sleep(4 + tries)
                tries += 1
                continue
        if not es:
            self.logger.error("Connection to %s failed. Shutting down." % (nodes))
            sys.exit()
        return es

    def testDefaultDocId(self):
        self.test_object.configure({'index_name': self.test_index_name,
                                    'nodes': [self.es_server],
                                    'batch_size': 1})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        event = Utils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered."})
        doc_id = event['gambolputty']['event_id']
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        time.sleep(1)
        try:
            result = self.es.get(index=self.test_index_name, id=doc_id)
        except elasticsearch.exceptions.NotFoundError, e:
            self.fail(e)
        self.assertEqual(type(result), dict)
        self.assertDictContainsSubset(event, result['_source'])

    def testCustomDocId(self):
        self.test_object.configure({'index_name': self.test_index_name,
                                    'nodes': [self.es_server],
                                    'doc_id': '$(event_doc_id)',
                                    'sniff_on_start': False,
                                    'store_interval_in_secs': 1})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        event = Utils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered.",
                                           'event_doc_id': 'Ewan'})
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        result = self.es.get(index=self.test_index_name, id='Ewan')
        self.assertEqual(type(result), dict)
        self.assertDictContainsSubset(event, result['_source'])

    def testCustomIndexName(self):
        self.test_object.configure({'index_name': 'testindex-%Y.%m.%d-$(gambolputty.event_type)',
                                    'nodes': [self.es_server],
                                    'sniff_on_start': False,
                                    'store_interval_in_secs': 1})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        event = Utils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered."})
        doc_id = event['gambolputty']['event_id']
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        index_name = Utils.mapDynamicValueInString('testindex-%Y.%m.%d-%(gambolputty.event_type)s', event, use_strftime=True).lower()
        result = self.es.get(index=index_name, id=doc_id)
        self.assertEqual(type(result), dict)
        self.assertDictContainsSubset(event, result['_source'])
        self.es.indices.delete(index=index_name, ignore=[400, 404])

    def __testStorageTTL(self):
        """
        Does not seem to be testable without waiting for at least 60 seconds.
        That seems to be the smallest interval the purger thread is running, no matter what I set ttl.interval to.
        The documentation @http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/modules-indices.html#indices-ttl
        does not say anything about a lower limit but testing leads me to the assumption that 60s is the lowest limit.
        """
        self.test_object.configure({'index_name': self.test_index_name,
                                    'nodes': [self.es_server],
                                    'ttl': 100,
                                    'sniff_on_start': False,
                                    'store_interval_in_secs': 1})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        # Enable ttl mapping.
        self.es.indices.close(index=self.test_index_name)
        self.es.indices.put_settings(index=self.test_index_name, body='{"ttl": {"interval" : "1s"}}')
        self.es.indices.open(index=self.test_index_name)
        self.es.indices.put_mapping(index=self.test_index_name, doc_type='Unknown', body='{"_ttl" : { "enabled" : true }}')
        event = Utils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered."})
        doc_id = event['gambolputty']['event_id']
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        try:
            result = self.es.get(index=self.test_index_name, id=doc_id)
        except elasticsearch.NotFoundError:
            self.fail("Document was not found.")
        self.assertEqual(type(result), dict)
        self.assertDictContainsSubset(event, result['_source'])
        time.sleep(2)
        try:
            result = self.es.get(index=self.test_index_name, id=doc_id)
            self.fail("Document was not deleted after ttl.")
        except elasticsearch.NotFoundError:
            pass


    def tearDown(self):
        ModuleBaseTestCase.ModuleBaseTestCase.tearDown(self)
        self.es.indices.delete(index=self.test_index_name, ignore=[400, 404])