Input modules
==========

#####TcpServerThreaded

Reads data from tcp socket and sends it to its output queues.

    Configuration example:

    - module: TcpServerThreaded
      configuration:
        interface: localhost             # <default: 'localhost'; type: string; is: optional>
        port: 5151                       # <default: 5151; type: integer; is: optional>
        tls: False                       # <default: False; type: boolean; is: optional>
        cert: /path/to/cert.pem          # <default: False; type: boolean||string; is: optional>
      receivers:
        - NextModuleName

#####StdInHandler

Reads data from stdin and sends it to its output queues.

    Configuration example:

    - module: StdInHandler
      configuration:
        multiline: True                  # <default: False; type: boolean; is: optional>
        stream-end-signal: #########     # <default: False; type: string; is: optional>
      receivers:
        - NextModuleName