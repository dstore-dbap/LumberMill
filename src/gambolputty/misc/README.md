Misc modules
==========

#####RedisClient

A simple wrapper around the redis python module.

It can be used to store results of modules in a redis key/value store.

See BaseThreadedModule documentation how values can be stored.

Configuration example:

    - module: RedisClient
      configuration:
        server: redis.server    # <default: 'localhost'; type: string; is: optional>
        port: 6379              # <default: 6379; type: integer; is: optional>
        db: 0                   # <default: 0; type: integer; is: optional>
        password: None          # <default: None; type: None||string; is: optional>
        socket_timeout: 10      # <default: 10; type: integer; is: optional>
        charset: 'utf-8'        # <default: 'utf-8'; type: string; is: optional>
        errors: 'strict'        # <default: 'strict'; type: string; is: optional>
        decode_responses: False # <default: False; type: boolean; is: optional>
        unix_socket_path: ''    # <default: ''; type: string; is: optional>

#####Statistics

Collect and log some statistic data.

Configuration example:

    - module: Statistics
      configuration:
        print_interval: 1000               # <default: 1000; type: integer; is: optional>
        regex_statistics: True             # <default: True; type: boolean; is: optional>
        receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
        waiting_event_statistics: True     # <default: True; type: boolean; is: optional>