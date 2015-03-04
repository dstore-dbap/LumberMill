.. _Misc:

Misc modules
============

EventBuffer
-----------

Store received events in a persistent backend until the event was successfully handled.
Events, that did not get handled correctly, will be requeued when GambolPutty is restarted.

At the moment only RedisStore is supported as backend.

As a technical note: This module is based on pythons garbage collection. If an event is
created, a copy of the event is stored in the persistence backend. If it gets garbage collected,
the event will be deleted from the backend.
When used, this module forces a garbage collection every <gc_interval> seconds.
This approach seemed to be the fastest and simplest with a small drawback:
IMPORTANT: It is not absolutely guaranteed, that an event will be collected, thus the event will
not be deleted from the backend data. This can cause a limited amount of duplicate events being
send to the sinks.
With an elasticsearch sink, this should be no problem, as long as your document id
stays the same for the same event data. This is also true for the default event_id.

Configuration template:

::

    - EventBuffer:
        backend:            # <default: 'RedisStore'; type: string; is: optional>
        gc_interval:        # <default: 5; type: integer; is: optional>
        key_prefix:         # <default: "gambolputty:eventbuffer"; type: string; is: optional>


KeyValueStore
-------------

A simple wrapper around the python simplekv module.

It can be used to store results of modules in all simplekv supported backends.

When set, the following options cause RedisStore to use a buffer for setting values.
Multiple values are set via the pipe command, which speeds up storage. Still this comes at a price.
Buffered values, that have not yet been send to redis, will be lost when GambolPutty crashes.

