import os
import ModuleBaseTestCase
import mock
import unittest

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.modifier import AddGeoInfo
from lumbermill.constants import LUMBERMILL_BASEPATH


class TestAddGeoInfo(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddGeoInfo, self).setUp(AddGeoInfo.AddGeoInfo(mock.Mock()))
        self.path_to_geo_db = LUMBERMILL_BASEPATH + '/assets/maxmind/GeoLite2-City.mmdb'
        if not os.path.isfile(self.path_to_geo_db):
            raise unittest.SkipTest('Could not find GeoCity db file in %s. Skipping test.' % self.path_to_geo_db)

    def testAddGeoInfoForFirstField(self):
        self.test_object.configure({'source_fields': ['f1'],
                                    'target_field': 'geoip',
                                    'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        dict = DictUtils.getDefaultEventDict({'f1': '99.124.167.129'})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['geoip']['country_code'], 'US')
        
    def testAddGeoInfo(self):
        self.test_object.configure({'source_fields': ['f1', 'f2'],
                                    'target_field': 'geoip',
                                    'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        dict = DictUtils.getDefaultEventDict({'f2': '99.124.167.129'})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['geoip']['country_code'], 'US')

    def testAddGeoInfoFromDefaultField(self):
        self.test_object.configure({'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        dict = DictUtils.getDefaultEventDict({'x_forwarded_for': '99.124.167.129'})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['geo_info']['country_code'], 'US')

    def testAddGeoInfoFromListField(self):
        self.test_object.configure({'geo_info_fields': ['country_code'],
                                    'source_fields': ['x_forwarded_for']})
        self.checkConfiguration()
        dict = DictUtils.getDefaultEventDict({'x_forwarded_for': ['99.124.167.129']})
        for event in self.test_object.handleEvent(dict):
            self.assertEqual(event['geo_info']['country_code'], 'US')

    def testIsValidIpV4Address(self):
        self.test_object.configure({'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        self.assertTrue(self.test_object.is_valid_ipv4_address('127.0.0.1'))

    def testIsInvalidIpV4Address(self):
        self.test_object.configure({'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        self.assertFalse(self.test_object.is_valid_ipv4_address('1234567890'))

    def testIsValidIpV6Address(self):
        self.test_object.configure({'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        self.assertTrue(self.test_object.is_valid_ipv6_address('::1'))

    def testIsInvalidIpV6Address(self):
        self.test_object.configure({'geo_info_fields': ['country_code']})
        self.checkConfiguration()
        self.assertFalse(self.test_object.is_valid_ipv6_address('1234567890'))

if __name__ == '__main__':
    unittest.main()