Misc modules
==========

#####ExecPython

Execute python code.

To make sure that the yaml parser keeps the tabs in the source code, ensure that the code is preceded by a comment.
E.g.:

- ExecPython:
source: |
  # Useless comment...
    try:
        imported = math
    except NameError:
        import math
    event['request_time'] = math.ceil(event['request_time'] * 1000)

code: Code to execute.
debug: Set to True to output the string that will be executed.

Configuration example:

    - ExecPython:
        source:               # <type: string; is: required>
        debug:                # <default: False; type: boolean; is: optional>

#####RedisStore

A simple wrapper around the redis python module.

It can be used to store results of modules in a redis key/value store.

cluster: dictionary of redis masters as keys and pack_followers as values.

Configuration example:

    - RedisStore:
        server:                                  # <default: 'localhost'; type: string; is: optional>
        cluster:                                 # <default: {}; type: dictionary; is: optional>
        port:                                    # <default: 6379; type: integer; is: optional>
        db:                                      # <default: 0; type: integer; is: optional>
        password:                                # <default: None; type: None||string; is: optional>
        socket_timeout:                          # <default: 10; type: integer; is: optional>
        charset:                                 # <default: 'utf-8'; type: string; is: optional>
        errors:                                  # <default: 'strict'; type: string; is: optional>
        decode_responses:                        # <default: False; type: boolean; is: optional>
        unix_socket_path:                        # <default: ''; type: string; is: optional>


#####RedisEventBuffer

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

!!IMPORTANT!!: At the moment, this module does not work. Will be rewritten...

Configuration example:

    - RedisEventBuffer:
        redis_store:                            # <type: string; is: required>
        queue_size:                             # <default: 5; type: integer; is: optional>
        redis_ttl:                              # <default: 3600; type: integer; is: optional>


#####Statistics

Collect and log some statistic data.

Configuration example:

    - Statistics:
        interval:                      # <default: 10; type: integer; is: optional>
        event_type_statistics:         # <default: True; type: boolean; is: optional>
        receive_rate_statistics:       # <default: True; type: boolean; is: optional>
        waiting_event_statistics:      # <default: False; type: boolean; is: optional>

#####Facet

Collect different values of one field over a defined period of time and pass all
encountered variations on as new event after period is expired.

The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

The event emitted by this module will be of type: "facet" and will have "facet_field",
"facet_count", "facets" and "other_event_fields" fields set.

This module supports the storage of the facet info in an redis db. If redis-client is set,
it will first try to retrieve the facet info from redis via the key setting.

Configuration example:

    - Facet:
        source_field:                           # <type:string; is: required>
        group_by:                               # <type:string; is: required>
        add_event_fields:                       # <default: []; type: list; is: optional>
        interval:                               # <default: 5; type: float||integer; is: optional>
        redis_store:                            # <default: None; type: None||string; is: optional>
        redis_ttl:                              # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


#####Tarpit

Send an event into a tarpit before passing it on.

Useful only for testing purposes of threading problems and concurrent access to event data.

Configuration example:

    - Tarpit:
        delay:          # <default: 10; type: integer; is: optional>
        receivers:
          - NextModule