import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import UrlParser

class TestUrlParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestUrlParser, self).setUp(UrlParser.UrlParser(gp=mock.Mock()))

    def testHandleEvent(self):
        self.test_object.configure({'source_field': 'uri'})
        data = Utils.getDefaultEventDict({'uri': 'http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty'})
        for event in self.test_object.handleEvent(data):
            self.assert_('uri' in event and event['uri']['query'] == 'gambol=putty')

if __name__ == '__main__':
    unittest.main()