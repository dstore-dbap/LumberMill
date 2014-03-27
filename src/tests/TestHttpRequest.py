import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import HttpRequest
import RedisStore

class TestHttpRequest(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestHttpRequest, self).setUp(HttpRequest.HttpRequest(gp=ModuleBaseTestCase.MockGambolPutty()))

    def testQuery(self):
        self.test_object.configure({'url': 'http://www.google.com'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1'})):
            self.assertTrue('gambolputty_http_request' in event and len(event['gambolputty_http_request']) > 0)

    def testQueryTargetField(self):
        self.test_object.configure({'url': 'http://www.google.com',
                                    'target_field': 'Johann Gambolputty'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1'})):
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testDynamicQueryTargetField(self):
        self.test_object.configure({'url': '%(schema)s://%(host)s',
                                    'target_field': 'Johann Gambolputty'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        data_dict = Utils.getDefaultEventDict({'TreeNodeID': '1',
                                              'schema': 'http',
                                              'host': 'www.google.com'})
        for event in self.test_object.handleEvent(data_dict):
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testHttpsQuery(self):
        self.test_object.configure({'url': 'https://www.google.com'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1'})):
            self.assertTrue('gambolputty_http_request' in event and len(event['gambolputty_http_request']) > 0)

    def testHttpsQueryDynamicTargetField(self):
        self.test_object.configure({'url': 'https://www.google.com',
                                    'target_field': '%(surname)s Gambolputty'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1', 'surname': 'Johann'})):
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testRedis(self):
        rc = RedisStore.RedisStore(gp=mock.Mock())
        rc.configure({'server': 'es-01.dbap.de'})
        self.test_object.gp.modules = {'RedisStore': {'instances': [rc]}}
        self.test_object.configure({'url': 'https://www.google.com',
                                    'target_field': '%(surname)s Gambolputty',
                                    'redis_store': 'RedisStore',
                                    'redis_key': '%(surname)s',
                                    'redis_ttl': 5})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        return
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1', 'surname': 'Johann'})):
            redis_entry = self.test_object.redis_client.getValue('Johann')
            self.assertEquals(event['Johann Gambolputty'], redis_entry)