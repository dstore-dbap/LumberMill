import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import Permutate

class TestPermutate(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestPermutate, self).setUp(Permutate.Permutate(gp=mock.Mock()))

    def testPermutate(self):
        self.test_object.configure({'source_field': 'facets',
                                    'target_fields': ['field1', 'field2'],
                                    'length': 2,
                                    'context_data_field': 'context'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        events = []
        for result in self.test_object.handleData(Utils.getDefaultDataDict({'facets': [1,2,3,4],
                                                                            'context': [{'ctx': 'a'},{'ctx': 'b'},{'ctx': 'c'},{'ctx': 'd'}]})):
            events.append(result)
        self.assertEquals(len(events), 12)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()