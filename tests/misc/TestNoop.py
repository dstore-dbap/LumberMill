import mock
import time
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.misc import Noop

class TestNoop(ModuleBaseTestCase):

    def setUp(self):
        super(TestNoop, self).setUp(Noop.Noop(mock.Mock()))

    def testNoop(self):
        self.test_object.configure()
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({})
        event_received = None
        for event_received in self.test_object.handleEvent(event):
            self.assertEqual(event, event_received)
        self.assertIsNotNone(event_received)
