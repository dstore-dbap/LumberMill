import time
import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import AddDnsLookup


class TestAddDnsLookup(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddDnsLookup, self).setUp(AddDnsLookup.AddDnsLookup(gp=mock.Mock()))

    def testDnsLookup(self):
        config = {'source_fields': 'host'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'host': 'www.dbap.de'})
        self.test_object.receiveEvent(data)
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            self.assertTrue(event['host'] == '195.137.224.39')

    def testDnsLookupWithTargetField(self):
        config = {'source_fields': 'host',
                  'target_field': 'host_ip_address'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'host': 'www.dbap.de'})
        self.test_object.receiveEvent(data)
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            self.assertTrue(event['host_ip_address'] == '195.137.224.39')

    def testDnsLookupWithMultipleSourceFields(self):
        config = {'source_fields': ['host1', 'host2', 'host3']}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'host1': 'www.aksjdhakjsgdag.de',
                                          'host3': 'www.dbap.de'})
        self.test_object.receiveEvent(data)
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            self.assertTrue(event['host3'] == '195.137.224.39')

    def testDnsLookupWithMultipleSourceFieldsAndTargetField(self):
        config = {'source_fields': ['host1', 'host2', 'host3'],
                  'target_field': 'host_ip_address'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'host1': 'www.aksjdhakjsgdag.de',
                                          'host3': 'www.dbap.de'})
        self.test_object.receiveEvent(data)
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            self.assertTrue(event['host_ip_address'] == '195.137.224.39')

    def testReverseDnsLookup(self):
        config = {'action': 'reverse',
                  'source_fields': 'remote_ip'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'remote_ip': '127.0.0.1'})
        self.test_object.receiveEvent(data)
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            result = event['remote_ip'].split('.')[0]
            self.assertTrue(result == 'localhost')

    def tearDown(self):
        pass