import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Queue
import AddGeoInfo
import Utils

class TestAddGeoInfo(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddGeoInfo, self).setUp(AddGeoInfo.AddGeoInfo(gp=mock.Mock()))

    def testAddGeoInfoForFirstField(self):
        self.test_object.configure({'source_fields': ['f1'],
                                    'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultDataDict({'f1': '99.124.167.129'})
        for result in self.test_object.handleData(dict):
            self.assertEqual(result['country_code'], 'US')
        
    def testAddGeoInfo(self):
        self.test_object.configure({'source_fields': ['f1','f2'],
                                    'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultDataDict({'f2': '99.124.167.129'})
        for result in self.test_object.handleData(dict):
            self.assertEqual(result['country_code'], 'US')

    def testAddGeoInfoFromDefaultField(self):
        self.test_object.configure({'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultDataDict({'x_forwarded_for': '99.124.167.129'})
        for result in self.test_object.handleData(dict):
            self.assertEqual(result['country_code'], 'US')

    def testQueueCommunication(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testQueueCommunication(config)

    def testOutputQueueFilterMatch(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testOutputQueueFilterMatch(config)

    def testOutputQueueFilterNoMatch(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testOutputQueueFilterMatch(config)

    def testWorksOnCopy(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testWorksOnCopy(config)

    def testWorksOnOriginal(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testWorksOnOriginal(config)

if __name__ == '__main__':
    unittest.main()