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
        dict = Utils.getDefaultEventDict({'f1': '99.124.167.129'})
        self.test_object.handleEvent(dict)
        for event in self.receiver.getEvent():
            self.assertEqual(event['country_code'], 'US')
        
    def testAddGeoInfo(self):
        self.test_object.configure({'source_fields': ['f1','f2'],
                                    'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultEventDict({'f2': '99.124.167.129'})
        self.test_object.handleEvent(dict)
        for event in self.receiver.getEvent():
            self.assertEqual(event['country_code'], 'US')

    def testAddGeoInfoFromDefaultField(self):
        self.test_object.configure({'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultEventDict({'x_forwarded_for': '99.124.167.129'})
        self.test_object.handleEvent(dict)
        for event in self.receiver.getEvent():
            self.assertEqual(event['country_code'], 'US')

    def __testQueueCommunication(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testQueueCommunication(config)

    def __testOutputQueueFilterMatch(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testOutputQueueFilterMatch(config)


    def __testOutputQueueFilterNoMatch(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testOutputQueueFilterMatch(config)

    def __testWorksOnOriginal(self):
        config = {'source_fields': ['f1'],
                  'geoip_dat_path': '../exampleData/GeoIP.dat'}
        super(TestAddGeoInfo, self).testWorksOnOriginal(config)

if __name__ == '__main__':
    unittest.main()