Cluster modules
==========
#####Cluster

Cluster base module. Handles pack leader discovery and alive checks of pack followers.

IMPORTANT:
This is just a first alpha implementation. No leader election, no fail over, no sanity checks for conflicting leaders.

interface:  Ipaddress to listen on.
port:   Port to listen on.
broadcast: Ipaddress for udp broadcasts.
interval: Autodiscover interval.
tornado_webserver: Name of the webserver module. Needed for leader - pack communication.
pack: Set this node to be either leader or member.
name: Name of the cluster. Used for auto-discovery in same network.
shared_secret: pre shared key to en/decrypt cluster messages.

    - Cluster:
        interface:                            # <default: '0.0.0.0'; type: string; is: optional>
        port:                                 # <default: 5252; type: integer; is: optional>
        broadcast:                            # <type: string; is: required>
        interval:                             # <default: 10; type: integer; is: optional>
        pack:                                 # <default: 'leader'; type: string; values: ['leader', 'follower']; is: optional>
        name:                                 # <type: string; is: required>
        secret:                               # <type: string; is: required>

Cluster submodules
==========
#####ClusterConfiguration

Synchronize configuration from leader to pack members.
Any changes to the leaders configuration will be synced to all pack followers.

Locally configured modules of pack members will not be overwritten by the leaders configuration.

Module dependencies: ['Cluster']

cluster: Name of the cluster module.
ignore_modules: List of module names to exclude from sync process.
interval: Time in seconds between checks if master config did change.

Configuration template:

    - ClusterConfiguration:
        cluster:                                # <default: 'Cluster'; type: string; is: optional>
        ignore_modules: [WebGui,LocalModule]    # <default: []; type: list; is: optional>
        interval: 10                            # <default: 60; type: integer; is: optional>