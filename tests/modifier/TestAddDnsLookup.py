import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.modifier import AddDnsLookup


class TestAddDnsLookup(ModuleBaseTestCase):

    def setUp(self):
        super(TestAddDnsLookup, self).setUp(AddDnsLookup.AddDnsLookup(mock.Mock()))

    def testDnsLookup(self):
        config = {'nameservers': '8.8.8.8', 'source_field': 'host'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = DictUtils.getDefaultEventDict({'host': 'www.poitin.de'})
        self.test_object.receiveEvent(data)
        self.test_object.shutDown()
        event = None
        for event in self.receiver.getEvent():
            self.assertTrue(event['host'] == '195.128.101.111')
        self.assertIsNotNone(event)

    def testDnsLookupWithTargetField(self):
        config = {'nameservers': '8.8.8.8',
                  'source_field': 'host',
                  'target_field': 'host_ip_address'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = DictUtils.getDefaultEventDict({'host': 'www.poitin.de'})
        self.test_object.receiveEvent(data)
        self.test_object.shutDown()
        event = None
        for event in self.receiver.getEvent():
            self.assertTrue(event['host_ip_address'] == '195.128.101.111')
        self.assertIsNotNone(event)

    def testReverseDnsLookup(self):
        config = {'action': 'reverse',
                  'source_field': 'remote_ip'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = DictUtils.getDefaultEventDict({'remote_ip': '1.1.1.1'})
        self.test_object.receiveEvent(data)
        self.test_object.shutDown()
        event = None
        for event in self.receiver.getEvent():
            self.assertTrue(event['remote_ip'] == 'one.one.one.one.')
        self.assertIsNotNone(event)

    def testReverseDnsLookupwithTargetField(self):
        config = {'action': 'reverse',
                  'source_field': 'remote_ip',
                  'target_field': 'remote_host'}
        self.test_object.configure(config)
        self.checkConfiguration()
        self.test_object.initAfterFork()
        data = DictUtils.getDefaultEventDict({'remote_ip': '1.1.1.1'})
        self.test_object.receiveEvent(data)
        self.test_object.shutDown()
        event = None
        for event in self.receiver.getEvent():
            self.assertTrue(event['remote_host'] == 'one.one.one.one.')
        self.assertIsNotNone(event)
