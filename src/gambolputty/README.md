Base Classes
==========

#####BaseThreadedModule

Base class for all gambolputty  modules.

Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      configuration:
        work-on-copy: True                      # <default: False; type: boolean; is: optional>
        redis-client: RedisClientName           # <default: ""; type: string; is: optional>
        redis-key: XPathParser%(server_name)s   # <default: ""; type: string; is: required if redis-client is True else optional>
        redis-ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
       - ModuleName
       - ModuleAlias