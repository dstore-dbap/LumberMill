Base Classes
==========

#####BaseThreadedModule

Base class for all gambolputty  modules.

Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: False; type: string; is: optional>
      pool-size: 4                              # <default: 1; type: integer; is: optional>
      configuration:
        work-on-copy: True                      # <default: False; type: boolean; is: optional>
        redis-client: RedisClientName           # <default: False; type: string; is: optional>
        redis-key: XPathParser%(server_name)s   # <default: False; type: string; is: optional>
        redis-ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:                                # <type: list, is: required>
       - ModuleName
       - ModuleAlias