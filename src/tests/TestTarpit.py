import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import time
import Tarpit

class TestTarpit(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestTarpit, self).setUp(Tarpit.Tarpit(gp=mock.Mock()))

    def testTarpit(self):
        self.test_object.configure({'delay': 1})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        before = time.time()
        self.test_object.handleEvent(Utils.getDefaultEventDict({}))
        for event in self.receiver.getEvent():
            after = time.time()
            self.assertEquals(1, int(after-before))

if __name__ == '__main__':
    unittest.main()