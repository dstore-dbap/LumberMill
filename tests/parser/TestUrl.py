import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import Url


class TestUrl(ModuleBaseTestCase):

    def setUp(self):
        super(TestUrl, self).setUp(Url.Url(mock.Mock()))

    def testHandleEvent(self):
        self.test_object.configure({'source_field': 'uri'})
        self.checkConfiguration()
        data = DictUtils.getDefaultEventDict({'uri': 'http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty'})
        for event in self.test_object.handleEvent(data):
            self.assert_('uri' in event and event['uri']['query'] == 'gambol=putty')
