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
        db: 0                   # <default: 0; type: string; is: optional>
        password: None          # <default: None; type: string; is: optional>
        socket-timeout: 10      # <default: 10; type: integer; is: optional>
        connection-pool: 10     # <default: None; type: object; is: optional>
        charset: 'utf-8'        # <default: 'utf-8'; type: string; is: optional>
        errors: 'strict'        # <default: 'strict'; type: string; is: optional>
        decode-responses: False # <default: False; type: boolean; is: optional>
        unix-socket-path: None  # <default: None; type: object; is: optional>

#####Statistics

Collect and log some statistic data.

Configuration example:

    - module: Statistics
      configuration:
        print-regex-statistics-interval: 1000               # <default: 1000; type: integer; is: optional>
        regexStatistics: True                               # <default: True; type: boolean; is: optional>
        receiveRateStatistics: True                         # <default: True; type: boolean; is: optional>
        waitingEventStatistics: True                        # <default: True; type: boolean; is: optional>