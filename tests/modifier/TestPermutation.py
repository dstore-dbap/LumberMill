import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.modifier import Permutate


class TestPermutate(ModuleBaseTestCase):

    def setUp(self):
        super(TestPermutate, self).setUp(Permutate.Permutate(mock.Mock()))

    def testPermutate(self):
        self.test_object.configure({'source_field': 'facets',
                                    'target_fields': ['field1', 'field2'],
                                    'context_data_field': 'context',
                                    'context_target_mapping': {'ctx2': ['ctx2_field1', 'ctx2_field2'], 'ctx': ['ctx_field1', 'ctx_field2']}})
        self.checkConfiguration()
        events = []
        source_event = DictUtils.getDefaultEventDict({'facets': [1,2],
                                                  'context': { 1: {'ctx': 'a', 'ctx2': 'aa'},
                                                               2: {'ctx': 'b', 'ctx2': 'bb'}}})
        for result in self.test_object.handleEvent(source_event):
            events.append(result)
        self.assertEqual(len(events), 2)

    def tearDown(self):
        pass
