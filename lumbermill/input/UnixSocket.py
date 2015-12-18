#coding:utf-8
import os
import socket
import sys

from tornado import netutil
from tornado.tcpserver import TCPServer

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


class SocketServer(TCPServer):

    def __init__(self, io_loop=None, ssl_options=None, gp_module=False, **kwargs):
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
        self.gp_module = gp_module
        self.address = socket.gethostname()

    def handle_stream(self, stream, address):
        ConnectionHandler(stream, self.address, self.gp_module)

class ConnectionHandler(object):

    stream_set = set([])

    def __init__(self, stream, address, gp_module):
        self.gp_module = gp_module
        self.is_open = True
        self.stream = stream
        self.address = address
        self.stream.set_close_callback(self._on_close)
        if not self.stream.closed():
            self.stream.read_until_regex(b'\r?\n', self._on_read_line)

    def _on_read_line(self, data):
        self.gp_module.sendEvent(DictUtils.getDefaultEventDict({"data": data}, caller_class_name='UnixSocket', received_from=self.address))
        if not self.stream.closed():
            self.stream.read_until_regex(b'\r?\n', self._on_read_line)

    def _on_close(self):
        self.stream.close()

@ModuleDocstringParser
class UnixSocket(BaseThreadedModule):
    """
    Reads data from an unix socket and sends it to its output queues.

    Configuration template:

    - UnixSocket:
       path_to_socket:                  # <type: string; is: required>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.running = False

    def start(self):
        if not self.receivers:
            self.logger.error("Will not start module %s since no receivers are set." % (self.__class__.__name__))
            return
        try:
            self.unix_socket = netutil.bind_unix_socket(self.getConfigurationValue('path_to_socket'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Will not start module %s. Could not create unix socket %s. Exception: %s, Error: %s." % (self.__class__.__name__, self.getConfigurationValue('path_to_socket'), etype, evalue))
            return
        try:
            self.server = SocketServer(gp_module=self)
            self.server.add_socket(self.unix_socket)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not access socket %s. Exception: %s, Error: %s" % (self.getConfigurationValue("path_to_socket"), etype, evalue))
            return
        self.running = True
        #self.server.start(0)
        #ioloop.IOLoop.instance().start()

    def shutDown(self):
        if self.running:
            try:
                os.remove(self.getConfigurationValue('path_to_socket'))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not remove socket %s. Exception: %s, Error: %s" % (self.getConfigurationValue("path_to_socket"), etype, evalue))
        return