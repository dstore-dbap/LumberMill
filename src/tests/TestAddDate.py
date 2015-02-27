import extendSysPath
import ModuleBaseTestCase
import mock
import re
import Utils
import AddDateTime


class TestAddDateTime(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddDateTime, self).setUp(AddDateTime.AddDateTime(gp=mock.Mock()))

    def testIsTimeStamp(self):
        self.test_object.configure({})
        self.checkConfiguration()
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({})):
            self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', event['@timestamp'])) # 2013-08-29T10:25:26

    def testAddDateTimeCustomFormat(self):
        self.test_object.configure({'format': '%Y/%M/%d %H.%M.%S'})
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({})):
            self.assert_(re.match('^\d+/\d+/\d+ \d+.\d+.\d+$', event['@timestamp'])) # 2013/08/29 10.25.26

    def testAddDateTimeDefaultField(self):
        self.test_object.configure({})
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({})):
            self.assert_('@timestamp' in event)

    def testAddDateTimeCustomField(self):
        self.test_object.configure({'target_field': 'test'})
        for event in self.test_object.handleEvent(Utils.getDefaultEventDict({})):
            self.assert_('test' in event)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()