# -*- coding: utf-8 -*-
import logging
import threading
import SocketServer
import ssl
import sys
import socket
import Queue
import Utils
import BaseModule
from Decorators import ModuleDocstringParser

class ThreadPoolMixIn(SocketServer.ThreadingMixIn):
    """
    Use a thread pool instead of a new thread on every request.

    Using a threadpool prevents the spawning of a new thread for each incoming
    request. This should increase performance a bit.

    See: http://code.activestate.com/recipes/574454/
    """
    numThreads = 15
    allow_reuse_address = True  # seems to fix socket.error on server restart
    is_alive = True

    def serve_forever(self):
        """
        Handle one request at a time until doomsday.
        """
        # Set up the threadpool.
        self.requests = Queue.Queue(self.numThreads)

        for x in range(self.numThreads):
            t = threading.Thread(target=self.process_request_thread)
            t.setDaemon(1)
            t.start()

        # server main loop
        while self.is_alive:
            self.handle_request()

        self.server_close()


    def process_request_thread(self):
        """
        obtain request from queue instead of directly from server socket
        """
        while True:
            SocketServer.ThreadingMixIn.process_request_thread(self, *self.requests.get())


    def handle_request(self):
        """
        simply collect requests and put them on the queue for the workers.
        """
        try:
            request, client_address = self.get_request()
        except:
            etype, evalue, etb = sys.exc_info()
            print "Exception: %s, Error: %s." % (etype, evalue)
            return
        #if self.verify_request(request, client_address):
        self.requests.put((request, client_address))


class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
    def __init__(self, tcp_server_instance, *args, **keys):
        self.tcp_server_instance = tcp_server_instance
        self.logger = logging.getLogger(self.__class__.__name__)
        SocketServer.BaseRequestHandler.__init__(self, *args, **keys)

    def handle(self):
        try:
            host, port = self.request.getpeername()
            data = True
            while data:
                data = self.rfile.readline().strip()
                if data == "":
                    continue
                self.tcp_server_instance.handleEvent(Utils.getDefaultEventDict({"received_from": "%s" % host, "data": data}))
        except socket.error, e:
           self.logger.warning("%sError occurred while reading from socket. Error: %s%s" % (Utils.AnsiColors.WARNING, e, Utils.AnsiColors.ENDC))
        except socket.timeout, e:
            self.logger.warning("%sTimeout occurred while reading from socket. Error: %s%s" % (Utils.AnsiColors.WARNING, e, Utils.AnsiColors.ENDC))
        finally:
            self.finish()

class ThreadedTCPServer(ThreadPoolMixIn, SocketServer.TCPServer):

    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, timeout=None, tls=False, key=False, cert=False, ssl_ver = ssl.PROTOCOL_SSLv23):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.socket.settimeout(timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.use_tls = tls
        self.timeout = timeout
        if tls == True:
            self.socket = ssl.wrap_socket(self.socket,
                                          server_side=True,
                                          keyfile=key,
                                          certfile=cert,
                                          cert_reqs=ssl.CERT_NONE,
                                          ssl_version=ssl_ver,
                                          do_handshake_on_connect=False,
                                          suppress_ragged_eofs=True)

    def get_request(self):
        (socket, addr) = SocketServer.TCPServer.get_request(self)
        if self.use_tls:
            socket.settimeout(self.timeout)
            socket.do_handshake()
        return (socket, addr)

class TCPRequestHandlerFactory:
    def produce(self, tcp_server_instance):
        def createHandler(*args, **keys):
            return ThreadedTCPRequestHandler(tcp_server_instance, *args, **keys)
        return createHandler

@ModuleDocstringParser
class TcpServerThreaded(BaseModule.BaseModule):
    """
    Reads data from tcp socket and sends it to its output queues.
    This incarnation of a TCP Server is (at least on Linux) not as fast as the TcpServerTornado.

    Configuration example:

    - module: TcpServerThreaded
      configuration:
        interface: localhost             # <default: 'localhost'; type: string; is: optional>
        port: 5151                       # <default: 5151; type: integer; is: optional>
        timeout: 5                       # <default: None; type: None||integer; is: optional>
        tls: False                       # <default: False; type: boolean; is: optional>
        key: /path/to/cert.key           # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert: /path/to/cert.crt          # <default: False; type: boolean||string; is: required if tls is True else optional>
      receivers:
        - NextModule
    """

    module_type = "input"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.server = False

    def run(self):
        if not self.addReceiver:
            self.logger.warning("%sWill not start module %s since no output queue set.%s" % (Utils.AnsiColors.WARNING, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        handler_factory = TCPRequestHandlerFactory()
        try:
            self.server = ThreadedTCPServer((self.getConfigurationValue("interface"),
                                             self.getConfigurationValue("port")),
                                             handler_factory.produce(self),
                                             timeout=self.getConfigurationValue("timeout"),
                                             tls=self.getConfigurationValue("tls"),
                                             key=self.getConfigurationValue("key"),
                                             cert=self.getConfigurationValue("cert"))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not listen on %s:%s. Exception: %s, Error: %s%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue("interface"),
                                                                                            self.getConfigurationValue("port"), etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
            return
        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        self.server_thread.daemon = True
        self.server_thread.start()

    def handleEvent(self, event):
        self.sendEvent(event)

    def shutDown(self):
        if self.server and self.is_alive:
            self.server.server_close()
