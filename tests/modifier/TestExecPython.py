import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.modifier import ExecPython


class TestExecPython(ModuleBaseTestCase):

    def setUp(self):
        super(TestExecPython, self).setUp(ExecPython.ExecPython(MockLumberMill()))

    def test(self):
        self.test_object.configure({'source': ' event["data"] = "Incontinenzia"'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'data': 'One thing is for sure; a sheep is not a creature of the air.'})
        self.test_object.receiveEvent(event)
        data = None
        for event in self.receiver.getEvent():
            data = event['data']
        self.assertEqual(data, 'Incontinenzia')