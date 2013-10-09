import extendSysPath
import unittest
import mock
import Queue
import AddGeoInfo
import Utils

class TestAddGeoInfo(unittest.TestCase):
    def setUp(self):
        self.input_queue = Queue.Queue()
        self.output_queue = Queue.Queue()
        self.test_object = AddGeoInfo.AddGeoInfo()
        self.test_object.lj = mock.Mock()
        self.test_object.setInputQueue(self.input_queue)
        self.test_object.addOutputQueue(self.output_queue, filter_by_marker=False, filter_by_field=False)
    
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

    def testQueueCommunication(self):
        self.test_object.configure({'lookup_fields': ['f1'],
                                    'geoip_dat_path': '../exampleData/GeoIP.dat'})
        dict = Utils.getDefaultDataDict({'f1': '99.124.167.129'})
        self.test_object.start()
        self.input_queue.put(Utils.getDefaultDataDict({}))
        queue_emtpy = False
        try:
            self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True)

if __name__ == '__main__':
    unittest.main()