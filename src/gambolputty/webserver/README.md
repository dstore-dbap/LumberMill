Parser modules
==========

#####WebserverTornado

A tornado based web server.

Configuration example:

    - module: WebserverTornado
      port: 6060                 # <default: 5100; type: integer; is: optional>
      document_root: other_root  # <default: 'docroot'; type: string; is: optional>

#####WebGui

A WebGui plugin for GambolPutty. At the moment this is just a stub.

Module dependencies:    WebserverTornado

Configuration example:

    - module: WebGui
      tornado_webserver: webserver          # <default: 'WebserverTornado'; type: string; is: optional>
      document_root: other_root             # <default: 'docroot'; type: string; is: optional>