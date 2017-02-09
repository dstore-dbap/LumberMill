import sys
import time
import ModuleBaseTestCase
import lumbermill.utils.DictUtils as DictUtils

from cStringIO import StringIO
from lumbermill.output import StdOutSink


class TestStdOutSink(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestStdOutSink, self).setUp(StdOutSink.StdOutSink(ModuleBaseTestCase.MockGambolPutty()))

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