import pprint
import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import time
import Utils
import RedisClient
import Facet

class TestFacet(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestFacet, self).setUp(Facet.Facet(gp=mock.Mock()))

    def testInternalFacet(self):
        self.test_object.configure({'source_field': 'url',
                                    'group_by': '%(remote_ip)s',
                                    'add_event_fields': ['remote_ip','user_agent'],
                                    'interval': .1})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.receiveEvent(Utils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))
        self.test_object.receiveEvent(Utils.getDefaultEventDict({'url': 'http://www.gambolputty.com',
                                                              'remote_ip': '127.0.0.2',
                                                              'user_agent': 'John'}))
        self.test_object.receiveEvent(Utils.getDefaultEventDict({'url': 'http://www.johann.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Graham'}))
        events = []
        time.sleep(.2)
        for event in self.receiver.getEvent():
            if event['event_type'] != 'facet':
                continue
            events.append(event)
        self.assertEquals(len(events), 2)
        self.assertEquals(events[0]['facets'], ['http://www.gambolputty.com'])

    def testRedisFacet(self):
        rc = RedisClient.RedisClient(gp=mock.Mock())
        rc.configure({'server': 'es-01.dbap.de'})
        self.test_object.gp.modules = {'RedisClient': {'instances': [rc]}}
        self.test_object.configure({'source_field': 'url',
                                    'group_by': '%(remote_ip)s',
                                    'add_event_fields': ['remote_ip','user_agent'],
                                    'interval': .1,
                                    'redis_client': 'RedisClient',
                                    'redis_ttl': 5})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.initRedisClient()
        self.test_object.receiveEvent(Utils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))
        self.test_object.receiveEvent(Utils.getDefaultEventDict({'url': 'http://www.johann.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Graham'}))
        self.test_object.receiveEvent(Utils.getDefaultEventDict({'url': 'http://www.gambolputty.com',
                                                              'remote_ip': '127.0.0.2',
                                                              'user_agent': 'John'}))
        events = []
        time.sleep(.2)
        for event in self.receiver.getEvent():
            if event['event_type'] != 'facet':
                continue
            events.append(event)
        self.assertEquals(len(events), 2)
        self.assertEquals(events[1]['facets'], ['http://www.gambolputty.com'])

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()