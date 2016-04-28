.. _Webserver:

Webserver modules
=================

WebGui
------

A WebGui plugin for LumberMill. At the moment this is just a stub.

Module dependencies:    WebserverTornado

Configuration template:

::

    tornado_webserver: Name of the webserver module.
    document_root: Path to look for templates and static files.

    - WebGui:
       tornado_webserver: webserver     # <default: 'WebserverTornado'; type: string; is: optional>
       document_root: other_root        # <default: 'docroot'; type: string; is: optional>


WebserverTornado
----------------

A tornado based web server.

Configuration template:

::

    - WebserverTornado:
       port:                            # <default: 5100; type: integer; is: optional>
       tls:                             # <default: False; type: boolean; is: optional>
       key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
       cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
       document_root:                   # <default: '../assets/webserver_docroot'; type: string; is: optional>
       application_settings:            # <default: None; type: None||dict; is: optional>