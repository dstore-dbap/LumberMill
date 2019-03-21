# -*- coding: utf-8 -*-
import os
import sys
import ssl
import time
import socket
import logging
import tornado.gen
import tornado.ioloop

from tornado import autoreload
from tornado.netutil import bind_sockets
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseModule import BaseModule
from lumbermill.utils.Decorators import ModuleDocstringParser

class TornadoTcpServer(TCPServer):

    def __init__(self, ssl_options=None, gp_module=False, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp_module = gp_module
        self.simple_separator = self.gp_module.getConfigurationValue('simple_separator')
        self.regex_separator = self.gp_module.getConfigurationValue('regex_separator')
        self.chunksize = self.gp_module.getConfigurationValue('chunksize')
        self.mode = self.gp_module.getConfigurationValue('mode')
        try:
            TCPServer.__init__(self, ssl_options=ssl_options, **kwargs)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not create tcp server. Exception: %s, Error: %s." % (etype, evalue))
            self.gp_module.shutDown()

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        while True:
            try:
                if not stream.closed():
                    ch = ConnectionHandler(stream, address, self.gp_module)
                    if self.mode == 'line' and self.regex_separator:
                        yield ch.read_until_regex(self.regex_separator)
                    elif self.mode == 'line':
                        yield ch.read_until_seperator(self.simple_separator)
                    else:
                        yield ch.read_chunk(self.chunksize)
            except StreamClosedError:
                break
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not read from socket %s. Exception: %s, Error: %s." % (address, etype, evalue))

class ConnectionHandler(object):

    def __init__(self, stream, address, gp_module):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp_module = gp_module
        self.stream = stream
        self.address = address
        self.host, self.port = self.address[0], self.address[1]
        self.stream.set_close_callback(self._on_close)

    @tornado.gen.coroutine
    def read_until_seperator(self, seperator):
        data = yield self.stream.read_until(seperator)
        data = data.strip()
        if data == "":
            return
        self.sendEvent(data)

    @tornado.gen.coroutine
    def read_until_regex(self, seperator_regex):
        data = yield self.stream.read_until_regex(seperator_regex)
        data = data.strip()
        if data == "":
            return
        self.sendEvent(data)

    @tornado.gen.coroutine
    def read_chunk(self, chunksize):
        data = yield self.stream.read_bytes(chunksize)
        if data == "":
            return
        self.sendEvent(data)

    def _on_close(self):
        # Send remaining buffer if neccessary.
        data = ""
        if self.stream and self.stream._read_buffer_size > 0:
            while True:
                try:
                    data += self.stream._read_buffer.popleft().strip()
                except IndexError:
                    break
                except AttributeError:
                    #print(self.stream._read_buffer)
                    sys.exit()
        if data != "":
            self.sendEvent(data)
        self.stream.close()

    def sendEvent(self, data):
        self.gp_module.sendEvent(DictUtils.getDefaultEventDict({"data": data}, caller_class_name="TcpServer", received_from="%s:%d" % (self.host, self.port)))


@ModuleDocstringParser
class TcpServer(BaseModule):
    r"""
    Reads data from tcp socket and sends it to its outputs.
    Should be the best choice perfomancewise if you are on Linux and are running with multiple workers.

    interface:  Ipaddress to listen on.
    port:       Port to listen on.
    timeout:    Sockettimeout in seconds.
    tls:        Use tls or not.
    key:        Path to tls key file.
    cert:       Path to tls cert file.
    cacert:     Path to ca cert file.
    tls_proto:  Set TLS protocol version.
    mode:       Receive mode, line or stream.
    simple_separator:  If mode is line, set separator between lines.
    regex_separator:   If mode is line, set separator between lines. Here regex can be used. The result includes the data that matches the regex.
    chunksize:  If mode is stream, set chunksize in bytes to read from stream.
    max_buffer_size: Max kilobytes to in receiving buffer.

    Configuration template:

    - TcpServer:
       interface:                       # <default: ''; type: string; is: optional>
       port:                            # <default: 5151; type: integer; is: optional>
       timeout:                         # <default: None; type: None||integer; is: optional>
       tls:                             # <default: False; type: boolean; is: optional>
       key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
       cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
       cacert:                          # <default: False; type: boolean||string; is: optional>
       tls_proto:                       # <default: 'TLSv1'; type: string; values: ['TLSv1', 'TLSv1_1', 'TLSv1_2']; is: optional>
       mode:                            # <default: 'line'; type: string; values: ['line', 'stream']; is: optional>
       simple_separator:                # <default: '\n'; type: string; is: optional>
       regex_separator:                 # <default: None; type: None||string; is: optional>
       chunksize:                       # <default: 16384; type: integer; is: required if mode is 'stream' else optional>
       max_buffer_size:                 # <default: 10240; type: integer; is: optional>
       receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""
    can_run_forked = True

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.configure(self, configuration)
        self.alive = True
        ssl_options = None
        if self.getConfigurationValue("tls"):
            ssl_options = {'ssl_version': getattr(ssl, "PROTOCOL_%s" % self.getConfigurationValue("tls_proto")),
                           'certfile': self.getConfigurationValue("cert"),
                           'keyfile': self.getConfigurationValue("key")}
        self.server = TornadoTcpServer(ssl_options=ssl_options, gp_module=self, max_buffer_size=self.getConfigurationValue('max_buffer_size') * 10240)
        try:
            self.sockets = bind_sockets(self.getConfigurationValue("port"), self.getConfigurationValue("interface"), backlog=128)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not listen on %s:%s. Exception: %s, Error: %s." % (self.getConfigurationValue("interface"),
                                                                                        self.getConfigurationValue("port"), etype, evalue))
            self.lumbermill.shutDown()
            return
        for server_socket in self.sockets:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        autoreload.add_reload_hook(self.shutDown)

    def getStartMessage(self):
        start_msg = "listening on %s:%s" % (self.getConfigurationValue("interface"), self.getConfigurationValue("port"))
        if self.getConfigurationValue("tls"):
            start_msg += " (with %s)" % self.getConfigurationValue("tls_proto")
        return start_msg

    def initAfterFork(self):
        BaseModule.initAfterFork(self)
        try:
            self.server.add_sockets(self.sockets)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not add sockets to forked server process: Exception: %s, Error: %s." % (etype, evalue))
            self.shutDown()

    def shutDown(self):
        self.server.stop()
        for server_socket in self.sockets:
            try:
                server_socket.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            server_socket.close()

