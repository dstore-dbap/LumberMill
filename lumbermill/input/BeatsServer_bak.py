# -*- coding: utf-8 -*-
import pprint
import os
import sys
import ssl
import zlib
import time
import socket
import struct
import logging
from cStringIO import StringIO

from tornado import autoreload
from tornado.iostream import StreamClosedError
from tornado.netutil import bind_sockets
from tornado.tcpserver import TCPServer

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.constants import IS_PYPY
from lumbermill.BaseModule import BaseModule
from lumbermill.utils.Decorators import ModuleDocstringParser

# For pypy the default json module is the fastest.
if IS_PYPY:
    import json
else:
    json = False
    for module_name in ['ujson', 'yajl', 'simplejson', 'json']:
        try:
            json = __import__(module_name)
            break
        except ImportError:
            pass
    if not json:
        raise ImportError


class TornadoTcpServer(TCPServer):

    def __init__(self, io_loop=None, ssl_options=None, gp_module=False, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp_module = gp_module
        try:
            TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not create tcp server. Exception: %s, Error: %s." % (etype, evalue))
            self.gp_module.shutDown()

    def handle_stream(self, stream, address):
        BeatsConnectionHandler(stream, address, self.gp_module)


class BeatsConnectionHandler(object):

    code_window_size = 'W'
    code_json_frame = 'J'
    code_compressed_frame = 'C'
    code_frame = 'D'

    def __init__(self, stream, address, gp_module):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.gp_module = gp_module
        # Adding 32 to windowBits will trigger header detection.
        self.decompressor = zlib.decompressobj(zlib.MAX_WBITS | 32)
        self.states = ["READ_HEADER",
                       "READ_FRAME_TYPE",
                       "READ_WINDOW_SIZE",
                       "READ_JSON_HEADER",
                       "READ_COMPRESSED_FRAME_HEADER",
                       "READ_COMPRESSED_FRAME",
                       "READ_JSON",
                       "READ_DATA_FIELDS"]
        self.is_open = True
        self.stream = stream
        self.address = address
        self.host, self.port = self.address[0], self.address[1]
        self.stream.set_close_callback(self.onStreamClose)
        self.initBatch()
        self.readRequiredBytes()

    def onStreamClose(self):
        # Send remaining buffer if neccessary.
        if self.mode == 'stream' and self.stream._read_buffer_size > 0:
            data = ""
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

    def getCurrentState(self):
        return self.states[self.current_state]

    def readRequiredBytes(self, beats_stream=None):
        if beats_stream and beats_stream.hasEnoughBytes(self.required_bytes):
            self.decodeBeatsStream(beats_stream)
            return
        try:
            self.logger.debug("Reading %d bytes from tcp stream." % self.required_bytes)
            self.stream.read_bytes(self.required_bytes, self.convertStringToStream)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error(
                "Could not read from socket %s. Exception: %s, Error: %s." % (self.address, etype, evalue))

    def convertStringToStream(self, data):
        self.decodeBeatsStream(BeatsStream(data))

    def decodeBeatsStream(self, beats_stream):
        self.logger.debug("Current state: %s, needed bytes: %s, stream size: %s." % (self.getCurrentState(), self.required_bytes, beats_stream.size))

        # READ_HEADER.
        if self.getCurrentState() == "READ_HEADER":
            self.logger.debug("Running: READ_HEADER")
            protocol_version = beats_stream.readByte()
            if protocol_version == "2":
                self.logger.debug("Frame version 2 detected.")
                self.batch.setProtocol(2)
            else:
                self.logger.debug("Frame version 1 detected.")
                self.batch.setProtocol(1)
            self.transition(1, 1)
            self.readRequiredBytes(beats_stream)
            return

        # READ_FRAME_TYPE.
        if self.getCurrentState() == "READ_FRAME_TYPE":
            self.logger.debug("Running: READ_FRAME_TYPE")
            frame_type = beats_stream.readByte()
            self.logger.debug("FrameType: %s" % frame_type)
            if frame_type == BeatsConnectionHandler.code_window_size:
                self.transition(2, 4)
            elif frame_type == BeatsConnectionHandler.code_json_frame:
                self.transition(3, 8)
            elif frame_type == BeatsConnectionHandler.code_compressed_frame:
                self.transition(4, 4)
            elif frame_type == BeatsConnectionHandler.code_frame:
                self.transition(7, 8)
            self.readRequiredBytes(beats_stream)
            return

        # READ_WINDOW_SIZE.
        if self.getCurrentState() == "READ_WINDOW_SIZE":
            self.logger.debug("Running: READ_WINDOW_SIZE")
            window_size = beats_stream.readUnsignedInt()
            self.batch.setWindowSize(window_size)
            self.logger.debug("WindowSize: %s" % self.batch.getWindowSize())
            # Copied from https://github.com/elastic/java-lumber/blob/eb9e6c429892813d5c1b556816b456257b19bb21/src/main/java/org/logstash/beats/BeatsParser.java#L95
            # This is unlikely to happen but I have no way to known when a frame is
            # actually completely done other than checking the windows and the sequence number,
            # If the FSM read a new window and I have still
            # events buffered I should send the current batch down to the next handler.
            if not self.batch.isEmpty():
                self.logger.warn("New window size received but the current batch was not complete, sending the current batch.")
            self.transition(0, 1)
            self.readRequiredBytes(beats_stream)
            return

        # READ_DATA_FIELDS.
        if self.getCurrentState() == "READ_DATA_FIELDS":
            self.logger.debug("Running: READ_DATA_FIELDS")
            self.sequence = beats_stream.readUnsignedInt()
            fields_count = beats_stream.readUnsignedInt()
            for count in xrange(0, fields_count - 1):
                field_length = beats_stream.readUnsignedInt()
                field = beats_stream.read(field_length)
            self.readRequiredBytes(beats_stream)
            return

        # READ_COMPRESSED_FRAME_HEADER.
        if self.getCurrentState() == "READ_COMPRESSED_FRAME_HEADER":
            self.logger.debug("Running: READ_COMPRESSED_FRAME_HEADER")
            self.transition(5, beats_stream.readUnsignedInt())
            self.readRequiredBytes(beats_stream)
            return

        # READ_COMPRESSED_FRAME.
        if self.getCurrentState() == "READ_COMPRESSED_FRAME":
            self.logger.debug("Running: READ_COMPRESSED_FRAME %s" % self.required_bytes)
            compressed_data = beats_stream.read(self.required_bytes)
            decompressed_data = ""
            try:
                decompressed_data = self.decompressor.decompress(compressed_data)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not decompress data %s. Exception: %s, Error: %s." % (len(compressed_data), etype, evalue))
                return None
            self.transition(0, 1)
            self.convertStringToStream(decompressed_data)

        # READ_JSON_HEADER.
        if self.getCurrentState() == "READ_JSON_HEADER":
            self.logger.debug("Running: READ_JSON_HEADER")
            self.sequence = beats_stream.readUnsignedInt()
            self.logger.debug("Sequence: %s" % self.sequence)
            self.transition(6, beats_stream.readUnsignedInt())
            self.readRequiredBytes(beats_stream)
            return

        # READ_JSON.
        if self.getCurrentState() == "READ_JSON":
            self.logger.debug("Running: READ_JSON")
            data = beats_stream.read(self.required_bytes)
            self.batch.addMessage({"sequence": self.sequence, "data": self.decodeJsonString(data)})
            if(self.batch.size() == self.batch.getWindowSize()):
                for message in self.batch.getMessage():
                    self.gp_module.sendEvent(DictUtils.getDefaultEventDict(message, caller_class_name="BeatsServer", received_from="%s:%d" % (self.host, self.port)))
                self.initBatch()
            self.transition(0, 1)
            self.readRequiredBytes(beats_stream)
            return

    def transition(self, next, required_bytes):
        self.logger.debug("Transition, from: %s to: %s required bytes: %d." % (self.getCurrentState(), self.states[next], required_bytes))
        self.required_bytes = required_bytes
        self.current_state = next

    def initBatch(self):
        self.current_state = 0
        self.required_bytes = 1
        self.sequence = 0;
        self.batch = Batch()


    def decodeJsonString(self, json_string):
        try:
            decoded_datasets = json.loads(json_string)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not json decode event data: %s. Exception: %s, Error: %s." % (json_string, etype, evalue))
            self.logger.warning("Maybe your json string contains single quotes?")
            return None
        return decoded_datasets

class Batch:

    def __init__(self):
        self.protocol = 2
        self.window_size = 1
        self.messages = []

    def getMessage(self):
        return self.messages

    def addMessage(self, message):
        self.messages.append(message)

    def size(self):
        return len(self.messages)

    def setWindowSize(self, window_size):
        self.window_size = window_size

    def getWindowSize(self):
        return self.window_size

    def isEmpty(self):
        if len(self.messages) == 0:
            return True
        return False

    def getProtocol(self):
        return self.protocol

    def setProtocol(self, protocol):
        self.protocol = protocol


class BeatsStream:

    def __init__(self, stream_string):
        self.stream = StringIO(stream_string)
        self.stream.seek(0, os.SEEK_END)
        self.size = self.stream.tell()
        self.stream.seek(0, os.SEEK_SET)

    def hasEnoughBytes(self, num_bytes):
        print("%d + %d <= %d" % (self.stream.tell(), num_bytes, self.size))
        return self.stream.tell() + num_bytes <= self.size

    def remainingBytes(self):
        return self.size - self.stream.tell()

    def read(self, num_bytes):
        return self.stream.read(num_bytes)

    def readByte(self):
        return self.stream.read(1)

    def readUnsignedInt(self):
        return struct.unpack(">I", self.stream.read(4))[0]


@ModuleDocstringParser
class BeatsServer(BaseModule):
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
        self.server = False
        self.max_buffer_size = self.getConfigurationValue('max_buffer_size') * 10240 #* 10240
        self.start_ioloop = False
        try:
            self.sockets = bind_sockets(self.getConfigurationValue("port"), self.getConfigurationValue("interface"), backlog=128)
            for server_socket in self.sockets:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not listen on %s:%s. Exception: %s, Error: %s." % (self.getConfigurationValue("interface"),
                                                                                        self.getConfigurationValue("port"), etype, evalue))
            self.lumbermill.shutDown()
            return
        autoreload.add_reload_hook(self.shutDown)

    def getStartMessage(self):
        start_msg = "listening on %s:%s" % (self.getConfigurationValue("interface"), self.getConfigurationValue("port"))
        if self.getConfigurationValue("tls"):
            start_msg += " (with %s)" % self.getConfigurationValue("tls_proto")
        return start_msg

    def initAfterFork(self):
        BaseModule.initAfterFork(self)
        ssl_options = None
        if self.getConfigurationValue("tls"):
            ssl_options = {'ssl_version': getattr(ssl, "PROTOCOL_%s" % self.getConfigurationValue("tls_proto")),
                           'certfile': self.getConfigurationValue("cert"),
                           'keyfile': self.getConfigurationValue("key")}
        self.server = TornadoTcpServer(ssl_options=ssl_options, gp_module=self, max_buffer_size=self.max_buffer_size)
        self.server.add_sockets(self.sockets)

    def shutDown(self):
        try:
            self.server.stop()
            self.sockets.close()
            # Give os time to free the socket. Otherwise a reload will fail with 'address already in use'
            time.sleep(.2)
        except AttributeError:
            pass
