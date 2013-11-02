import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import Facet

class TestFacet(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestFacet, self).setUp(Facet.Facet(gp=mock.Mock()))

    def testFacet(self):
        self.test_object.configure({'source_field': 'url',
                                    'group_by': '%(remote_ip)s',
                                    'keep_fields': ['remote_ip','user_agent'],
                                    'interval': .1})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.handleData(Utils.getDefaultDataDict({'url': 'http://www.google.com',
                                                                     'remote_ip': '127.0.0.1',
                                                                     'user_agent': 'Eric'}))
        self.test_object.handleData(Utils.getDefaultDataDict({'url': 'http://www.gambolputty.com',
                                                                     'remote_ip': '127.0.0.2',
                                                                       'user_agent': 'John'}))
        self.test_object.handleData(Utils.getDefaultDataDict({'url': 'http://www.johann.com',
                                                                     'remote_ip': '127.0.0.1',
                                                                     'user_agent': 'Graham'}))
        self.test_object.start()
        events = []
        while True:
            try:
                events.append(self.output_queue.get(timeout=1))
            except:
                break
        self.assertEquals(len(events), 2)
        self.assertEquals(events[0]['facets'], ['http://www.gambolputty.com'])

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()