import logging
import threading
import SocketServer
import sys
import socket
import Utils
import BaseModule

class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):

    def __init__(self, queue, *args, **keys):
        self.output_queues = queue
        self.logger = logging.getLogger(self.__class__.__name__)
        SocketServer.BaseRequestHandler.__init__(self, *args, **keys)

    def handle(self):
        try:
            host,port = self.request.getpeername()
            data = True
            while data:
                data = self.rfile.readline().strip()
                try:
                    # [queue.put(Utils.getDefaultDataDict({"received_from": host, "data": data}), block=True, timeout=5) for queue in self.output_queues]
                    for queue in self.output_queues:
                        queue.put(Utils.getDefaultDataDict({"received_from": host, "data": data}), block=True, timeout=5)
                        #BaseModule.BaseModule.lock.acquire()
                        #BaseModule.BaseModule.messages_in_queues += 1
                        #BaseModule.BaseModule.lock.release()
                        BaseModule.BaseModule.incrementQueueCounter()
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("Could not add received data to output queue. Excpeption: %s, Error: %s." % (etype, evalue))
                    
        except socket.timeout, e:
            # Handle a timeout gracefully
            self.finish()

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    pass

class TCPRequestHandlerFactory:
    def produce(self, output_queues):
        def createHandler(*args, **keys):
            return ThreadedTCPRequestHandler(output_queues, *args, **keys)
        return createHandler

class TcpServerThreaded:
 
    output_queues = []
 
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
   
    def configure(self, configuration):
        self.config = configuration
   
    def addOutputQueue(self, queue, filter_by_marker=False):
        if queue not in self.output_queues:
            self.output_queues.append(queue)
    
    def run(self):
        if not self.output_queues:
            self.logger.warning("Will not start module %s since no output queue set." % (self.__class__.__name__))
            return
        handler_factory = TCPRequestHandlerFactory()
        try:
            self.server = ThreadedTCPServer((self.config["interface"], int(self.config["port"])), handler_factory.produce(self.output_queues))  
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not listen on %s:%s. Exception: %s, Error: %s" % (self.config["interface"],self.config["port"], etype, evalue))
            sys.exit(255)     
        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        self.server_thread.daemon = True
        self.server_thread.start()
        self.logger.info("Started ThreadedTCPServer on interface %s, port: %s" % (self.config["interface"], self.config["port"]))

    def shutdown(self):
        self.server.shutdown()