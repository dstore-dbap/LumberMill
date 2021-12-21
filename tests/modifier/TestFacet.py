import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.modifier import Facet
from lumbermill.misc import Cache


class TestFacet(ModuleBaseTestCase):

    def setUp(self):
        super(TestFacet, self).setUp(Facet.Facet(MockLumberMill()))

    def testFacet(self):
        cache = Cache.Cache(mock.Mock())
        cache.configure({})
        self.test_object.lumbermill.addModule('Cache', cache)
        self.test_object.configure({'source_field': 'url',
                                    'group_by': '$(remote_ip)',
                                    'add_event_fields': ['remote_ip', 'user_agent'],
                                    'interval': 1,
                                    'cache': 'Cache',
                                    'cache_key': 'testFacet',
                                    'cache_ttl': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                                     'remote_ip': '127.0.0.1',
                                                                     'user_agent': 'Eric'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.google.com',
                                                                     'remote_ip': '127.0.0.1',
                                                                     'user_agent': 'Eric'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.blackknight.com',
                                                                     'remote_ip': '127.0.0.1',
                                                                     'user_agent': 'Idle'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.blank.com',
                                                                     'remote_ip': '127.0.0.1',
                                                                     'user_agent': 'Idle'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.johann.com',
                                                                     'remote_ip': '127.0.0.2',
                                                                     'user_agent': 'Graham'}))
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'url': 'http://www.lumbermill.com',
                                                                     'remote_ip': '127.0.0.2',
                                                                     'user_agent': 'John'}))
        self.test_object.shutDown()
        events = []
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] != 'facet':
                continue
            events.append(event)
        events = sorted(events, key=lambda k: k['facet_count'])
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['facets'], ['http://www.johann.com', 'http://www.lumbermill.com'])
        self.assertEqual(events[0]['other_event_fields'][0], {'facet': 'http://www.johann.com', 'user_agent': 'Graham', 'remote_ip': '127.0.0.2'})
        self.assertEqual(events[1]['facets'], ['http://www.google.com', 'http://www.blackknight.com', 'http://www.blank.com'])
        self.assertEqual(events[1]['other_event_fields'][0], {'facet': 'http://www.google.com', 'user_agent': 'Eric', 'remote_ip': '127.0.0.1'})