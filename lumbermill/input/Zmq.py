# -*- coding: utf-8 -*-
import socket
import sys

import zmq

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class Zmq(BaseThreadedModule):
    """
    Read events from a zeromq.


    mode: Whether to run a server or client.
    address: Address to connect to. Pattern: hostname:port. If mode is server, this sets the addresses to listen on.
    pattern: One of 'pull', 'sub'.
    hwm: Highwatermark for sending/receiving socket.

    Configuration template:

    - Zmq:
       mode:                            # <default: 'server'; type: string; values: ['server', 'client']; is: optional>
       address:                         # <default: '*:5570'; type: string; is: optional>
       pattern:                         # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
       topic:                           # <default: ''; type: string; is: optional>
       hwm:                             # <default: None; type: None||integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.topic = self.getConfigurationValue('topic')
        self.pattern = self.getConfigurationValue('pattern')
        self.context = zmq.Context()
        if self.pattern == 'pull':
            self.socket = self.context.socket(zmq.PULL)
        elif self.pattern == 'sub':
            self.socket = self.context.socket(zmq.SUB)
            self.socket.setsockopt(zmq.SUBSCRIBE, str(self.topic))
        if self.getConfigurationValue('hwm'):
            self.setReceiveHighWaterMark(self.getConfigurationValue('hwm'))
        server_addr, server_port = self.getServerAddress(self.getConfigurationValue('address'))
        if self.getConfigurationValue('mode') == 'server':
            self.bind(server_addr, server_port)
        else:
            self.connect(server_addr, server_port)

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

    def getEventFromZmq(self):
        try:
            event = self.socket.recv()
            yield event
        except zmq.error.ContextTerminated:
            pass
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            if exc_value in ['Interrupted system call', 'Socket operation on non-socket']:
                return
            self.logger.error("Could not read data from zeromq. Exception: %s, Error: %s." % (exc_type, exc_value))

    def run(self):
        if not self.receivers:
            self.logger.error("Shutting down module %s since no receivers are set." % (self.__class__.__name__))
            return
        while self.alive:
            for event in self.getEventFromZmq():
                event = DictUtils.getDefaultEventDict({"data": event}, caller_class_name="Zmq")
                if self.pattern == 'sub':
                    topic, event['data'] = event['data'].split(' ', 1)
                    event['topic'] = topic
                self.sendEvent(event)

    def shutDown(self):
        # Call parent shutDown method.
        BaseThreadedModule.shutDown(self)
        try:
            self.socket.close()
            self.context.term()
        except AttributeError:
            pass

