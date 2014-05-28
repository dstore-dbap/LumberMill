#!/usr/bin/env python
#
# Copyright 2009 Phus Lu
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Blocking and non-blocking Redis client implementations using IOStream."""

import logging
import socket

from collections import deque
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.util import bytes_type

def encode(request):
    """Encode request (command, *args) to redis bulk bytes.

    Note that command is a string defined by redis.
    All elements in args should be a string.
    """
    assert isinstance(request, tuple)
    data = '*%d\r\n' % len(request) + ''.join(['$%d\r\n%s\r\n' % (len(str(x)), x) for x in request])
    return data

def decode(read_buffer):
    """Decode redis buffer to python object."""
    assert isinstance(read_buffer, deque)
    first_line = read_buffer.popleft()
    c = first_line[0]
    if c == '+':
        return first_line[1:-2]
    elif c == '-':
        return RedisError(first_line[1:-2], data)
    elif c == ':':
        return int(first_line[1:])
    elif c == '$':
        number = int(first_line[1:])
        if number == -1:
            return None
        else:
            return read_buffer[0][:number]
    elif c == '*':
        number = int(first_line[1:])
        if number == -1:
            return None
        else:
            result = []
            while number:
                line = read_buffer.popleft()
                c = line[0]
                if c == '$':
                    length  = int(line[1:])
                    element = read_buffer.popleft()[:length]
                    result.append(element)
                else:
                    if c == ':':
                        element = int(line[1:])
                    else:
                        element = read_buffer.popleft()[:-2]
                    result.append(element)
                number -= 1
            return result
    else:
        raise RedisError('bulk cannot startswith %r' % c, data)

class RedisClient(object):
    """A blocking Redis client.

    This interface is provided for convenience and testing; most applications
    that are running an IOLoop will want to use `AsyncRedisClient` instead.
    Typical usage looks like this::

        redis_client = redisclient.RedisClient(('127.0.0.1', 6379))
        try:
            result = redis_client.fetch(('set', 'foo', 'bar'))
            print result
        except redisclient.RedisError, e:
            print "Error:", e
    """
    def __init__(self, address):
        self.address = address
        self._io_loop = IOLoop()
        self._async_client = AsyncRedisClient(self.address, self._io_loop)
        self._result = None
        self._closed = False

    def __del__(self):
        self.close()

    def close(self):
        """Closes the RedisClient, freeing any resources used."""
        if not self._closed:
            self._async_client.close()
            self._io_loop.close()
            self._closed = True

    def fetch(self, request, **kwargs):
        """Executes a request, returning an `result`.

        The request may be a tuple object. like ('set','foo','bar')

        If an error occurs during the fetch, we raise an `RedisError`.
        """
        def callback(result):
            self._result = result
            self._io_loop.stop()
        self._async_client.fetch(request, callback, **kwargs)
        self._io_loop.start()
        result = self._result
        self._result = None
        return result

class AsyncRedisClient(object):
    """An non-blocking Redis client.

    Example usage::

        import ioloop

        def handle_request(result):
            print 'Redis reply: %r' % result
            ioloop.IOLoop.instance().stop()

        redis_client = AsyncRedisClient(('127.0.0.1', 6379))
        redis_client.fetch(('set', 'foo', 'bar'), None)
        redis_client.fetch(('get', 'foo'), handle_request)
        ioloop.IOLoop.instance().start()

    This class implements a Redis client on top of Tornado's IOStreams.
    It does not currently implement all applicable parts of the Redis
    specification, but it does enough to work with major redis server APIs
    (mostly tested against the LIST/HASH/PUBSUB API so far).

    This class has not been tested extensively in production and
    should be considered somewhat experimental as of the release of
    tornado 1.2.  It is intended to become the default tornado
    AsyncRedisClient implementation.
    """

    def __init__(self, address, io_loop=None, socket_timeout=10):
        """Creates a AsyncRedisClient.

        address is the tuple of redis server address that can be connect by
        IOStream. It can be to ('127.0.0.1', 6379).
        """
        self.address         = address
        self.io_loop         = io_loop or IOLoop.instance()
        self._callback_queue = deque()
        self._callback       = None
        self._read_buffer    = None
        self._result_queue   = deque()
        self.socket          = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(socket_timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.stream          = IOStream(self.socket, self.io_loop)
        self.stream.connect(self.address, self._wait_result)

    def close(self):
        """Destroys this redis client, freeing any file descriptors used.
        Not needed in normal use, but may be helpful in unittests that
        create and destroy redis clients.  No other methods may be called
        on the AsyncRedisClient after close().
        """
        self.stream.close()

    def fetch(self, request, callback):
        """Executes a request, calling callback with an redis `result`.

        The request should be a string tuple. like ('set', 'foo', 'bar')

        If an error occurs during the fetch, a `RedisError` exception will
        throw out. You can use try...except to catch the exception (if any)
        in the callback.
        """
        self._callback_queue.append(callback)
        self.stream.write(encode(request))

    def _wait_result(self):
        """Read a completed result data from the redis server."""
        self._read_buffer = deque()
        self.stream.read_until('\r\n', self._on_read_first_line)

    def _maybe_callback(self):
        """Try call callback in _callback_queue when we read a redis result."""
        try:
            read_buffer    = self._read_buffer
            callback       = self._callback
            result_queue   = self._result_queue
            callback_queue = self._callback_queue
            if result_queue:
                result_queue.append(read_buffer)
                read_buffer = result_queue.popleft()
            if callback_queue:
                callback = self._callback = callback_queue.popleft()
            if callback:
                callback(decode(read_buffer))
        except Exception:
            logging.error('Uncaught callback exception', exc_info=True)
            self.close()
            raise
        finally:
            self._wait_result()

    def _on_read_first_line(self, data):
        self._read_buffer.append(data)
        c = data[0]
        if c in ':+-':
            self._maybe_callback()
        elif c == '$':
            if data[:3] == '$-1':
                self._maybe_callback()
            else:
                length = int(data[1:])
                self.stream.read_bytes(length+2, self._on_read_bulk_body)
        elif c == '*':
            if data[1] in '-0' :
                self._maybe_callback()
            else:
                self._multibulk_number = int(data[1:])
                self.stream.read_until('\r\n', self._on_read_multibulk_bulk_head)

    def _on_read_bulk_body(self, data):
        self._read_buffer.append(data)
        self._maybe_callback()

    def _on_read_multibulk_bulk_head(self, data):
        self._read_buffer.append(data)
        c = data[0]
        if c == '$':
            length = int(data[1:])
            self.stream.read_bytes(length+2, self._on_read_multibulk_bulk_body)
        else:
            self._maybe_callback()

    def _on_read_multibulk_bulk_body(self, data):
        self._read_buffer.append(data)
        self._multibulk_number -= 1
        if self._multibulk_number:
            self.stream.read_until('\r\n', self._on_read_multibulk_bulk_head)
        else:
            self._maybe_callback()

class RedisError(Exception):
    """Exception thrown for an unsuccessful Redis request.

    Attributes:

    data - Redis error data error code, e.g. -(ERR).
    """
    def __init__(self, message, data=None):
        self.data = data
        Exception.__init__(self, '(Error): %s' % message)


def test():
    def handle_request(result):
        print 'Redis reply: %r' % result
    redis_client = AsyncRedisClient(('localhost', 6379))
    redis_client.fetch(('subscribe', 'GamboPutty'), handle_request)
    #redis_client.fetch(('set', 'foo', 'bar'), handle_request)
    #redis_client.fetch(('get', 'foo'), lambda x:(handle_request(x),IOLoop.instance().stop()))
    IOLoop.instance().start()

if __name__ == '__main__':
    test()

import time
import sys
import threading
import zmq
import msgpack

def setInterval(interval, max_run_count=0, call_on_init=False):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()
            def loop(): # executed in another thread
                run_count = 0
                if call_on_init:
                    function(*args, **kwargs)
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)
                    if max_run_count > 0:
                        run_count += 1
                        if run_count == max_run_count:
                            break
            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator

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
        if self.flush_interval:
            self.timed_func_handle = self.flush_timed_func()
        self.is_storing = False

    def getTimedFlushMethod(self):
        @setInterval(self.flush_interval)
        def timedFlush():
            self.flush()
        return timedFlush

    def append(self, item):
        self.put(item)

    def put(self, item):
        # Wait till a running store is finished to avoid strange race conditions when using this buffer with multiprocessing.
        while self.is_storing:
            time.sleep(.00001)
        while len(self.buffer) > self.maxsize:
            self.logger.warning("Maximum number of items (%s) in buffer reached. Waiting for flush." % self.maxsize)
            time.sleep(1)
        self.buffer.append(item)
        if self.flush_size and len(self.buffer) == self.flush_size:
            self.flush()

    def flush(self):
        if len(self.buffer) == 0 or self.is_storing:
            return
        self.is_storing = True
        if self.flush_callback(self.buffer):
            self.buffer = []
        self.is_storing = False

class BufferedQueue():
    """
    Simple class to add a buffer to a queue.

    example usage:
    queue = BufferedQueue(multiprocessing.Queue(queue_max_size), queue_buffer_size)
    """
    def __init__(self, queue, buffersize=500):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = Buffer(buffersize, self.sendBuffer, 5)

    def put(self, payload):
        self.buffer.append(payload)

    def sendBuffer(self, buffered_data):
        try:
            buffered_data = msgpack.packb(buffered_data)
            self.queue.put(buffered_data)
            return True
        except (KeyboardInterrupt, SystemExit):
            # Keyboard interrupt should be catched in main process. Ignore it here.
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not append data to queue. Exception: %s, Error: %s." % (etype, evalue))

    def get(self, block=True, timeout=None):
        try:
            buffered_data = self.queue.get(block, timeout)
            buffered_data = msgpack.unpackb(buffered_data)
            for data in buffered_data:
                yield data
        except (KeyboardInterrupt, SystemExit, ValueError, OSError):
            # Keyboard interrupt should be catched in main process. Ignore it here.
            pass
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self.logger.error("Could not read data from input queue. Exception: %s, Error: %s" % (exc_type, exc_value) )

    def qsize(self):
        return self.buffer.bufsize() + self.queue.qsize()

    def __getattr__(self, name):
        return getattr(self.queue, name)

class ZeroMqMpQueue:
    """
    Use ZeroMQ for IPC.
    This is faster than the default multiprocessing.Queue.

    send_pyobj and recv_pyobj is not used since its performance is slower than using msgpack for serialization.
    """

    def __init__(self, queue_max_size=20):
        self.queue_size = 0
        zmq_context = zmq.Context()
        self.queue_max_size = queue_max_size
        self.sender = zmq_context.socket(zmq.PUSH)
        try:
            self.sender.setsockopt(zmq.SNDHWM, queue_max_size)
        except AttributeError:
            self.sender.setsockopt(zmq.HWM, queue_max_size)
        self.selected_port = self.sender.bind_to_random_port("tcp://127.0.0.1", min_port=5200, max_port=5300, max_tries=100)
        self.receiver = None

    def put(self, data):
        self.sender.send(data)

    def get(self, block, timeout):
        if not self.receiver:
            zmq_context = zmq.Context()
            self.receiver = zmq_context.socket(zmq.PULL)
            try:
                self.receiver.setsockopt(zmq.RCVHWM, self.queue_max_size)
            except:
                self.receiver.setsockopt(zmq.HWM, self.queue_max_size)
            self.receiver.connect("tcp://127.0.0.1:%d" % self.selected_port)
        data = None
        try:
            data = self.receiver.recv()
            return data
        except zmq.error.ZMQError as e:
            # Ignore iterrupt error caused by SIGINT
            if e.strerror == "Interrupted system call":
                return data

    def qsize(self):
        return self.queue_size