Misc modules
==========

#####RedisClient

A simple wrapper around the redis python module.

It can be used to store results of modules in a redis key/value store.

See BaseModule documentation how values can be stored.

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


#####TrackEvents

Keeps track of all events passing through GambolPutty.

This module stores all events that enter GambolPutty in a redis backend and deletes them, as soon as they
get destroyed by the BaseModule.destroyEvent method. Events that did not get destroyed will be resent when
GamboPutty is restarted. This should make sure that nearly every event gets to its destination, even when
something goes absolutely wrong.

As storage backend a redis client is needed.

Please note, that this will significantly slow down the event processing. You have to decide if speed or
event delivery is of higher importance to you. Even without this module, GambolPutty tries to make sure
all events reach their destination. This module is thread based, so playing around with its pool size might
increase performance.

!!IMPORTANT!!: At the moment, this module will only work with TcpServerTornado as input.

Configuration example:

    - module: TrackEvents
      pool_size: 1
      configuration:
        redis_client: RedisClientName           # <type: string; is: required>
        redis_ttl: 3600                         # <default: 3600; type: integer; is: optional>



#####Statistics

Collect and log some statistic data.

Configuration example:

    - module: Statistics
      configuration:
        print_interval: 10                 # <default: 10; type: integer; is: optional>
        event_type_statistics: True        # <default: True; type: boolean; is: optional>
        receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
        waiting_event_statistics: True     # <default: True; type: boolean; is: optional>
        processing_event_statistics: True  # <default: False; type: boolean; is: optional>


#####Facet

Collect different values of one field over a defined period of time and pass all
encountered variations on as new event after period is expired.

The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

The event emitted by this module will be of type: "facet" and will have "facet_field",
"facet_count", "facets" and "other_event_fields" fields set.

This module supports the storage of the facet info in an redis db. If redis-client is set,
it will first try to retrieve the facet info from redis via the key setting.

    Configuration example:

    - module: Facet
      configuration:
        source_field: url                       # <type:string; is: required>
        group_by: %(remote_ip)s                 # <type:string; is: required>
        add_event_fields: [user_agent]          # <default: []; type: list; is: optional>
        interval: 30                            # <default: 5; type: float||integer; is: optional>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
        - NextModule


#####Tarpit

Send an event into a tarpit before passing it on.

Useful only for testing purposes of threading problems and concurrent access to event data.

    Configuration example:

    - module: Tarpit
      configuration:
        delay: 10  # <default: 10; type: integer; is: optional>
      receivers:
        - NextModule