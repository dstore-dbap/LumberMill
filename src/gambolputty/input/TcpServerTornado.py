# -*- coding: utf-8 -*-
import sys
import logging
import time
import socket
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado import autoreload
import Utils
import BaseThreadedModule
from Decorators import ModuleDocstringParser

class TornadoTcpServer(TCPServer):

    def __init__(self, io_loop=None, ssl_options=None, gp_module=False, **kwargs):
        self.gp_module = gp_module
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)

    def handle_stream(self, stream, address):
        ConnectionHandler(stream, address, self.gp_module)

class ConnectionHandler(object):

    def __init__(self, stream, address, gp_module):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp_module = gp_module
        self.seperator = self.gp_module.getConfigurationValue('seperator')
        self.chunksize = self.gp_module.getConfigurationValue('chunksize')
        self.is_open = True
        self.stream = stream
        self.address = address
        (self.host, self.port) = self.address
        self.stream.set_close_callback(self._on_close)
        if not self.stream.closed():
            if self.gp_module.getConfigurationValue('mode') == 'line':
                self.stream.read_until(self.seperator, self._on_read_line)
            else:
                self.stream.read_bytes(self.chunksize, self._on_read_chunk)

    def _on_read_line(self, data):
        data = data.strip()
        if data == "":
            return
        event = Utils.getDefaultEventDict({"received_from": self.host, "data": data}, caller_class_name="TcpServerTornado")
        self.gp_module.sendEvent(event)
        try:
            if not self.stream.reading():
                self.stream.read_until(self.seperator, self._on_read_line)
        except StreamClosedError:
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sFailed to read from stream. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))

    def _on_read_chunk(self, data):
        data = data.strip()
        if data == "":
            return
        event = Utils.getDefaultEventDict({"received_from": self.host, "data": data}, caller_class_name="TcpServerTornado")
        self.gp_module.sendEvent(event)
        try:
            if not self.stream.reading():
                self.stream.read_bytes(self.chunksize, self._on_read_chunk)
        except StreamClosedError:
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sFailed to read from stream. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))

    def _on_close(self):
        # Send remaining buffer if neccessary.
        if self.gp_module.getConfigurationValue('mode') == 'stream' and self.stream._read_buffer_size > 0:
            data = ""
            while True:
                try:
                    data += self.stream._read_buffer.popleft().strip()
                except IndexError:
                    if data != "":
                        event = Utils.getDefaultEventDict({"received_from": self.host, "data": data}, caller_class_name="TcpServerTornado")
                        self.gp_module.sendEvent(event)
                    break
        self.stream.close()

@ModuleDocstringParser
class TcpServerTornado(BaseThreadedModule.BaseThreadedModule):
    r"""
    Reads data from tcp socket and sends it to its output queues.
    Should be the best choice perfomancewise if you are on Linux.

    interface:  Ipaddress to listen on.
    port:       Port to listen on.
    timeout:    Sockettimeout in seconds.
    tls:        Use tls or not.
    key:        Path to tls key file.
    cert:       Path to tls cert file.
    mode:       Receive mode, line or stream.
    seperator:  If mode is line, set seperator between lines.
    chunksize:  If mode is stream, set chunksize in bytes to read from stream.
    max_buffer_size: Max kilobytes to in receiving buffer.

    Configuration example:

    - module: TcpServerTornado
      interface:                       # <default: ''; type: string; is: optional>
      port:                            # <default: 5151; type: integer; is: optional>
      timeout:                         # <default: None; type: None||integer; is: optional>
      tls:                             # <default: False; type: boolean; is: optional>
      key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
      cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
      mode:                            # <default: 'line'; type: string; values: ['line', 'stream']; is: optional>
      seperator:                       # <default: '\n'; type: string; is: optional>
      chunksize:                       # <default: 16384; type: integer; is: optional>
      max_buffer_size:                 # <default: 1024; type: integer; is: optional>
      receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""

    can_run_parallel = False

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.server = False
        self.max_buffer_size = self.getConfigurationValue('max_buffer_size') * 102400

    def run(self):
        if not self.receivers:
            self.logger.error("%sWill not start module %s since no receivers are set.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        try:
            ssl_options = None
            if self.getConfigurationValue("tls"):
                ssl_options = { 'certfile': self.getConfigurationValue("cert"),
                                'keyfile': self.getConfigurationValue("key")}
            self.server = TornadoTcpServer(ssl_options=ssl_options, gp_module=self, max_buffer_size=self.max_buffer_size)
            self.server.listen(self.getConfigurationValue("port"), self.getConfigurationValue("interface"))
            for fd, server_socket in self.server._sockets.iteritems():
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not listen on %s:%s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("interface"),
                                                                                       self.getConfigurationValue("port"), etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
            return
        autoreload.add_reload_hook(self.shutDown)
        return
        ioloop = IOLoop.instance()
        ioloop.make_current()
        try:
            ioloop.start()
        except ValueError:
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutDown(self, silent):
        # Call parent shutDown method
        BaseThreadedModule.BaseThreadedModule.shutDown(self, silent)
        if self.server:
            self.server.stop()
            # Give os time to free the socket. Otherwise a reload will fail with 'address already in use'
            time.sleep(.2)