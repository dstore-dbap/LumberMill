import extendSysPath
import ModuleBaseTestCase
import unittest
import mock
import Utils
import UserAgentParser

class TestUserAgentParser(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestUserAgentParser, self).setUp(UserAgentParser.UserAgentParser(gp=mock.Mock()))

    def testUserAgentSingleSourceField(self):
        self.test_object.configure({'source_fields': 'user_agent'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        event = Utils.getDefaultEventDict({'user_agent': "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.307.11 Safari/532.9"})
        for event in self.test_object.handleEvent(event):
            self.assert_('user_agent_info' in event and event['user_agent_info']['browser']['version'] == "5.0.307.11")

    def testUserAgentMultipleSourceField(self):
        self.test_object.configure({'source_fields': ['user_agent_missing', 'user_agent']})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        event = Utils.getDefaultEventDict({'user_agent': "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.307.11 Safari/532.9"})
        for event in self.test_object.handleEvent(event):
            self.assert_('user_agent_info' in event and event['user_agent_info']['browser']['version'] == "5.0.307.11")

    def testUserAgentTargetField(self):
        self.test_object.configure({'source_fields': 'user_agent',
                                    'target_field': 'http_user_agent_data'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        event = Utils.getDefaultEventDict({'user_agent': "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.307.11 Safari/532.9"})
        for event in self.test_object.handleEvent(event):
            self.assert_('http_user_agent_data' in event and event['http_user_agent_data']['browser']['version'] == "5.0.307.11")

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()