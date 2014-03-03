#coding:utf-8
import sys
import os
import socket
from tornado import netutil
from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer

import Utils
import BaseThreadedModule
from Decorators import ModuleDocstringParser

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
        self.gp_module.sendEvent(Utils.getDefaultEventDict({"received_from": self.address, "data": data}, caller_class_name='UnixSocket'))
        if not self.stream.closed():
            self.stream.read_until_regex(b'\r?\n', self._on_read_line)

    def _on_close(self):
        self.stream.close()

@ModuleDocstringParser
class UnixSocket(BaseThreadedModule.BaseThreadedModule):
    """
    Reads data from an unix socket and sends it to its output queues.

    Configuration example:

    - UnixSocket:
        path_to_socket:         # <type: string; is: required>
        receivers:
          - NextModule
    """

    module_type = "input"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.running = False

    def run(self):
        if not self.receivers:
            self.logger.error("%sWill not start module %s since no receivers are set.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        try:
            self.unix_socket = netutil.bind_unix_socket(self.getConfigurationValue('path_to_socket'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sWill not start module %s. Could not create unix socket %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, self.getConfigurationValue('path_to_socket'), etype, evalue, Utils.AnsiColors.ENDC))
            return
        try:
            self.server = SocketServer(gp_module=self)
            self.server.add_socket(self.unix_socket)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not access socket %s. Exception: %s, Error: %s%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("path_to_socket"), etype, evalue, Utils.AnsiColors.ENDC))
            return
        self.running = True
        #self.server.start(0)
        IOLoop.instance().start()

    def shutDown(self, silent):
        if self.running:
            try:
                os.remove(self.getConfigurationValue('path_to_socket'))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not remove socket %s. Exception: %s, Error: %s%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("path_to_socket"), etype, evalue, Utils.AnsiColors.ENDC))
        return