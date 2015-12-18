import ModuleBaseTestCase
import mock

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.parser import UserAgentParser


class TestUserAgentParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestUserAgentParser, self).setUp(UserAgentParser.UserAgentParser(mock.Mock()))

    def testUserAgentSingleSourceField(self):
        self.test_object.configure({'source_fields': 'user_agent'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'user_agent': "Mozilla/5.0 (Windows NT 6.0; rv:33.0) Gecko/20100101 Firefox/33.0"})
        for event in self.test_object.handleEvent(event):
            self.assert_('user_agent_info' in event and event['user_agent_info']['user_agent']['family'] == "Firefox")

    def testUserAgentMultipleSourceField(self):
        self.test_object.configure({'source_fields': ['user_agent_missing', 'user_agent']})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'user_agent': "Mozilla/5.0 (Windows NT 6.0; rv:33.0) Gecko/20100101 Firefox/33.0"})
        for event in self.test_object.handleEvent(event):
            self.assert_('user_agent_info' in event and event['user_agent_info']['user_agent']['major'] == "33")

    def testUserAgentTargetField(self):
        self.test_object.configure({'source_fields': 'user_agent',
                                    'target_field': 'http_user_agent_data'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'user_agent': "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
        for event in self.test_object.handleEvent(event):
            self.assert_('http_user_agent_data' in event and event['http_user_agent_data']['device']['family'] == "Spider")

    def tearDown(self):
        pass
