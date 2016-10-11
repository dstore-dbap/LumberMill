import ModuleBaseTestCase
import mock
import time

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.modifier import Facet
from lumbermill.misc import RedisStore


class TestFacet(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestFacet, self).setUp(Facet.Facet(ModuleBaseTestCase.MockGambolPutty()))

    def testFacet(self):
        rc = RedisStore.RedisStore(mock.Mock())
        rc.configure({'server': 'localhost'})
        self.test_object.lumbermill.modules = {'RedisStore': {'instances': [rc]}}
        self.test_object.configure({'source_field': 'url',
                                    'group_by': '$(remote_ip)',
                                    'add_event_fields': ['remote_ip','user_agent'],
                                    'interval': .1,
                                    'backend': 'RedisStore',
                                    'backend_ttl': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.johann.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Graham'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.lumbermill.com',
                                                              'remote_ip': '127.0.0.2',
                                                              'user_agent': 'John'}))
        events = []
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] != 'facet':
                continue
            events.append(event)
        self.assertEquals(len(events), 2)
        self.assertEquals(events[0]['facets'], ['http://www.lumbermill.com'])
        self.assertEquals(events[0]['other_event_fields']['http://www.lumbermill.com'], {'user_agent': 'John', 'remote_ip': '127.0.0.2'})
        self.assertEquals(events[1]['facets'], ['http://www.google.com', 'http://www.johann.com'])

    def testFacetValuesMustBeUnique(self):
        rc = RedisStore.RedisStore(mock.Mock())
        rc.configure({'server': 'localhost'})
        self.test_object.lumbermill.modules = {'RedisStore': {'instances': [rc]}}
        self.test_object.configure({'source_field': 'url',
                                    'group_by': '$(remote_ip)',
                                    'interval': 4,
                                    'backend': 'RedisStore',
                                    'backend_ttl': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))

        time.sleep(1)
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))
        time.sleep(1)
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                              'remote_ip': '127.0.0.1',
                                                              'user_agent': 'Eric'}))
        time.sleep(1)
        self.test_object.shutDown();
        events = []
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] != 'facet':
                continue
            events.append(event)
        self.assertEquals(len(events), 1)
        self.assertEquals(len(events[0]['facets']), 1)
        self.assertEquals(events[0]['facets'][0], 'http://www.google.com')

    def tearDown(self):
        pass