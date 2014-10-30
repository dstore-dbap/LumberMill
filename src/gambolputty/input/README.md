input modules
==========
#####FileQueue

Stores all received events in a file based queue for persistance.

path: Path to queue file.
store_interval_in_secs: sending data to es in x seconds intervals.
batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.

Configuration template:

    - FileQueueSink:
        path:                           # <type: string; is: required>
        store_interval_in_secs:         # <default: 10; type: integer; is: optional>
        batch_size:                     # <default: 500; type: integer; is: optional>
        receivers:
          - NextModule


#####NmapScanner

Scan network with nmap and emit result as new event.

Configuration template:

    - NmapScanner:
        network:                    # <type: string; is: required>
        netmask:                    # <default: '/24'; type: string; is: optional>
        ports:                      # <default: None; type: None||string; is: optional>
        arguments:                  # <default: '-O -F --osscan-limit'; type: string; is: optional>
        interval:                   # <default: 900; type: integer; is: optional>
        receivers:
          - NextModule


#####RedisChannel

Subscribes to a redis channels and passes incoming events to receivers.

channel: Name of redis channel to subscribe to.
server: Redis server to connect to.
port: Port redis server is listening on.
db: Redis db.
password: Redis password.

Configuration template:

    - RedisChannel:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule


#####RedisList

Subscribes to a redis channels/lists and passes incoming events to receivers.

lists: Name of redis lists to subscribe to.
server: Redis server to connect to.
port: Port redis server is listening on.
db: Redis db.
password: Redis password.
timeout: Timeout in seconds.

Configuration template:

    - RedisList:
        lists:                    # <type: list; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        timeout:                  # <default: 0; type: integer; is: optional>
        receivers:
          - NextModule


#####ScapyNetSniffer

Sniff network traffic. Needs root privileges.

interface: Sets interface to listen on. Default is to listen on all interfaces.
packetfilter: Sets a filter for incoming traffic. Berkley packet filter is used, e.g.: 'tcp and port 80' (@see tcpdump).
promiscous: Sets interface to promiscous mode. Needs root privileges.

Configuration template:

    - TcpSniffer:
        interface:          # <type: None||string; default: None; is: optional>
        packetfilter:       # <type: None||string; default: None; is: optional>
        promiscous:         # <type: boolean; default: False; is: optional>
        receivers:
          - NextModule


#####Sniffer

Sniff network traffic. Needs root privileges.

Reason for using pcapy as sniffer lib:
As Gambolputty is intended to be run with pypy, every module should be compatible with pypy.
Creating a raw socket in pypy is no problem but it is (up to now) not possible to bind this
socket to a selected interface, e.g. socket.bind(('lo', 0)) will throw "error: unknown address family".
With pcapy this problem does not exist.

Dependencies:
- pcapy: pypy -m pip install pcapy

Configuration template:

    - TcpSniffer:
        interface:              # <default: 'any'; type: None||string; is: optional>
        packetfilter:           # <default: None; type: None||string; is: optional>
        promiscous:             # <default: False; type: boolean; is: optional>
        key_value_store:        # <default: None; type: none||string; is: optional>
        receivers:
          - NextModule


#####Spam

Emits events as fast as possible.

Use this module to load test GambolPutty.

event: Send custom event data.
sleep: Time to wait between sending events.
events_count: Only send configured number of events. 0 means no limit.

Configuration template:

    - Spam:
        event:                    # <default: {}; type: dict; is: optional>
        sleep:                    # <default: 0; type: int||float; is: optional>
        events_count:             # <default: 0; type: int; is: optional>
        receivers:
          - NextModule


#####StdInHandler

Reads data from stdin and sends it to its output queues.

Configuration template:

    - StdInHandler:
        multiline:                     # <default: False; type: boolean; is: optional>
        stream_end_signal:             # <default: False; type: boolean||string; is: optional>
        receivers:
          - NextModule


#####TornadoTcpServer

Reads data from tcp socket and sends it to its output queues.
Should be the best choice perfomancewise if you are on Linux.

interface:  Ipaddress to listen on.
port:       Port to listen on.
timeout:    Sockettimeout in seconds.
tls:        Use tls or not.
key:        Path to tls key file.
cert:       Path to tls cert file.
mode:       Receive mode, line or stream.
simple_separator:  If mode is line, set separator between lines.
regex_separator:   If mode is line, set separator between lines. Here regex can be used.
chunksize:  If mode is stream, set chunksize in bytes to read from stream.
max_buffer_size: Max kilobytes to in receiving buffer.

Configuration template:

    - TcpServerTornado:
        interface:                       # <default: ''; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
        mode:                            # <default: 'line'; type: string; values: ['line', 'stream']; is: optional>
        simple_separator:                # <default: '\n'; type: string; is: optional>
        regex_separator:                 # <default: None; type: None||string; is: optional>
        chunksize:                       # <default: 16384; type: integer; is: optional>
        max_buffer_size:                 # <default: 10240; type: integer; is: optional>
        receivers:
          - NextModule


#####ThreadPoolMixIn

Use a thread pool instead of a new thread on every request.

Using a threadpool prevents the spawning of a new thread for each incoming
request. This should increase performance a bit.

