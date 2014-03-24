Input modules
==========
#####TcpServerTornado

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

Configuration template:

    - TcpServerTornado:
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


#####TcpServerThreaded

Reads data from tcp socket and sends it to its output queues.
This incarnation of a TCP Server is (at least on Linux) not as fast as the TcpServerTornado.

Configuration template:

    - TcpServerThreaded:
        interface:                       # <default: 'localhost'; type: string; is: optional>
        port:                            # <default: 5151; type: integer; is: optional>
        timeout:                         # <default: None; type: None||integer; is: optional>
        tls:                             # <default: False; type: boolean; is: optional>
        key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
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

#####UnixSocket

Reads data from an unix socket and sends it to its output queues.

Configuration template:

    - UnixSocket:
        path_to_socket:         # <type: string; is: required>
        receivers:
          - NextModule

#####RedisChannel

Subscribes to a redis channels and passes incoming events to receivers.

Configuration template:

    - RedisChannel:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>

#####RedisList

Subscribes to redis lists and passes incoming events to receivers.

Configuration template:

    - RedisList:
        lists:                    # <type: list; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        timeout:                  # <default: 0; type: integer; is: optional>

#####Zmq

Read events from a zeromq.

servers: Servers to poll. Pattern: hostname:port.
pattern: Either pull or subscribe.
mode: Wether to run a server or client.
multipart: When using the sub pattern, messages can have a topic. If send via multipart set this to true.
seperator: When using the sub pattern, messages can have a topic. Set seperator to split message from topic.

Configuration template:

    - Zmq:
        servers:                    # <default: ['localhost:5570']; type: list; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        mode:                       # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        multipart:                  # <default: False; type: boolean; is: optional>
        seperator:                  # <default: None; type: None||string; is: optional>

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