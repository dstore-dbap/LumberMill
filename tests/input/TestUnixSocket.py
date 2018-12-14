import os
import time
import mock
import socket
import unittest
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.input import UnixSocket

class TestUnixSocket(ModuleBaseTestCase):

    def setUp(self):
        super(TestUnixSocket, self).setUp(UnixSocket.UnixSocket(mock.Mock()))

    def testUnixSocket(self):
        raise unittest.SkipTest('Skipping test because no UnixSocket input is currently broken.')
        try:
            os.remove('/tmp/test.sock')
        except OSError:
            pass
        self.assertFalse(os.path.exists('/tmp/test.sock'))
        self.test_object.configure({'path_to_socket': '/tmp/test.sock'})
        self.checkConfiguration()
        self.test_object.start()
        self.startTornadoEventLoop()
        time.sleep(.1)
        self.assertTrue(os.path.exists('/tmp/test.sock'))
        unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            unix_socket.connect('/tmp/test.sock')
        except socket.errno:
            self.fail("Could not connect to unix socket.")
        for _ in range(0,5000):
            unix_socket.send(b"http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty\r\n")
        expected_ret_val = DictUtils.getDefaultEventDict({'data': "http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty\r\n"})
        expected_ret_val.pop('lumbermill')
        time.sleep(.5)
        event = False
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event)
        self.assertEqual(counter, 5000)
        event.pop('lumbermill')
        self.assertDictEqual(event, expected_ret_val)