See: http://code.activestate.com/recipes/574454/
"""
numThreads = 15
allow_reuse_address = True  # seems to fix socket.error on server restart
alive = True

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
while self.alive:
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
event = Utils.getDefaultEventDict({"received_from": "%s" % host, "data": data}, caller_class_name='TcpServerThreaded')
self.tcp_server_instance.sendEvent(event)
except socket.error, e:
self.logger.warning("%sError occurred while reading from socket. Error: %s%s" % (Utils.AnsiColors.WARNING, e, Utils.AnsiColors.ENDC))
except socket.timeout, e:
self.logger.warning("%sTimeout occurred while reading from socket. Error: %s%s" % (Utils.AnsiColors.WARNING, e, Utils.AnsiColors.ENDC))

class ThreadedTCPServer(ThreadPoolMixIn, SocketServer.TCPServer):

allow_reuse_address = True

def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, timeout=None, tls=False, key=False, cert=False, ssl_ver = ssl.PROTOCOL_SSLv23):
SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
self.socket.settimeout(timeout)
self.use_tls = tls
self.timeout = timeout
if tls:
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

Configuration template:

    - TcpServerThreaded:
        interface:                       # <default: ''; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
        receivers:
          - NextModule


#####TornadoTcpServer

Reads data from tcp socket and sends it to its output queues.
Should be the best choice perfomancewise if you are on Linux.

interface:  Ipaddress to listen on.
port:       Port to listen on.
timeout:    Sockettimeout in seconds.
tls:        Use tls or not.
key:        Path to tls key file.
cert:       Path to tls cert file.
mode:       Receive mode, line or stream.
simple_separator:  If mode is line, set separator between lines.
regex_separator:   If mode is line, set separator between lines. Here regex can be used.
chunksize:  If mode is stream, set chunksize in bytes to read from stream.
max_buffer_size: Max kilobytes to in receiving buffer.

Configuration template:

    - TcpServerTornado:
        interface:                       # <default: ''; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
        mode:                            # <default: 'line'; type: string; values: ['line', 'stream']; is: optional>
        simple_separator:                # <default: '\n'; type: string; is: optional>
        regex_separator:                 # <default: None; type: None||string; is: optional>
        chunksize:                       # <default: 16384; type: integer; is: optional>
        max_buffer_size:                 # <default: 10240; type: integer; is: optional>
        receivers:
          - NextModule


#####ThreadPoolMixIn

Use a thread pool instead of a new thread on every request.

Using a threadpool prevents the spawning of a new thread for each incoming
request. This should increase performance a bit.

See: http://code.activestate.com/recipes/574454/
"""
numThreads = 15
allow_reuse_address = True  # seems to fix socket.error on server restart
alive = True

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
while self.alive:
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


class ThreadedUdpRequestHandler(SocketServer.BaseRequestHandler):

def __init__(self, udp_server_instance, *args, **keys):
self.udp_server_instance = udp_server_instance
self.logger = logging.getLogger(self.__class__.__name__)
SocketServer.BaseRequestHandler.__init__(self, *args, **keys)

def handle(self):
try:
data = self.request[0].strip()
if data == "":
return
host = self.client_address[0]
port = self.client_address[1]
event = Utils.getDefaultEventDict({"data": data}, received_from="%s:%s" % (host, port),caller_class_name='UdpServer')
self.udp_server_instance.sendEvent(event)
except socket.error, e:
self.logger.warning("%sError occurred while reading from socket. Error: %s%s" % (Utils.AnsiColors.WARNING, e, Utils.AnsiColors.ENDC))
except socket.timeout, e:
self.logger.warning("%sTimeout occurred while reading from socket. Error: %s%s" % (Utils.AnsiColors.WARNING, e, Utils.AnsiColors.ENDC))

class ThreadedUdpServer(ThreadPoolMixIn, SocketServer.UDPServer):

allow_reuse_address = True

def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, timeout=None, tls=False, key=False, cert=False, ssl_ver = ssl.PROTOCOL_SSLv23):
SocketServer.UDPServer.__init__(self, server_address, RequestHandlerClass)
self.socket.settimeout(timeout)
self.use_tls = tls
self.timeout = timeout
if tls:
self.socket = ssl.wrap_socket(self.socket,
server_side=True,
keyfile=key,
certfile=cert,
cert_reqs=ssl.CERT_NONE,
ssl_version=ssl_ver,
do_handshake_on_connect=False,
suppress_ragged_eofs=True)

def get_request(self):
(socket, addr) = SocketServer.UDPServer.get_request(self)
if self.use_tls:
socket.settimeout(self.timeout)
socket.do_handshake()
return (socket, addr)

class UdpRequestHandlerFactory:
def produce(self, tcp_server_instance):
def createHandler(*args, **keys):
return ThreadedUdpRequestHandler(tcp_server_instance, *args, **keys)
return createHandler

@ModuleDocstringParser
class UdpServer(BaseModule.BaseModule):
"""
Reads data from tcp socket and sends it to its output queues.
This incarnation of a TCP Server is (at least on Linux) not as fast as the TcpServerTornado.

Configuration template:

    - TcpServerThreaded:
        interface:                       # <default: ''; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
        receivers:
          - NextModule


#####SocketServer

Reads data from an unix socket and sends it to its output queues.

Configuration template:

    - UnixSocket:
        path_to_socket:         # <type: string; is: required>
        receivers:
          - NextModule


#####Zmq

Read events from a zeromq.

server: Server to poll. Pattern: hostname:port.
pattern: Either pull or sub.
mode: Whether to run a server or client.
hwm: Highwatermark for receiving socket.

Configuration template:

    - Zmq:
        server:                     # <default: 'localhost:5570'; type: string; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        hwm:                        # <default: None; type: None||integer; is: optional>
        receivers:
          - NextModule


#####ZmqTornado

Read events from a zeromq.

servers: Servers to poll. Pattern: hostname:port.
pattern: Either pull or sub.
mode: Whether to run a server or client.
separator: When using the sub pattern, messages can have a topic. Set separator to split message from topic.

Configuration template:

    - Zmq:
        servers:                    # <default: ['localhost:5570']; type: list; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        separator:                  # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule