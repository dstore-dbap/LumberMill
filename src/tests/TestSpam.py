import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import Queue
import Spam
import unittest2

class TestSpam(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestSpam, self).setUp(Spam.Spam(gp=mock.Mock()))

    def testSpam(self):
        self.test_object.configure({'event': {'Lobster': 'Thermidor', 'Truffle': 'Pate'} })
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.start()
        count = 0
        queue_emtpy = False
        while count < 100:
            try:
                event = self.output_queue.get(timeout=.2)
            except Queue.Empty:
                queue_emtpy = True
                break
            except:
                break
            finally:
                count += 1
        self.assertEquals(queue_emtpy, False)
        self.assertEquals(count, 100)

    @unittest2.skip("Skipping testQueueCommunication.")
    def testQueueCommunication(self):
        super(TestSpam, self).testQueueCommunication(self.default_config)

    @unittest2.skip("Skipping testOutputQueueFilterMatch.")
    def testOutputQueueFilterMatch(self):
        super(TestSpam, self).testOutputQueueFilterMatch(self.default_config)

    @unittest2.skip("Skipping testOutputQueueFilterNoMatch.")
    def testOutputQueueFilterNoMatch(self):
        super(TestSpam, self).testOutputQueueFilterNoMatch(self.default_config)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()