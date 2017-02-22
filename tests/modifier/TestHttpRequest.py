import mock
import time

import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.modifier import HttpRequest
from lumbermill.misc import RedisStore


class TestHttpRequest(ModuleBaseTestCase):

    def setUp(self):
        super(TestHttpRequest, self).setUp(HttpRequest.HttpRequest(MockLumberMill()))

    def testQuery(self):
        self.test_object.configure({'url': 'http://www.google.com'})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'TreeNodeID': '1'})):
            self.assertTrue('http_request_result' in event and len(event['http_request_result']) > 0)

    def testQueryTargetField(self):
        self.test_object.configure({'url': 'http://www.google.com',
                                    'target_field': 'Johann Gambolputty'})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'TreeNodeID': '1'})):
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testDynamicQueryTargetField(self):
        self.test_object.configure({'url': '$(schema)://$(host)',
                                    'target_field': 'Johann Gambolputty'})
        self.checkConfiguration()
        data_dict = DictUtils.getDefaultEventDict({'schema': 'http',
                                              'host': 'www.google.com'})
        for event in self.test_object.handleEvent(data_dict):
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testHttpsQuery(self):
        self.test_object.configure({'url': 'https://www.python.org/'})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'TreeNodeID': '1'})):
            self.assertTrue('http_request_result' in event and len(event['http_request_result']) > 0)

    def testHttpsQueryDynamicTargetField(self):
        self.test_object.configure({'url': 'http://www.google.com',
                                    'target_field': '$(surname) Gambolputty'})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'TreeNodeID': '1', 'surname': 'Johann'})):
            self.assertTrue('Johann Gambolputty' in event and len(event['Johann Gambolputty']) > 0)

    def testRedis(self):
        rc = RedisStore.RedisStore(mock.Mock())
        rc.configure({'server': 'localhost'})
        self.test_object.lumbermill.modules = {'RedisStore': {'instances': [rc]}}
        self.test_object.configure({'url': 'http://www.google.com',
                                    'target_field': '$(surname) Gambolputty',
                                    'redis_store': 'RedisStore',
                                    'redis_key': '$(surname)',
                                    'redis_ttl': 5})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({'TreeNodeID': '1', 'surname': 'Johann'})):
            redis_entry = rc.get('Johann')
            self.assertEquals(event['Johann Gambolputty'], redis_entry)

    def testInterval(self):
        self.test_object.configure({'url': 'http://www.google.com',
                                    'interval': 1})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        time.sleep(3.2)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertTrue(len(events) == 3)
        self.assertNotEquals(events[0]['http_request_result'], '')

    def testGetMetaData(self):
        self.test_object.configure({'url': 'http://www.google.com',
                                    'get_metadata': True})
        self.checkConfiguration()
        event = None
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({})):
            self.assertTrue('http_request_result' in event and len(event['http_request_result']) > 0)
        self.assertIsNotNone(event)
        self.assertTrue(len(event['http_request_result']['headers']) > 0)