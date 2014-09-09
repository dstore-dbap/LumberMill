import os
import time
import tornado.ioloop
import extendSysPath
import mock
import socket
import ModuleBaseTestCase
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
        unix_socket.send(b"http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty\r\n")
        time.sleep(.1)
        event = False
        for event in self.receiver.getEvent():
            self.assert_('data' in event and event['data'] == 'http://en.wikipedia.org/wiki/Monty_Python/?gambol=putty\r\n')
        self.assertTrue(event)
        unix_socket.close()