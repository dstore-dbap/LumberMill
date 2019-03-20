# -*- coding: utf-8 -*-
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
from tornado.tcpclient import TCPClient
from tornado import gen

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


class TornadoTcpClient(TCPClient):

    def __init__(self, ssl_options=None, gp_module=False, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp_module = gp_module
        try:
            TCPClient.__init__(self, ssl_options=ssl_options, **kwargs)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not create tcp client. Exception: %s, Error: %s." % (etype, evalue))
            self.gp_module.shutDown()

    @gen.coroutine
    def handle_stream(self, stream, address):
        handler = BeatsConnectionHandler(stream, address, self.gp_module)
        yield handler.handleStream()


class BeatsConnectionHandler(object):

    code_window_size_frame = 'W'
    code_json_frame = 'J'
    code_compressed_frame = 'C'
    code_frame = 'D'

    def __init__(self, stream, address, gp_module):
        self.logger = logging.getLogger(self.__class__.__name__)
        #self.logger.setLevel(logging.DEBUG)
        self.gp_module = gp_module
        self.states = ["DECODE_HEADER",
                       "DECODE_FRAME_TYPE",
                       "DECODE_WINDOW_SIZE",
                       "DECODE_JSON_HEADER",
                       "DECODE_COMPRESSED_FRAME_HEADER",
                       "DECODE_COMPRESSED_FRAME",
                       "DECODE_JSON",
                       "DECODE_DATA_FIELDS"]
        self.state_decoder = [self.decodeHeader,
                              self.decodeFrameType,
                              self.decodeWindowSize,
                              self.decodeJsonHeader,
                              self.decodeCompressedFrameHeader,
                              self.decodeCompressedFrame,
                              self.decodeJson,
                              self.decodeDataFields]
        self.is_open = True
        self.tcp_stream = stream
        self.address = address
        self.host, self.port = self.address[0], self.address[1]
        self.tcp_stream.set_close_callback(self.onStreamClose)
        self.initBatch()

    def initBatch(self):
        self.stringio_stream = None
        self.stringio_size = 0
        self.current_state = 0
        self.required_bytes = 1
        self.sequence_number = 0
        self.batch = Batch()

    def onStreamClose(self):
        # Send remaining buffer if neccessary.
        data = ""
        if self.tcp_stream._read_buffer_size > 0:
            data = ""
            while True:
                try:
                    data += self.tcp_stream._read_buffer.popleft().strip()
                except IndexError:
                    break
                except AttributeError:
                    print(self.tcp_stream._read_buffer)
                    sys.exit()
        if data != "":
            if not self.stringio_stream:
                self.stringio_stream = StringIO()
            self.stringio_size += len(data)
            self.stringio_stream.write(data)
            self.readRequiredBytes()
        self.tcp_stream.close()

    def sendBatch(self):
        for message in self.batch.getMessage():
            self.gp_module.sendEvent(DictUtils.getDefaultEventDict(message, caller_class_name="BeatsServer", received_from="%s:%d" % (self.host, self.port)))
        self.sendAck()
        self.initBatch()

    def sendAck(self):
        self.logger.debug("Sending ack for seq: %s. %sA%s" % (self.sequence_number, self.batch.getProtocol(), struct.pack(">I", self.sequence_number)))
        self.tcp_stream.write("%sA%s" % (self.batch.getProtocol(), struct.pack(">I", self.sequence_number)))

    def transition(self, next, required_bytes):
        self.logger.debug("Transition, from: %s to: %s required bytes: %d." % (self.getCurrentState(), self.states[next], required_bytes))
        self.required_bytes = required_bytes
        self.current_state = next

    def getCurrentState(self):
        return self.states[self.current_state]

    @gen.coroutine
    def handleStream(self):
        """
        decodeCompressedFrame produces a StringIO object, containing the uncompressed data stream.
        So if self.stringio_stream exists, read from this stream instead of the tcp stream.
        When all data from self.stringio_stream has been read, discard it and continue to read from tcp stream.
        :return:
        """
        while True:
            try:
                if self.stringio_stream:
                    self.logger.debug("Reading %d byte(s) from stringio stream." % self.required_bytes)
                    stream_data = self.stringio_stream.read(self.required_bytes)
                    self.stringio_size -= self.required_bytes
                    if self.stringio_size <= 0:
                        self.stringio_stream = None
                        self.stringio_size = 0
                else:
                    self.logger.debug("Reading %d byte(s) from tcp stream." % self.required_bytes)
                    stream_data = yield self.tcp_stream.read_bytes(self.required_bytes)
                # Empty stream data signals an error in stream. Reset to scan for next frame header.
                if not stream_data:
                    self.logger.warning("Got empty stream data. Falling back to decoding next header.")
                    self.sendBatch()
                    self.transition(0, 1)
                self.state_decoder[self.current_state](stream_data)
            except StreamClosedError:
                break

    def decodeHeader(self, stream_data):
        self.logger.debug("decodeHeader, requiredBytes: %s" % self.required_bytes)
        if stream_data == "2":
            self.logger.debug("Frame version 2 detected.")
            self.batch.setProtocol(2)
        elif stream_data == "1":
            self.logger.debug("Frame version 1 detected.")
            self.batch.setProtocol(1)
        else:
            self.logger.warning("Unknown header: %s (Hex: %s). Skipping." % (stream_data, "{:02x}".format(ord(stream_data))))
            self.sendBatch()
            self.transition(0, 1)
            return
        self.transition(1, 1)

    def decodeFrameType(self, stream_data):
        self.logger.debug("decodeFrameType, requiredBytes: %s" % self.required_bytes)
        self.logger.debug("FrameType: %s" % stream_data)
        if stream_data == BeatsConnectionHandler.code_window_size_frame:
            self.transition(2, 4)
        elif stream_data == BeatsConnectionHandler.code_json_frame:
            self.transition(3, 8)
        elif stream_data == BeatsConnectionHandler.code_compressed_frame:
            self.transition(4, 4)
        elif stream_data == BeatsConnectionHandler.code_frame:
            self.transition(7, 8)
        else:
            self.logger.warning("Unknown frame type: %s (Hex: %s). Falling back to decoding next header." % (stream_data, "{:02x}".format(ord(stream_data))))
            self.sendBatch()
            self.transition(0, 1)

    def decodeWindowSize(self, stream_data):
        self.logger.debug("decodeWindowSize, requiredBytes: %s" % self.required_bytes)
        window_size = struct.unpack(">I", stream_data)[0]
        self.batch.setWindowSize(window_size)
        self.logger.debug("WindowSize: %s" % self.batch.getWindowSize())
        # Copied from https://github.com/elastic/java-lumber/blob/eb9e6c429892813d5c1b556816b456257b19bb21/src/main/java/org/logstash/beats/BeatsParser.java#L95
        # This is unlikely to happen but I have no way to known when a frame is
        # actually completely done other than checking the windows and the sequence number,
        # If the FSM read a new window and I have still
        # events buffered I should send the current batch down to the next handler.
        if not self.batch.isEmpty() and not self.stringio_stream:
            self.logger.warn("New window size received but the current batch was not complete, sending the current batch.")
            self.sendBatch()
        self.transition(0, 1)

    def decodeDataFields(self, stream_data):
        """
        TODO: Not yet implemented.
        :param stream_data:
        :return:
        """
        self.logger.debug("decodeDataFields, requiredBytes: %s" % self.required_bytes)
        self.sequence_number = struct.unpack(">I", stream_data[:4])[0]
        fields_count = struct.unpack(">I", stream_data[4:])[0]
        for count in xrange(0, fields_count - 1):
            field_length = stream_data.readUnsignedInt()
            field = stream_data.read(field_length)

    def decodeCompressedFrameHeader(self, stream_data):
        self.logger.debug("decodeCompressedFrameHeader, requiredBytes: %s" % self.required_bytes)
        self.transition(5, struct.unpack(">I", stream_data)[0])

    def decodeCompressedFrame(self, stream_data):
        self.logger.debug("decodeCompressedFrame, requiredBytes: %s" % self.required_bytes)
        decompressed_data = ""
        try:
            decompressed_data = zlib.decompress(stream_data)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not decompress data %s. Exception: %s, Error: %s. Falling back to decoding header." % (len(stream_data), etype, evalue))
            self.transition(0, 1)
            return None
        self.stringio_size = len(decompressed_data)
        self.stringio_stream = StringIO(decompressed_data)
        self.transition(0, 1)

    def decodeJsonHeader(self, stream_data):
        self.logger.debug("decodeJsonHeader, requiredBytes: %s" % self.required_bytes)
        self.sequence_number = struct.unpack(">I", stream_data[:4])[0]
        self.logger.debug("Sequence: %s" % self.sequence_number)
        self.transition(6, struct.unpack(">I", stream_data[4:])[0])

    def decodeJson(self, stream_data):
        self.logger.debug("decodeJson, requiredBytes: %s" % self.required_bytes)
        self.batch.addMessage({"sequence": self.sequence_number, "data": self.decodeJsonString(stream_data)})
        if self.batch.size() == self.batch.getWindowSize():
            self.sendBatch()
        self.transition(0, 1)

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
        print("%d + %d <= %d" % (self.tcp_stream.tell(), num_bytes, self.size))
        return self.tcp_stream.tell() + num_bytes <= self.size

    def remainingBytes(self):
        return self.size - self.tcp_stream.tell()

    def read(self, num_bytes):
        return self.tcp_stream.read(num_bytes)



@ModuleDocstringParser
class BeatsServer(BaseModule):
    r"""
    Reads data from elastic beats client, i.e. filebeats, and sends it to its outputs.

    interface:  Ipaddress to listen on.
    port:       Port to listen on.
    timeout:    Sockettimeout in seconds.
    tls:        Use tls or not.
    key:        Path to tls key file.
    cert:       Path to tls cert file.
    cacert:     Path to ca cert file.
    tls_proto:  Set TLS protocol version.
    max_buffer_size: Max kilobytes to in receiving buffer.

    Configuration template:

    - BeatsServer:
       interface:                       # <default: ''; type: string; is: optional>
       port:                            # <default: 5151; type: integer; is: optional>
       timeout:                         # <default: None; type: None||integer; is: optional>
       tls:                             # <default: False; type: boolean; is: optional>
       key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
       cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
       cacert:                          # <default: False; type: boolean||string; is: optional>
       tls_proto:                       # <default: 'TLSv1'; type: string; values: ['TLSv1', 'TLSv1_1', 'TLSv1_2']; is: optional>
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
