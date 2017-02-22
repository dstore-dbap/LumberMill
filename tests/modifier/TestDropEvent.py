import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.modifier import DropEvent


class TestDropEvent(ModuleBaseTestCase):

    def setUp(self):
        super(TestDropEvent, self).setUp(DropEvent.DropEvent(MockLumberMill()))

    def test(self):
        self.test_object.configure({})
        self.checkConfiguration()
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'/dev/null': '"Spam! Spam! Spam! Lovely Spam! Spam! Spam!"'}))
        got_event = False
        for event in self.receiver.getEvent():
            got_event = True
        self.assertFalse(got_event)
