import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import time
import Tarpit

class TestTarpit(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestTarpit, self).setUp(Tarpit.Tarpit(gp=mock.Mock()))

    def testTarpit(self):
        self.test_object.configure({'delay': 1})
        self.checkConfiguration()
        before = time.time()
        self.test_object.handleEvent(Utils.getDefaultEventDict({}))
        for event in self.receiver.getEvent():
            after = time.time()
            self.assertEquals(1, int(after-before))
