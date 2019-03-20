import sys
import time
import mock
import socket
import ssl
import lumbermill.utils.DictUtils as DictUtils

from lumbermill.constants import LUMBERMILL_BASEPATH
from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.input import BeatsServer


class TestBeatsServer(ModuleBaseTestCase):

    def setUp(self):
        super(TestBeatsServer, self).setUp(BeatsServer.BeatsServer(mock.Mock()))



    def tearDown(self):
        self.test_object.shutDown()
        ModuleBaseTestCase.tearDown(self)