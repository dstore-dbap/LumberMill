Webserver modules
==========

#####WebserverTornado

A tornado based web server.

port: Port to listen on.
document_root: Location of documents and templates.

Configuration example:

    - WebserverTornado:
        port: 6060                 # <default: 5100; type: integer; is: optional>
        document_root: other_root  # <default: 'docroot'; type: string; is: optional>

WebserverTornado submodules
==========
#####WebGui

A WebGui plugin for GambolPutty. At the moment this is just a stub.

Module dependencies:    WebserverTornado

Configuration example:

    - WebGui:
        tornado_webserver: webserver          # <default: 'WebserverTornado'; type: string; is: optional>
        document_root: other_root             # <default: 'docroot'; type: string; is: optional>