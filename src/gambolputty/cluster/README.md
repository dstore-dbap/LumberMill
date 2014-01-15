Cluster modules
==========
#####Cluster

Container module for all cluster related plugins.

Configuration example:

    - module: Cluster
      master: master.gp.server   # <default: None; type: None||string; is: optional>
      submodules:
        - module: ClusterConfiguration
          ignore_modules: [...]
          ...

Cluster submodules
==========
#####ClusterConfiguration

Synchronize configuration from master to slaves.
The running master configuration will be stored in the required redis backend.
Any changes to the masters configuration will be synced to the redis backend.
Slaves will check in an configurabe interval if any changes were made to the
configuration. If so, the new configuration will be imported from redis backend
and a reload will be executed.

Locally configured modules in slaves will not be overwritten by the master configuration.

Configuration example:

    - module: ClusterConfiguration
      ignore_modules: [WebGui,LocalModule]    # <default: None; type: None||list; is: optional>
      redis_client: RedisClientName           # <type: string; is: required>
      redis_key: Cluster1:configuration       # <default: 'gambolputty:configuration'; type: string; is: optional>
      redis_ttl: 600                          # <default: 3600; type: integer; is: optional>
      interval: 10                            # <default: 60; type: integer; is: optional>