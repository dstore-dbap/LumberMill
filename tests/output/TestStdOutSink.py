import sys
import time
import lumbermill.utils.DictUtils as DictUtils

from cStringIO import StringIO
from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.output import StdOutSink


class TestStdOutSink(ModuleBaseTestCase):

    def setUp(self):
        super(TestStdOutSink, self).setUp(StdOutSink.StdOutSink(MockLumberMill()))

    def test(self):
        self.test_object.configure({})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'data': 'One thing is for sure; a sheep is not a creature of the air.'})
        try:
            sys.stdout = stdout_captured = StringIO()
            self.test_object.receiveEvent(event)
            time.sleep(.5)
        finally:
            sys.stdout = sys.__stdout__
        self.assertTrue(stdout_captured.getvalue().startswith("{   'data': 'One thing is for sure; a sheep is not a creature of the air.',"))

    def testFormat(self):
        self.test_object.configure({'format': '$(data) - $(lumbermill.event_type)'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'data': 'One thing is for sure; a sheep is not a creature of the air.'})
        try:
            sys.stdout = stdout_captured = StringIO()
            self.test_object.receiveEvent(event)
            time.sleep(.5)
        finally:
            sys.stdout = sys.__stdout__
        self.assertEquals(stdout_captured.getvalue(), 'One thing is for sure; a sheep is not a creature of the air. - Unknown\n')