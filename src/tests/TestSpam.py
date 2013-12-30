import extendSysPath
import ModuleBaseTestCase
import time
import Spam

class TestSpam(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        test_object = Spam.Spam(gp=ModuleBaseTestCase.MockGambolPutty())
        test_object.gp.addModule(test_object)
        super(TestSpam, self).setUp(test_object)

    def testSpam(self):
        self.test_object.configure({'event': {'Lobster': 'Thermidor', 'Truffle': 'Pate'},
                                    'events_count': 985})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        self.test_object.start()
        count = 0
        time.sleep(1)
        for event in self.receiver.getEvent():
            count += 1
        self.assertEquals(count, 985)
