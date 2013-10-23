import logging
import threading
import SocketServer
import sys
import socket
import Queue
import Utils
import BaseModule


class ThreadPoolMixIn(SocketServer.ThreadingMixIn):
    """
    use a thread pool instead of a new thread on every request
    See: http://code.activestate.com/recipes/574454/
    """
    numThreads = 15
    allow_reuse_address = True  # seems to fix socket.error on server restart
    is_alive = True

    def serve_forever(self):
        """
        Handle one request at a time until doomsday.
        """
        # set up the threadpool
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
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))


class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
    def __init__(self, queue, *args, **keys):
        self.output_queues = queue
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
                try:
                    # [queue.put(Utils.getDefaultDataDict({"received_from": host, "data": data}), block=True, timeout=5) for queue in self.output_queues]
                    for queue in self.output_queues:
                        queue.put(Utils.getDefaultDataDict({"received_from": host, "data": data}), block=True,
                                  timeout=5)
                        BaseModule.BaseModule.incrementQueueCounter()
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error(
                        "Could not add received data to output queue. Excpeption: %s, Error: %s." % (etype, evalue))

        except socket.timeout, e:
            # Handle a timeout gracefully
            self.finish()


class ThreadedTCPServer(ThreadPoolMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    pass

class TCPRequestHandlerFactory:
    def produce(self, output_queues):
        def createHandler(*args, **keys):
            return ThreadedTCPRequestHandler(output_queues, *args, **keys)
        return createHandler


class TcpServerThreaded:

    module_type = "input"
    """Set module type"""

    def __init__(self, gp=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp = gp

    def setup(self):
        self.output_queues = []

    def configure(self, configuration):
        self.configuration_data = configuration

    def addOutputQueue(self, queue, filter_by_marker=False, filter_by_field=False):
        if queue not in self.output_queues:
            self.output_queues.append(queue)

    def run(self):
        if not self.output_queues:
            self.logger.warning("Will not start module %s since no output queue set." % (self.__class__.__name__))
            return
        handler_factory = TCPRequestHandlerFactory()
        try:
            self.server = ThreadedTCPServer((self.configuration_data["interface"], int(self.configuration_data["port"])),
                                            handler_factory.produce(self.output_queues))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not listen on %s:%s. Exception: %s, Error: %s" % (
            self.configuration_data["interface"], self.configuration_data["port"], etype, evalue))
            self.gp.shutDown()
            # Start a thread with the server -- that thread will then start one
        # more thread for each request
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        self.server_thread.daemon = True
        self.server_thread.start()

    def shutDown(self):
        self.server.server_close()
        self.server.is_alive = False