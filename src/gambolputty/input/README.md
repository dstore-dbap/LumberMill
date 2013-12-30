Input modules
==========
#####TcpServerTornado

Reads data from tcp socket and sends it to its output queues.
Should be the best choice perfomancewise if you are on Linux.

    Configuration example:

    - module: TcpServerTornado
      configuration:
        interface: localhost             # <default: 'localhost'; type: string; is: optional>
        port: 5151                       # <default: 5151; type: integer; is: optional>
        timeout: 5                       # <default: None; type: None||integer; is: optional>
        tls: False                       # <default: False; type: boolean; is: optional>
        key: /path/to/cert.key           # <default: False; type: boolean||string; is: required if tls is True else optional>
        cert: /path/to/cert.crt          # <default: False; type: boolean||string; is: required if tls is True else optional>
      receivers:
        - NextModule
    """


#####TcpServerThreaded

Reads data from tcp socket and sends it to its output queues.
This incarnation of a TCP Server is (at least on Linux) not as fast as the TcpServerTornado.

Configuration example:

    - module: TcpServerThreaded
      configuration:
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
      configuration:
        multiline: True                  # <default: False; type: boolean; is: optional>
        stream_end_signal: #########     # <default: False; type: string; is: optional>
      receivers:
        - NextModuleName

#####UnixSocket

Reads data from an unix socket and sends it to its output queues.

Configuration example:

    - module: UnixSocket
      configuration:
        path_to_socket: /tmp/test.sock   # <type: string; is: required>
      receivers:
        - NextModule

#####RedisChannel

Subscribes to a redis channel and passes incoming events to receivers.

Configuration example:

    - module: RedisChannel
      configuration:
        channels:                   # <type: string; is: required>
        server: redis.server        # <default: 'localhost'; type: string; is: optional>
        port: 6379                  # <default: 6379; type: integer; is: optional>
        db: 0                       # <default: 0; type: integer; is: optional>
        password: None              # <default: None; type: None||string; is: optional>
        socket_timeout: 10          # <default: 10; type: integer; is: optional>

#####Spam

Emits events as fast as possible.

Use this module to load test GambolPutty.

event: Send custom event data.
sleep: Time to wait between sending events.
events_count: Only send configured number of events. 0 means no limit.

Configuration example:

    - module: Spam
      configuration:
        event: {'Lobster': 'Thermidor', 'Truffle': 'Pate'}  # <default: {}; type: dict; is: optional>
        sleep: 0                                            # <default: 0; type: int||float; is: optional>
        events_count: 1000                                  # <default: 0; type: int; is: optional>
      receivers:
        - NextModule