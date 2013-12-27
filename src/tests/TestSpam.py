import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import time
import Spam

class TestSpam(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestSpam, self).setUp(Spam.Spam(gp=mock.Mock()))

    def testSpam(self):
        self.test_object.configure({'event': {'Lobster': 'Thermidor', 'Truffle': 'Pate'} })
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.start()
        count = 0
        started = time.time()
        for event in self.receiver.getEvent():
            if count == 100 or time.time() - started > 2:
                break
            count += 1
        self.assertEquals(count, 100)

if __name__ == '__main__':
    unittest.main()