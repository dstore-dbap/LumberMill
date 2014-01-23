Base Classes
==========

#####BaseModule

Base class for all GambolPutty modules that will run not run.
If you happen to override one of the methods defined here, be sure to know what you
are doing ;) You have been warned ;)

Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      redis_client: RedisClientName             # <default: ""; type: string; is: optional>
      redis_key: XPathParser%(server_name)s     # <default: ""; type: string; is: required if redis_client is True else optional>
      redis_ttl: 600                            # <default: 60; type: integer; is: optional>
      ...
      receivers:
       - ModuleName
       - ModuleAlias

#####BaseThreadedModule

Base class for all GambolPutty modules that will run as separate threads.
If you happen to override one of the methods defined here, be sure to know what you
are doing ;) You have been warned ;)

Running a module as a thread should only be done if the task is mainly I/O bound or the
used python code will release the GIL during its man work.
Otherwise a threaded module is prone to slow everything down.

Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      pool_size: 4                              # <default: None; type: None||integer; is: optional>
      queue_size: 20                            # <default: None; type: None||integer; is: optional>
      redis_client: RedisClientName             # <default: ""; type: string; is: optional>
      redis_key: XPathParser%(server_name)s     # <default: ""; type: string; is: required if redis_client is True else optional>
      redis_ttl: 600                            # <default: 60; type: integer; is: optional>
      ...
      receivers:
       - ModuleName
       - ModuleAlias