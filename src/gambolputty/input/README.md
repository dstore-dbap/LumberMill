input modules
==========
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


#####TcpServerMultipleWorker

Reads data from tcp socket and sends it to its outputs.
Should be the best choice perfomancewise if you are on Linux and are running with multiple workers.

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


#####TcpServerSingleWorker

Reads data from tcp socket and sends it to its output queues.
Should be the best choice perfomancewise if you are on Linux and are running with only one worker.
If running with multiple workers, consider using

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
parser:     Parser for received data.

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
        parsers:                         # <default: None; type: None||list; is: optional>
        receivers:
          - NextModule


#####TcpServerThreaded

Reads data from tcp socket and sends it to its output queues.
This incarnation of a TCP Server is (at least on Linux) not as fast as the TcpServerSingleWorker or TcpServerMultipleWorker.

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


#####UdpServer

Reads data from udp socket and sends it to its output queues.

Configuration template:

    - UdpServer:
        interface:                       # <default: ''; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
        receivers:
          - NextModule


#####UnixSocket

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