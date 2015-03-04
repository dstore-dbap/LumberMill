import os
import time
import mock
import socket
import extendSysPath
import ModuleBaseTestCase
import Utils
import UnixSocket

class TestUnixSocket(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestUnixSocket, self).setUp(UnixSocket.UnixSocket(gp=mock.Mock()))

    def testUnixSocket(self):
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
        expected_ret_val = Utils.getDefaultEventDict({'data': "http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty\r\n"})
        expected_ret_val.pop('gambolputty')
        time.sleep(.5)
        event = False
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event)
        self.assertEqual(counter, 5000)
        event.pop('gambolputty')
        self.assertDictEqual(event, expected_ret_val)