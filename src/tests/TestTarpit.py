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
        self.test_object.configure({'delay': 2})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        before = time.time()
        for result in self.test_object.handleData(Utils.getDefaultDataDict({})):
            after = time.time()
            self.assertEquals(2, int(after-before))

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()