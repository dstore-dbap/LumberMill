# -*- coding: utf-8 -*-
import socket
import sys
import zmq
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

import lumbermill.Utils as Utils
from lumbermill.BaseModule import BaseModule
from lumbermill.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class ZmqTornado(BaseModule):
    """
    Read events from a zeromq.

    mode: Whether to run a server or client.
    address: Address to connect to. Pattern: hostname:port. If mode is server, this sets the addresses to listen on.
    pattern: One of 'pull', 'sub'.
    hwm: Highwatermark for sending/receiving socket.
    separator: When using the sub pattern, messages can have a topic. Set separator to split message from topic.

    Configuration template:

    - ZmqTornado:
       mode:                            # <default: 'server'; type: string; values: ['server', 'client']; is: optional>
       address:                         # <default: '*:5570'; type: string; is: optional>
       pattern:                         # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
       topic:                           # <default: ''; type: string; is: optional>
       separator:                       # <default: None; type: None||string; is: optional>
       hwm:                             # <default: None; type: None||integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    zmq_pattern_mapping = {'push': zmq.PUSH,
                           'pull': zmq.PULL,
                           'pub': zmq.PUB,
                           'sub': zmq.SUB}

    def configure(self, configuration):
         # Call parent configure method
        BaseModule.configure(self, configuration)
        self.client = None
        self.topic = self.getConfigurationValue('topic')
        self.separator = self.getConfigurationValue('separator')
        self.context = zmq.Context()
        self.socket = self.context.socket(self.zmq_pattern_mapping[self.getConfigurationValue('pattern')])
        if self.getConfigurationValue('hwm'):
            self.setReceiveHighWaterMark(self.getConfigurationValue('hwm'))
        server_addr, server_port = self.getServerAddress(self.getConfigurationValue('address'))
        if self.getConfigurationValue('mode') == 'server':
            self.bind(server_addr, server_port)
        else:
            self.connect(server_addr, server_port)
        self.socket = zmqstream.ZMQStream(self.socket)
        self.socket.on_recv(self.onReceive)

    def getServerAddress(self, server_name):
        # ZMQ does not like hostnames too much. Try to get the ip address for server name.
        server_name, server_port = server_name.split(":")
        try:
            server_addr = socket.gethostbyname(server_name)
        except socket.gaierror:
            server_addr = server_name
        return (server_addr, server_port)

    def setReceiveHighWaterMark(self, hwm):
        try:
            self.socket.setsockopt(zmq.RCVHWM, hwm)
        except:
            self.socket.setsockopt(zmq.HWM, hwm)

    def bind(self, server_addr, server_port):
        try:
            self.socket.bind('tcp://%s:%s' % (server_addr, server_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not bind to %s:%s. Exception: %s, Error: %s." % (server_addr, server_port, etype, evalue))
            self.lumbermill.shutDown()

    def connect(self, server_addr, server_port):
        try:
            self.socket.connect('tcp://%s:%s' % (server_addr, server_port))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not connect to zeromq at %s:%s. Exception: %s, Error: %s." % (server_addr, server_port, etype, evalue))
            self.lumbermill.shutDown()

    def onReceive(self, data):
        data = data[0]
        if self.separator:
            topic, data = data.split(self.separator)
        event = Utils.getDefaultEventDict({"data": data}, caller_class_name="ZmqTornado")
        self.sendEvent(event)

    def shutDown(self):
        try:
            self.socket.close()
            self.context.term()
        except AttributeError:
            pass
        # Call parent shutDown method.
        BaseModule.shutDown(self)