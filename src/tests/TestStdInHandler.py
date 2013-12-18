import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import StringIO
import BaseThreadedModule
import StdInHandler

class TestStdInHandler(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestStdInHandler, self).setUp(StdInHandler.StdInHandler(gp=mock.Mock()))

    def testStdInHandlerSingleLine(self):
        self.test_object.configure({})
        input = StringIO.StringIO("We are the knights who say ni!")
        self.test_object.run(input)
        for event in self.receiver.getEvent():
            self.assertEquals(event['data'], "We are the knights who say ni!")

    def testStdInHandlerMultiLine(self):
        self.test_object.configure({'multiline': True})
        input = StringIO.StringIO("""We are the knights who say ni!
Bring us a shrubbery!""")
        self.test_object.run(input)
        for event in self.receiver.getEvent():
            self.assertEquals(event['data'], """We are the knights who say ni!
Bring us a shrubbery!""")        

    def testStdInHandlerStreamBoundry(self):
        self.test_object.configure({'multiline': True,
                                    'stream_end_signal': "Ekki-Ekki-Ekki-Ekki-PTANG\n"})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        input = StringIO.StringIO("""We are the knights who say ni!
Bring us a shrubbery!
Ekki-Ekki-Ekki-Ekki-PTANG
We are now no longer the Knights who say Ni.""")
        self.test_object.run(input)
        item = []
        for event in self.receiver.getEvent():
            item.append(event)
        self.assertEquals(len(item), 2)
        self.assertEquals(item[0]['data'], """We are the knights who say ni!
Bring us a shrubbery!\n""")
        self.assertEquals(item[1]['data'], "We are now no longer the Knights who say Ni.")        

if __name__ == '__main__':
    unittest.main()