import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import DomainName


class TestDomainName(ModuleBaseTestCase):

    def setUp(self):
        super(TestDomainName, self).setUp(DomainName.DomainName(mock.Mock()))

    def testDomainNameWithSourceAndTargetField(self):
        config = {'source_field': 'url',
                  'target_field': 'url_tld_data'}
        self.test_object.configure(config)
        self.checkConfiguration()
        payload = 'http://the.sheep.co.uk'
        data = DictUtils.getDefaultEventDict({'url': payload})
        expected_result = {'domain': u'sheep', 'subdomain': u'the', 'suffix': u'co.uk', 'tld': u'co.uk'}
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['url_tld_data'] == expected_result)
