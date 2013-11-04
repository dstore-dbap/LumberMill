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
        for result in self.test_object.handleData(Utils.getDefaultDataDict({})):
            self.assert_(re.match('^\d+-\d+-\d+T\d+:\d+:\d+$', result['@timestamp'])) # 2013-08-29T10:25:26

    def testQueueCommunication(self):
        super(TestModuleContainer, self).testQueueCommunication(self.default_config)

    def testOutputQueueFilterNoMatch(self):
        super(TestModuleContainer, self).testOutputQueueFilterNoMatch(self.default_config)

    def testOutputQueueFilterMatch(self):
        super(TestModuleContainer, self).testOutputQueueFilterMatch(self.default_config)

    @unittest2.skip("Skipping testWorksOnCopy because this is tested via the module tests.")
    def testWorksOnCopy(self):
        super(TestModuleContainer, self).testWorksOnCopy(self.default_config)

    @unittest2.skip("Skipping testWorksOnCopy because this is tested via the module tests.")
    def testWorksOnOriginal(self):
        super(TestModuleContainer, self).testWorksOnOriginal(self.default_config)

if __name__ == '__main__':
    unittest.main()