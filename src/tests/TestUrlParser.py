import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import UrlParser

class TestUrlParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestUrlParser, self).setUp(UrlParser.UrlParser(gp=mock.Mock()))

    def testHandleData(self):
        self.test_object.configure({'source_field': 'uri'})
        data = Utils.getDefaultDataDict({'uri': 'http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty'})
        for result in self.test_object.handleData(data):
            self.assert_('gambol' in result and result['gambol'] == 'putty')

    def testQueueCommunication(self):
        config = {'source_field': 'data'}
        super(TestUrlParser, self).testQueueCommunication(config)

    def testOutputQueueFilterNoMatch(self):
        config = {'source_field': 'dev_null'}
        super(TestUrlParser, self).testOutputQueueFilterNoMatch(config)

    def testOutputQueueFilterMatch(self):
        config = {'source_field': 'dev_null'}
        super(TestUrlParser, self).testOutputQueueFilterMatch(config)

    def testWorksOnCopy(self):
        config = {'source_field': 'data'}
        super(TestUrlParser, self).testWorksOnCopy(config)

    def testWorksOnOriginal(self):
        config = {'source_field': 'data'}
        super(TestUrlParser, self).testWorksOnOriginal(config)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()