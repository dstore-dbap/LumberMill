import os

import extendSysPath
import ModuleBaseTestCase
import mock
import unittest
import AddGeoInfo
import Utils

class TestAddGeoInfo(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddGeoInfo, self).setUp(AddGeoInfo.AddGeoInfo(gp=mock.Mock()))
        self.path_to_geo_db = './test_data/GeoLiteCity.dat'
        if not os.path.isfile(self.path_to_geo_db):
            raise unittest.SkipTest('Could not find GeoCity db file in %s. Skipping test.' % self.path_to_geo_db)

    def testAddGeoInfoForFirstField(self):
        self.test_object.configure({'source_fields': ['f1'],
                                    'geoip_dat_path': './test_data/GeoLiteCity.dat',
                                    'target_field': 'geoip',
                                    'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        dict = Utils.getDefaultEventDict({'f1': '99.124.167.129'})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['geoip']['country_code'], 'US')
        
    def testAddGeoInfo(self):
        self.test_object.configure({'source_fields': ['f1','f2'],
                                    'geoip_dat_path': './test_data/GeoLiteCity.dat',
                                    'target_field': 'geoip',
                                    'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        dict = Utils.getDefaultEventDict({'f2': '99.124.167.129'})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['geoip']['country_code'], 'US')

    def testAddGeoInfoFromDefaultField(self):
        self.test_object.configure({'geoip_dat_path': './test_data/GeoLiteCity.dat',
                                    'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        dict = Utils.getDefaultEventDict({'x_forwarded_for': '99.124.167.129'})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['country_code'], 'US')

if __name__ == '__main__':
    unittest.main()