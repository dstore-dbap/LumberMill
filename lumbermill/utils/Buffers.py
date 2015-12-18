# -*- coding: utf-8 -*-
import logging
import socket
import sys
import time

import pylru

try:
    import msgpack
    msgpack_avaiable = True
except ImportError:
    msgpack_avaiable = False

try:
    import zmq
    zmq_avaiable = True
except ImportError:
    zmq_avaiable = False

from lumbermill.utils.Decorators import setInterval
from lumbermill.utils.misc import TimedFunctionManager
from lumbermill.utils.DictUtils import KeyDotNotationDict

class Buffer:
    def __init__(self, flush_size=None, callback=None, interval=1, maxsize=5000):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.flush_size = flush_size
        self.buffer = []
        self.maxsize = maxsize
        self.append = self.put
        self.flush_interval = interval
        self.flush_callback = callback
        self.flush_timed_func = self.getTimedFlushMethod()
        self.timed_func_handle = TimedFunctionManager.startTimedFunction(self.flush_timed_func)
        self.is_flushing = False

    def stopInterval(self):
        TimedFunctionManager.stopTimedFunctions(self.timed_func_handle)
        self.timed_func_handle = False

    def startInterval(self):
        if self.timed_func_handle:
            self.stopInterval()
        self.timed_func_handle = TimedFunctionManager.startTimedFunction(self.flush_timed_func)

    def getTimedFlushMethod(self):
        @setInterval(self.flush_interval)
        def timedFlush():
            self.flush()
        return timedFlush

    def append(self, item):
        self.put(item)

    def put(self, item):
        # Wait till a running store is finished to avoid strange race conditions when using this buffer with multiprocessing.
        while self.is_flushing:
            time.sleep(.00001)
        while len(self.buffer) > self.maxsize:
            self.logger.warning("Maximum number of items (%s) in buffer reached. Waiting for flush." % self.maxsize)
            time.sleep(1)
        self.buffer.append(item)
        if self.flush_size and len(self.buffer) == self.flush_size:
            self.flush()

    def flush(self):
        if self.bufsize() == 0 or self.is_flushing:
            return
        self.is_flushing = True
        self.stopInterval()
        success = self.flush_callback(self.buffer)
        if success:
            self.buffer = []
        self.startInterval()
        self.is_flushing = False

    def bufsize(self):
        return len(self.buffer)

class BufferedQueue:
    def __init__(self, queue, buffersize=500):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = Buffer(buffersize, self.sendBuffer, 5)

    def startInterval(self):
        self.buffer.startInterval()

    def put(self, payload):
        self.buffer.append(payload)

    def sendBuffer(self, buffered_data):
        try:
            buffered_data = msgpack.packb(buffered_data)
            self.queue.put(buffered_data)
            return True
        except (KeyboardInterrupt, SystemExit):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not append data to queue. Exception: %s, Error: %s." % (etype, evalue))

    def get(self, block=True, timeout=None):
        try:
            buffered_data = self.queue.get(block, timeout)
            buffered_data = msgpack.unpackb(buffered_data)
            # After msgpack.uppackb we just have a normal dict. Cast this to KeyDotNotationDict.
            for data in buffered_data:
                yield KeyDotNotationDict(data)
        except (KeyboardInterrupt, SystemExit, ValueError, OSError):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass

    def qsize(self):
        return self.buffer.bufsize() + self.queue.qsize()

    def __getattr__(self, name):
        return getattr(self.queue, name)

class ZeroMqMpQueue:
    """
    Use ZeroMQ for IPC.
    This is faster than the default multiprocessing.Queue.

    Sender and receiver will be initalized on first put/get. This is neccessary since a zmq context will not
    survive a fork.

    send_pyobj and recv_pyobj is not used since it performance is slower than using msgpack for serialization.
    (A test for a simple dict using send_pyobj et.al performed around 12000 eps, while msgpack and casting to
    KeyDotNotationDict after unpacking resulted in around 17000 eps)
    """
    def __init__(self, queue_max_size=20):
        # Get a free random port.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 0))
        sock.listen(socket.SOMAXCONN)
        ipaddr, self.port = sock.getsockname()
        sock.close()
        self.queue_max_size = queue_max_size
        self.queue_size = 0
        self.sender = None
        self.receiver = None

    def initSender(self):
        zmq_context = zmq.Context()
        self.sender = zmq_context.socket(zmq.PUSH)
        try:
            self.sender.setsockopt(zmq.SNDHWM, self.queue_max_size)
        except AttributeError:
            self.sender.setsockopt(zmq.HWM, self.queue_max_size)
        try:
            self.sender.bind("tcp://127.0.0.1:%d" % self.port)
        except zmq.error.ZMQError:
            print("Address in use. Connecting only.")
            self.sender.connect("tcp://127.0.0.1:%d" % self.port)


    def initReceiver(self):
        #print("Init receiver in %s" % os.getpid())
        zmq_context = zmq.Context()
        self.receiver = zmq_context.socket(zmq.PULL)
        try:
            self.receiver.setsockopt(zmq.RCVHWM, self.queue_max_size)
        except AttributeError:
            self.receiver.setsockopt(zmq.HWM, self.queue_max_size)
        self.receiver.connect("tcp://127.0.0.1:%d" % self.port)

    def put(self, data):
        if not self.sender:
            self.initSender()
        self.sender.send(data)

    def get(self, block=None, timeout=None):
        if not self.receiver:
            self.initReceiver()
        events = ""
        try:
            events = self.receiver.recv()
            return events
        except zmq.error.ZMQError as e:
            # Ignore iterrupt error caused by SIGINT
            if e.strerror == "Interrupted system call":
                return events

    def qsize(self):
        return self.queue_size

class MemoryCache():

    def __init__(self, size=1000):
        self.lru_dict = pylru.lrucache(size)

    def set(self, key, value):
        self.lru_dict[key] = value

    def get(self, key):
        return self.lru_dict[key]

    def unset(self, key):
        return self.lru_dict.pop(key)