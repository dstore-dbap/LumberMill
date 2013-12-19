import extendSysPath
import unittest
import ModuleBaseTestCase
import mock
import Utils
import HttpRequest
import RedisClient

class TestHttpRequest(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestHttpRequest, self).setUp(HttpRequest.HttpRequest(gp=mock.Mock()))

    def testQuery(self):
        self.test_object.configure({'url': 'http://www.google.com'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1'}))
        for event in self.receiver.getEvent():
            self.assertTrue('gambolputty_http_request' in event and len(event['gambolputty_http_request']) > 0)

    def testQueryTargetField(self):
        self.test_object.configure({'url': 'http://www.google.com',
                                    'target_field': 'Johann Gambolputty'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1'}))
        for event in self.receiver.getEvent():
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testDynamicQueryTargetField(self):
        self.test_object.configure({'url': '%(schema)s://%(host)s',
                                    'target_field': 'Johann Gambolputty'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        data_dict = Utils.getDefaultEventDict({'TreeNodeID': '1',
                                              'schema': 'http',
                                              'host': 'www.google.com'})
        self.test_object.handleEvent(data_dict)
        for event in self.receiver.getEvent():
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testHttpsQuery(self):
        self.test_object.configure({'url': 'https://www.google.com'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1'}))
        for event in self.receiver.getEvent():
            self.assertTrue('gambolputty_http_request' in event and len(event['gambolputty_http_request']) > 0)

    def testHttpsQueryDynamicTargetField(self):
        self.test_object.configure({'url': 'https://www.google.com',
                                    'target_field': '%(surname)s Gambolputty'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1', 'surname': 'Johann'}))
        for event in self.receiver.getEvent():
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testRedis(self):
        rc = RedisClient.RedisClient(gp=mock.Mock())
        rc.configure({'server': 'es-01.dbap.de'})
        self.test_object.gp.modules = {'RedisClient': {'instances': [rc]}}
        self.test_object.configure({'url': 'https://www.google.com',
                                    'target_field': '%(surname)s Gambolputty',
                                    'redis_client': 'RedisClient',
                                    'redis_key': '%(surname)s',
                                    'redis_ttl': 5})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.initRedisClient()
        self.test_object.handleEvent(Utils.getDefaultEventDict({'TreeNodeID': '1', 'surname': 'Johann'}))
        for event in self.receiver.getEvent():
            redis_entry = self.test_object.getRedisValue('Johann')
            self.assertEquals(event['Johann Gambolputty'], redis_entry)

    def __testQueueCommunication(self):
        config = {'url': 'https://www.google.com'}
        super(TestHttpRequest, self).testQueueCommunication(config)

    def __testOutputQueueFilterMatch(self):
        config = {'url': 'https://www.google.com'}
        super(TestHttpRequest, self).testOutputQueueFilterMatch(config)

    def __testWorksOnOriginal(self):
        config = {'url': 'https://www.google.com'}
        super(TestHttpRequest, self).testWorksOnOriginal(config)