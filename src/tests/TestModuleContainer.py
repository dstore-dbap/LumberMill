import extendSysPath
import unittest2
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
        super(TestModuleContainer, self).testQueueCommunication(self.default_config)

    def testOutputQueueFilter(self):
        super(TestModuleContainer, self).testOutputQueueFilter(self.default_config)

    def testInvertedOutputQueueFilter(self):
        super(TestModuleContainer, self).testInvertedOutputQueueFilter(self.default_config)

    @unittest2.skip("Skipping testWorksOnCopy because this is tested via the module tests.")
    def testWorksOnCopy(self):
        super(TestModuleContainer, self).testWorksOnCopy(self.default_config)

    @unittest2.skip("Skipping testWorksOnCopy because this is tested via the module tests.")
    def testWorksOnOriginal(self):
        super(TestModuleContainer, self).testWorksOnOriginal(self.default_config)

if __name__ == '__main__':
    unittest.main()