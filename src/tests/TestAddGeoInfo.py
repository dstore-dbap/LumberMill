import extendSysPath
import unittest
import mock
import AddGeoInfo
import Utils

class TestAddGeoInfo(unittest.TestCase):
    def setUp(self):
        self.test_object = AddGeoInfo.AddGeoInfo()
        self.test_object.lj = mock.Mock()
    
    def testAddGeoInfoForFirstField(self):
        self.test_object.configure({'lookup_fields': ['f1'],
                                    'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultDataDict({'f1': '99.124.167.129'})
        result = self.test_object.handleData(dict)
        self.assertEqual(result['country_code'], 'US')
        
    def testAddGeoInfo(self):
        self.test_object.configure({'lookup_fields': ['f1','f2'],
                                    'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultDataDict({'f2': '99.124.167.129'})
        result = self.test_object.handleData(dict)
        self.assertEqual(result['country_code'], 'US')
        
if __name__ == '__main__':
    unittest.main()