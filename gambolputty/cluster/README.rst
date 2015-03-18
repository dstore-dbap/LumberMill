.. _Cluster:

Cluster modules
===============

Pack
----

Pack base module. Handles pack leader discovery and alive checks of pack followers.

IMPORTANT:
This is just a first alpha implementation. No leader election, no failover, no sanity checks for conflicting leaders.

| **name**:  Name of the cluster. Used for auto-discovery in same network.
| **secret**:  pre shared key to en/decrypt cluster messages.
| **broadcast**:  Ipaddress for udp broadcasts.
| **interface**:   Ipaddress to listen on.
| **port**:    Port to listen on.
| **interval**:  Autodiscover interval.
| **pack**:  Set this node to be either leader or member.

Configuration template:

::

    - Pack:
        name:                                 # <type: string; is: required>
        secret:                               # <type: string; is: required>
        broadcast:                            # <type: string; is: required>
        interface:                            # <default: '0.0.0.0'; type: string; is: optional>
        port:                                 # <default: 5252; type: integer; is: optional>
        interval:                             # <default: 10; type: integer; is: optional>
        pack:                                 # <default: 'leader'; type: string; values: ['leader', 'follower']; is: optional>


PackConfiguration
-----------------

Synchronize configuration from leader to pack members.
Any changes to the leaders configuration will be synced to all pack followers.

Locally configured modules of pack members will not be overwritten by the leaders configuration.

Module dependencies: ['Pack']

| **pack**:  Name of the pack module. Defaults to the standard Pack module.
| **ignore_modules**:  List of module names to exclude from sync process.
| **interval**:  Time in seconds between checks if master config did change.

Configuration template:

::

    - PackConfiguration:
        pack:                                   # <default: 'Pack'; type: string; is: optional>
        ignore_modules: [WebGui,LocalModule]    # <default: []; type: list; is: optional>
        interval: 10                            # <default: 60; type: integer; is: optional>