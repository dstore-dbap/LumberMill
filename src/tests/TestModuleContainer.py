import extendSysPath
import unittest
import ModuleBaseTestCase
import mock
import re
import Utils
import ModuleContainer


class TestModuleContainer(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestModuleContainer, self).setUp(ModuleContainer.ModuleContainer(gp=mock.Mock()))
        self.default_config = [{'module': 'AddDateTime',
                                'configuration': {'target-field': '@timestamp'}}]

    def testHandleData(self):
        self.test_object.configure(self.default_config)
        data = self.test_object.handleData(Utils.getDefaultDataDict({}))
        self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', data['@timestamp'])) # 2013-08-29T10:25:26

    def testQueueCommunication(self):
        self.test_object.setup()
        super(TestModuleContainer, self).testQueueCommunication(self.default_config)

    def testOutputQueueFilter(self):
        self.test_object.setup()
        super(TestModuleContainer, self).testOutputQueueFilter(self.default_config)

    def testInvertedOutputQueueFilter(self):
        self.test_object.setup()
        super(TestModuleContainer, self).testInvertedOutputQueueFilter(self.default_config)

    def testWorksOnCopy(self):
        return
        self.test_object.setup()
        super(TestModuleContainer, self).testWorksOnCopy(self.default_config)

    def testWorksOnOriginal(self):
        return
        super(TestModuleContainer, self).testWorksOnOriginal(self.default_config)

if __name__ == '__main__':
    unittest.main()