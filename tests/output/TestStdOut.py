import time
import lumbermill.utils.DictUtils as DictUtils

from io import StringIO
from contextlib import redirect_stdout
from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.output import StdOut


class TestStdOut(ModuleBaseTestCase):

    def setUp(self):
        super(TestStdOut, self).setUp(StdOut.StdOut(MockLumberMill()))

    def test(self):
        self.test_object.configure({})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'data': 'One thing is for sure; a sheep is not a creature of the air.'})
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.test_object.receiveEvent(event)
            time.sleep(.5)
        self.assertTrue(stdout.getvalue().startswith("{   'data': 'One thing is for sure; a sheep is not a creature of the air.',"))

    def testFormat(self):
        self.test_object.configure({'format': '$(data) - $(lumbermill.event_type)'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'data': 'One thing is for sure; a sheep is not a creature of the air.'})
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.test_object.receiveEvent(event)
            time.sleep(.5)
        self.assertEqual(stdout.getvalue(), 'One thing is for sure; a sheep is not a creature of the air. - Unknown\n')