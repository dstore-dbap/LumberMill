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

Configuration example:

    - module: TcpServerTornado
      interface:                       # <default: ''; type: string; is: optional>
      port:                            # <default: 5151; type: integer; is: optional>
      timeout:                         # <default: None; type: None||integer; is: optional>
      tls:                             # <default: False; type: boolean; is: optional>
      key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
      cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
      mode:                            # <default: 'line'; type: string; values: ['line', 'stream']; is: optional>
      seperator:                       # <default: '\n'; type: string; is: optional>
      chunksize:                       # <default: 16384; type: integer; is: optional>
      receivers:
        - NextModule


#####TcpServerThreaded

Reads data from tcp socket and sends it to its output queues.
This incarnation of a TCP Server is (at least on Linux) not as fast as the TcpServerTornado.

Configuration example:

    - module: TcpServerThreaded
      interface: localhost             # <default: 'localhost'; type: string; is: optional>
      port: 5151                       # <default: 5151; type: integer; is: optional>
      timeout: 5                       # <default: None; type: None||integer; is: optional>
      tls: False                       # <default: False; type: boolean; is: optional>
      key: /path/to/cert.key           # <default: False; type: boolean||string; is: required if tls is True else optional>
      cert: /path/to/cert.crt          # <default: False; type: boolean||string; is: required if tls is True else optional>
      receivers:
        - NextModule

#####StdInHandler

Reads data from stdin and sends it to its output queues.

Configuration example:

    - module: StdInHandler
      multiline: True                  # <default: False; type: boolean; is: optional>
      stream_end_signal: #########     # <default: False; type: string; is: optional>
      receivers:
        - NextModuleName

#####UnixSocket

Reads data from an unix socket and sends it to its output queues.

Configuration example:

    - module: UnixSocket
      path_to_socket: /tmp/test.sock   # <type: string; is: required>
      receivers:
        - NextModule

#####RedisChannel

Subscribes to a redis channels and passes incoming events to receivers.

Configuration example:

    - module: RedisChannel
      channel: my_channel         # <type: string; is: required>
      server: redis.server        # <default: 'localhost'; type: string; is: optional>
      port: 6379                  # <default: 6379; type: integer; is: optional>
      db: 0                       # <default: 0; type: integer; is: optional>
      password: None              # <default: None; type: None||string; is: optional>

#####RedisList

Subscribes to redis lists and passes incoming events to receivers.

Configuration example:

    - module: RedisList
      lists: ['my_list']          # <type: list; is: required>
      server: redis.server        # <default: 'localhost'; type: string; is: optional>
      port: 6379                  # <default: 6379; type: integer; is: optional>
      db: 0                       # <default: 0; type: integer; is: optional>
      password: None              # <default: None; type: None||string; is: optional>
      timeout: 10                 # <default: 0; type: integer; is: optional>

#####Zmq

Read events from a zeromq.

servers: Servers to poll. Pattern: hostname:port.
pattern: Either pull or subscribe.
mode: Wether to run a server or client.
multipart: When using the sub pattern, messages can have a topic. If send via multipart set this to true.
seperator: When using the sub pattern, messages can have a topic. Set seperator to split message from topic.

Configuration example:

- module: Zmq
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

Configuration example:

    - module: Spam
      event: {'Lobster': 'Thermidor', 'Truffle': 'Pate'}  # <default: {}; type: dict; is: optional>
      sleep: 0                                            # <default: 0; type: int||float; is: optional>
      events_count: 1000                                  # <default: 0; type: int; is: optional>
      receivers:
        - NextModule