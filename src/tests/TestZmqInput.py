import time
import ModuleBaseTestCase
import mock
import sys
import socket
import unittest2
import extendSysPath
import Utils
#import Zmq

class TestZmqInput(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestZmqInput, self).setUp(Zmq.Zmq(gp=mock.Mock()))

    def testZmqPull(self):
        ipaddr, port = self.getFreePortoOLocalhost()
        self.test_object.configure({'address': '%s:%s' % (ipaddr, port),
                                    'pattern': 'pull'})
        self.checkConfiguration()
        self.test_object.start()
        message = 'A comfy chair is not an effective method of torture!'
        sender = self.getZmqSocket(ipaddr, port, 'push')
        for _ in range(0, 5000):
            sender.send(message)
        sender.close()
        expected_ret_val = Utils.getDefaultEventDict({'data': 'A comfy chair is not an effective method of torture!'})
        expected_ret_val.pop('gambolputty')
        event = False
        time.sleep(.1)
        counter = 0
        for event in self.receiver.getEvent():
            counter += 1
        self.assertTrue(event is not False)
        event.pop('gambolputty')
        self.assertDictEqual(event, expected_ret_val)
        self.assertEqual(counter, 5000)

    def testZmqSubWithoutTopicFilter(self):
        ipaddr, port = self.getFreePortoOLocalhost()
        self.test_object.configure({'address': '%s:%s' % (ipaddr, port),
                                    'pattern': 'sub'})
        self.checkConfiguration()
        self.test_object.start()
        message = 'Test A comfy chair is not an effective method of torture!'
        sender = self.getZmqSocket(ipaddr, port, 'pub')
        for _ in range(0, 5000):
            sender.send(message)
        sender.close()
        expected_ret_val = Utils.getDefaultEventDict({'data': 'A comfy chair is not an effective method of torture!',
                                                      'topic': 'Test'})
        expected_ret_val.pop('gambolputty')
        event = False
        for event in self.receiver.getEvent():
            event.pop('gambolputty')
            self.assertDictEqual(event, expected_ret_val)
        self.assertTrue(event is not False)

    def testZmqSubWithTopicFilter(self):
        ipaddr, port = self.getFreePortoOLocalhost()
        self.test_object.configure({'address': '%s:%s' % (ipaddr, port),
                                    'pattern': 'sub',
                                    'topic': 'Test'})
        self.checkConfiguration()
        self.test_object.start()
        message = 'Test A comfy chair is not an effective method of torture!'
        sender = self.getZmqSocket(ipaddr, port, 'pub')
        for _ in range(0, 10000):
            sender.send(message)
        sender.close()
        expected_ret_val = Utils.getDefaultEventDict({'data': 'A comfy chair is not an effective method of torture!',
                                                      'topic': 'Test'})
        expected_ret_val.pop('gambolputty')
        self.assertTrue(self.receiver.hasEvents() is True)

    def testZmqSubWithFailingTopicFilter(self):
        ipaddr, port = self.getFreePortoOLocalhost()
        self.test_object.configure({'address': '%s:%s' % (ipaddr, port),
                                    'pattern': 'sub',
                                    'topic': 'NotThere'})
        self.checkConfiguration()
        self.test_object.start()
        message = 'Test A comfy chair is not an effective method of torture!'
        sender = self.getZmqSocket(ipaddr, port, 'pub')
        for _ in range(0, 10000):
            sender.send(message)
        sender.close()
        expected_ret_val = Utils.getDefaultEventDict({'data': 'A comfy chair is not an effective method of torture!',
                                                      'topic': 'Test'})
        expected_ret_val.pop('gambolputty')
        self.assertTrue(self.receiver.hasEvents() is False)



    def getZmqSocket(self, host, port, mode):
        context = zmq.Context()
        if mode == 'push':
            sock = context.socket(zmq.PUSH)
        else:
            sock = context.socket(zmq.PUB)
        try:
            sock.connect('tcp://%s:%s' % (host, port))
        except:
            etype, evalue, etb = sys.exc_info()
            print("Failed to connect to %s:%s. Exception: %s, Error: %s." % (host, port, etype, evalue))
        return sock

    def getFreePortoOLocalhost(self):
        # Get a free random port.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 0))
        sock.listen(socket.SOMAXCONN)
        ipaddr, port = sock.getsockname()
        return (ipaddr, port)

if __name__ == '__main__':
    unittest2.main()