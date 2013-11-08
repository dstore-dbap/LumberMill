Input modules
==========

#####TcpServerThreaded

Reads data from tcp socket and sends it to its output queues.

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