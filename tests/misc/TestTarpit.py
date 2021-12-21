import mock
import time
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.misc import Tarpit

class TestTarpit(ModuleBaseTestCase):

    def setUp(self):
        super(TestTarpit, self).setUp(Tarpit.Tarpit(mock.Mock()))

    def testTarpit(self):
        self.test_object.configure({'delay': 1})
        self.checkConfiguration()
        before = time.time()
        event = None
        for event in self.test_object.handleEvent(DictUtils.getDefaultEventDict({})):
            after = time.time()
            self.assertEqual(1, int(after - before))
        self.assertIsNotNone(event)
