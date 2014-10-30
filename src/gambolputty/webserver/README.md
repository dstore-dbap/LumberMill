webserver modules
==========
#####WebGui

A WebGui plugin for GambolPutty. At the moment this is just a stub.

Module dependencies:    WebserverTornado

Configuration template:

    tornado_webserver: Name of the webserver module.
    document_root: Path to look for templates and static files.

    - WebGui:
        tornado_webserver: webserver          # <default: 'WebserverTornado'; type: string; is: optional>
        document_root: other_root             # <default: 'docroot'; type: string; is: optional>


#####WebserverTornado

A tornado based web server.

Configuration template:

    - WebserverTornado:
        port: 6060                 # <default: 5100; type: integer; is: optional>
        document_root: other_root  # <default: 'docroot'; type: string; is: optional>