backend: backends supported by [simplekv](http://pythonhosted.org//simplekv/)
store_interval_in_secs: Sending data to redis in x seconds intervals.
batch_size: Sending data to redis if count is above, even if store_interval_in_secs is not reached.
backlog_size: Maximum count of values waiting for transmission. Values above count will be dropped.

Configuration template:

::

    - KeyValueStore:
        backend:                                 # <default: 'DictStore'; type: string; is: optional>
        server:                                  # <default: None; type: None||string; is: required if backend in ['RedisStore', 'MemcacheStore'] and cluster is None else optional>
        cluster:                                 # <default: None; type: None||dictionary; is: required if backend == 'RedisStore' and server is None else optional>
        port:                                    # <default: 6379; type: integer; is: optional>
        db:                                      # <default: 0; type: integer; is: optional>
        password:                                # <default: None; type: None||string; is: optional>
        socket_timeout:                          # <default: 10; type: integer; is: optional>
        charset:                                 # <default: 'utf-8'; type: string; is: optional>
        errors:                                  # <default: 'strict'; type: string; is: optional>
        decode_responses:                        # <default: False; type: boolean; is: optional>
        unix_socket_path:                        # <default: None; type: None||string; is: optional>
        batch_size:                              # <default: None; type: None||integer; is: optional>
        store_interval_in_secs:                  # <default: None; type: None||integer; is: optional>
        backlog_size:                            # <default: 5000; type: integer; is: optional>


RedisStore
----------

A simple wrapper around the redis python module.

It can be used to store results of modules in a redis key/value store.

server: Redis server to connect to.
cluster: Dictionary of redis masters as keys and pack_followers as values, e.g.: {'172.16.0.1:6379': '172.16.0.2:6379'}
port: Port redis server is listening on.
db: Redis db.
password: Redis password.
socket_timeout: Socket timeout in seconds.
charset: Charset to use.
errors:
decode_responses: specifies whether return values from Redis commands get decoded automatically using the client's charset value.
unix_socket_path: Path to unix socket file.

When set, the following options cause RedisStore to use a buffer for setting values.
Multiple values are set via the pipe command, which speeds up storage. Still this comes at a price.
Buffered values, that have not yet been send to redis, will be lost when GambolPutty crashes.

store_interval_in_secs: Sending data to redis in x seconds intervals.
batch_size: Sending data to redis if count is above, even if store_interval_in_secs is not reached.
backlog_size: Maximum count of values waiting for transmission. Values above count will be dropped.

Configuration template:

::

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
        unix_socket_path:                        # <default: None; type: None||string; is: optional>
        batch_size:                              # <default: None; type: None||integer; is: optional>
        store_interval_in_secs:                  # <default: None; type: None||integer; is: optional>
        backlog_size:                            # <default: 5000; type: integer; is: optional>


SimpleStats
-----------

Collect and log some simple gambolputty statistic data.

Use this module if you just need some simple statistics on how many events are passing through gambolputty.
Per default, statistics will just be send to stdout.

As a side note: This module inits MultiProcessStatisticCollector. As it uses multiprocessing.Manager().dict()
this will start another process. So if you use SimpleStats, you will see workers + 1 processes in the process
list.

Configuration template:

::

    - SimpleStats:
        interval:                      # <default: 10; type: integer; is: optional>
        event_type_statistics:         # <default: True; type: boolean; is: optional>
        receive_rate_statistics:       # <default: True; type: boolean; is: optional>
        waiting_event_statistics:      # <default: False; type: boolean; is: optional>
        emit_as_event:                 # <default: False; type: boolean; is: optional>


SimpleStats
-----------

Collect and log some simple gambolputty statistic data.

Use this module if you just need some simple statistics on how many events are passing through gambolputty.
Per default, statistics will just be send to stdout.

Configuration template:

::

    - SimpleStats:
        interval:                      # <default: 10; type: integer; is: optional>
        event_type_statistics:         # <default: True; type: boolean; is: optional>
        receive_rate_statistics:       # <default: True; type: boolean; is: optional>
        waiting_event_statistics:      # <default: False; type: boolean; is: optional>
        emit_as_event:                 # <default: False; type: boolean; is: optional>


Statistics
----------

Collect and log statistic data.

This module keeps track of the number of times a field occured in an event during interval.
So, if you want to count the http_status codes encountered during the last 10s, you would use this configuration:
- Statistics:
interval: 10
fields: [http_status]

After interval seconds, an event will be emitted with the following fields (counters are just examples ;):
{'data': '',
'event_type': 'statistic',
'field_name': 'http_status',
'field_counts': {'200': 5, '301': 10, '400': 5},
'gambolputty': {'event_id': 'cef34d298fbe8ce4b662251e17b2acfb',
'event_type': 'statistic',
'received_from': False,
'source_module': 'Statistics'}
'interval': 10,
'total_count': 20}

Configuration template:

::

    - Statistics:
        interval:                      # <default: 10; type: integer; is: optional>
        fields:                        # <default: ['gambolputty.event_type']; type: list; is: optional>


Tarpit
------

Send an event into a tarpit before passing it on.

Useful only for testing purposes of threading problems and concurrent access to event data.

Configuration template:

::

    - Tarpit:
        delay:          # <default: 10; type: integer; is: optional>
        receivers:
          - NextModule


Throttle
--------

Throttle event count over a given time period.

key: Identifies events as being the "same". Dynamic notations can be used here.
timeframe: Time window in seconds from first encountered event to last.
min_count: Minimal count of same events to allow event to be passed on.
max_mount: Maximum count of same events before same events will be blocked.
backend: Name of a key::value store plugin. When running multiple instances of gp this backend can be used to
synchronize events across multiple instances.
backend_key_prefix: Prefix for the backend key.

Configuration template:

::

    - Throttle:
        key:                # <type:string; is: required>
        timeframe:          # <default: 600; type: integer; is: optional>
        min_count:          # <default: 1; type: integer; is: optional>
        max_count:          # <default: 1; type: integer; is: optional>
        backend:            # <default: None; type: None||string; is: optional>
        backend_key_prefix: # <default: "gambolputty:throttle"; type: string; is: optional>
        receivers:
          - NextModule