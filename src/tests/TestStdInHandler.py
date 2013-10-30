import extendSysPath
import unittest
import mock
import Queue
import StringIO
import Utils
import ConfigurationValidator
import BaseThreadedModule
import StdInHandler

class TestStdInHandler(unittest.TestCase):

    def setUp(self):
        self.conf_validator = ConfigurationValidator.ConfigurationValidator()
        self.test_object = StdInHandler.StdInHandler(gp=mock.Mock())
        self.default_dict = Utils.getDefaultDataDict({})
        self.queue = Queue.Queue()
        
    def testStdInHandlerSingleLine(self):
        self.test_object.configure({})
        input = StringIO.StringIO("We are the knights who say ni!")
        self.test_object.addOutputQueue(self.queue)
        self.test_object.run(input)
        while True:
            try:
                item = self.queue.get(block=False)
            except Queue.Empty:
                break
        self.assertEquals(item['data'], "We are the knights who say ni!")

    def testStdInHandlerMultiLine(self):
        self.test_object.configure({'multiline': True})
        input = StringIO.StringIO("""We are the knights who say ni!
Bring us a shrubbery!""")
        self.test_object.addOutputQueue(self.queue)
        self.test_object.run(input)
        while True:
            try:
                item = self.queue.get(block=False)
            except Queue.Empty:
                break
        self.assertEquals(item['data'], """We are the knights who say ni!
Bring us a shrubbery!""")        

    def testStdInHandlerStreamBoundry(self):
        self.test_object.configure({'multiline': True,
                                    'stream-end-signal': "Ekki-Ekki-Ekki-Ekki-PTANG\n"})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        input = StringIO.StringIO("""We are the knights who say ni!
Bring us a shrubbery!
Ekki-Ekki-Ekki-Ekki-PTANG
We are now no longer the Knights who say Ni.""")
        self.test_object.addOutputQueue(self.queue)
        self.test_object.run(input)
        item = []
        while True:
            try:
                item.append(self.queue.get(block=False))
            except Queue.Empty:
                break
        self.assertEquals(len(item), 2)
        self.assertEquals(item[0]['data'], """We are the knights who say ni!
Bring us a shrubbery!\n""")
        self.assertEquals(item[1]['data'], "We are now no longer the Knights who say Ni.")        

if __name__ == '__main__':
    unittest.main()