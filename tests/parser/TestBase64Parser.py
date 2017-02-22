import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import Base64Parser


class TestBase64Parser(ModuleBaseTestCase):

    def setUp(self):
        super(TestBase64Parser, self).setUp(Base64Parser.Base64Parser(mock.Mock()))

    def testBase64Encode(self):
        config = {'action': 'encode'}
        self.test_object.configure(config)
        self.checkConfiguration()
        payload = "I cut down trees, I skip and jump, I like to press wild flowers. I put on women's clothing and hang around in bars."
        data = DictUtils.getDefaultEventDict({'data': payload})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['data'] == 'SSBjdXQgZG93biB0cmVlcywgSSBza2lwIGFuZCBqdW1wLCBJIGxpa2UgdG8gcHJlc3Mgd2lsZCBmbG93ZXJzLiBJIHB1dCBvbiB3b21lbidzIGNsb3RoaW5nIGFuZCBoYW5nIGFyb3VuZCBpbiBiYXJzLg==' )

    def testBase64Decode(self):
        config = {'action': 'decode'}
        self.test_object.configure(config)
        self.checkConfiguration()
        payload = 'SSBjdXQgZG93biB0cmVlcywgSSBza2lwIGFuZCBqdW1wLCBJIGxpa2UgdG8gcHJlc3Mgd2lsZCBmbG93ZXJzLiBJIHB1dCBvbiB3b21lbidzIGNsb3RoaW5nIGFuZCBoYW5nIGFyb3VuZCBpbiBiYXJzLg=='
        data = DictUtils.getDefaultEventDict({'data': payload})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['data'] ==  "I cut down trees, I skip and jump, I like to press wild flowers. I put on women's clothing and hang around in bars.")

    def testBase64EncodeWithSourceAndTargetField(self):
        config = {'action': 'encode',
                  'source_field': 'encodeme',
                  'target_field': 'encoded',
                  'keep_original': False}
        self.test_object.configure(config)
        self.checkConfiguration()
        payload = "I cut down trees, I skip and jump, I like to press wild flowers. I put on women's clothing and hang around in bars."
        data = DictUtils.getDefaultEventDict({'encodeme': payload})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['encoded'] == 'SSBjdXQgZG93biB0cmVlcywgSSBza2lwIGFuZCBqdW1wLCBJIGxpa2UgdG8gcHJlc3Mgd2lsZCBmbG93ZXJzLiBJIHB1dCBvbiB3b21lbidzIGNsb3RoaW5nIGFuZCBoYW5nIGFyb3VuZCBpbiBiYXJzLg==' )
            self.assertTrue('encodeme' not in event.keys())
