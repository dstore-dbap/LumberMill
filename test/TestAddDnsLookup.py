import time
import ModuleBaseTestCase
import mock

import lumbermill.Utils as Utils
from lumbermill.modifier import AddDnsLookup


class TestAddDnsLookup(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestAddDnsLookup, self).setUp(AddDnsLookup.AddDnsLookup(mock.Mock()))

    def testDnsLookup(self):
        config = {'source_field': 'host'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'host': 'www.dbap.de'})
        self.test_object.receiveEvent(data)
        event = None
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            self.assertTrue(event['host'] == '195.137.224.39')
        self.assertIsNotNone(event)

    def testDnsLookupWithTargetField(self):
        config = {'source_field': 'host',
                  'target_field': 'host_ip_address'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'host': 'www.dbap.de'})
        self.test_object.receiveEvent(data)
        event = None
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            self.assertTrue(event['host_ip_address'] == '195.137.224.39')
        self.assertIsNotNone(event)

    def testReverseDnsLookup(self):
        config = {'action': 'reverse',
                  'source_field': 'remote_ip'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'remote_ip': '127.0.0.1'})
        self.test_object.receiveEvent(data)
        event = None
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            result = event['remote_ip'].split('.')[0]
            self.assertTrue(result == 'localhost')
        self.assertIsNotNone(event)

    def testReverseDnsLookupwithTargetField(self):
        config = {'action': 'reverse',
                  'source_field': 'remote_ip',
                  'target_field': 'remote_host'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = Utils.getDefaultEventDict({'remote_ip': '127.0.0.1'})
        self.test_object.receiveEvent(data)
        event = None
        # Wait for interval.
        time.sleep(1)
        for event in self.receiver.getEvent():
            result = event['remote_host'].split('.')[0]
            self.assertTrue(result == 'localhost')
        self.assertIsNotNone(event)

    def tearDown(self):
        pass