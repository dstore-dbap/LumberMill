modifier modules
==========
#####AddDateTime

    Add a field with the current datetime.
  
    Configuration template:

    - AddDateTime:
        target_field:        # <default: '@timestamp'; type: string; is: optional>
        format:              # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
        receivers:
          - NextModule


#####AddGeoInfo

    Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.
  
    {'city': 'Hanover', 'region_name': '06', 'area_code': 0, 'time_zone': 'Europe/Berlin', 'dma_code': 0, 'metro_code': None, 'country_code3': 'DEU', 'latitude': 52.36670000000001, 'postal_code': '', 'longitude': 9.716700000000003, 'country_code': 'DE', 'country_name': 'Germany', 'continent': 'EU'}

    geoip_dat_path: path to maxmind geoip database file.  
    source_fields: list of fields to use for lookup. The first list entry that produces a hit is used.  
    target: field to populate with the geoip data. If none is provided, the field will be added directly to the event.  
    geo_info_fields: fields to add. Available field names:  
     - area_code  
     - city  
     - continent  
     - country_code  
     - country_code3  
     - country_name  
     - dma_code  
     - metro_code  
     - postal_code  
     - region_name  
     - time_zone  
     - latitude  
     - longitude
  
    Configuration template:

    - AddGeoInfo:
        geoip_dat_path:           # <type: string; is: required>
        geo_info_fields:          # <default: None; type: list; is: optional>
        source_fields:            # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
        target_field:             # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule


#####DropEvent

    Drop all events received by this module.
  
    This module is intended to be used with an activated filter.
  
    Configuration template:

    - DropEvent:
        receivers:
          - NextModule


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

    imports: Modules to import, e.g. re, math etc.  
    code: Code to execute.  
    debug: Set to True to output the string that will be executed.
  
    Configuration template:

    - ExecPython:
        imports:              # <default: []; type: list; is: optional>
        source:               # <type: string; is: required>
        debug:                # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule


#####Facet

    Collect different values of one field over a defined period of time and pass all  
    encountered variations on as new event after period is expired.
  
    The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

    The event emitted by this module will be of type: "facet" and will have "facet_field",  
    "facet_count", "facets" and "other_event_fields" fields set.

    This module supports the storage of the facet info in an redis db. If redis_store is set,  
    it will first try to retrieve the facet info from redis via the key setting.
  
    Configuration template:

    - Facet:
        source_field:                           # <type:string; is: required>
        group_by:                               # <type:string; is: required>
        add_event_fields:                       # <default: []; type: list; is: optional>
        interval:                               # <default: 5; type: float||integer; is: optional>
        redis_store:                            # <default: None; type: None||string; is: optional>
        redis_ttl:                              # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


#####FacetV2

    Collect different values of one field over a defined period of time and pass all  
    encountered variations on as new event after period is expired.
  
    The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

    The event emitted by this module will be of type: "facet" and will have "facet_field",  
    "facet_count", "facets" and "other_event_fields" fields set.

    This module supports the storage of the facet info in an backend db (At the moment this only works for a redis backend.  
    This offers the possibility of using this module across multiple instances of GambolPutty.

    source_field: Field to be scanned for unique values.  
    group_by: Field to relate the variations to, e.g. ip address.  
    add_event_fields: Fields to add from the original event to the facet event.  
    interval: Number of seconds to until all encountered values of source_field will be send as new facet event.  
    backend: Name of a key::value store plugin. When running multiple instances of gp this backend can be used to  
             synchronize events across multiple instances.  
    backend_ttl: Time to live for backend entries. Should be greater than interval.
  
    Configuration template:

    - Facet:
        source_field:               # <type:string; is: required>
        group_by:                   # <type:string; is: required>
        add_event_fields:           # <default: []; type: list; is: optional>
        interval:                   # <default: 5; type: float||integer; is: optional>
        backend:                    # <default: None; type: None||string; is: optional>
        backend_ttl:                # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


#####HttpRequest

    Issue an arbitrary http request and store the response in a configured field.

    This module supports the storage of the responses in an redis db. If redis_store is set,  
    it will first try to retrieve the response from redis via the key setting.  
    If that fails, it will execute the http request and store the result in redis.
  
    Configuration template:

    - HttpRequest:
        url:                                    # <type: string; is: required>
        socket_timeout:                         # <default: 25; type: integer; is: optional>
        target_field:                           # <default: "gambolputty_http_request"; type: string; is: optional>
        redis_store:                            # <default: None; type: None||string; is: optional>
        redis_key:                              # <default: None; type: None||string; is: optional if redis_store is None else required>
        redis_ttl:                              # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


#####Math

    Execute arbitrary math functions.

    Simple example to cast nginx request time (seconds with milliseconds as float) to apache request time  
    (microseconds as int):

    - Math:  
        filter: if $(server_type) == "nginx"  
        target_field: request_time  
        function: int(float($(request_time)) * 1000)

    If interval is set, the results of <function> will be collected for the interval time and the final result  
    will be calculated via the <results_function>.

    function: the function to be applied to/with the event data.  
    results_function: if interval is configured, use this function to calculate the final result.  
    interval: Number of seconds to until.  
    target_field: event field to store the result in.
  
    Configuration template:

    - Math:
        function:                   # <type: string; is: required>
        results_function:           # <default: None; type: None||string; is: optional if interval is None else required>
        interval:                   # <default: None; type: None||float||integer; is: optional>
        target_field:               # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule


#####MergeEvent

    Merge multiple event into a single one.

    In most cases, inputs will split an incoming stream at some kind of delimiter to produce events.  
    Sometimes, the delimiter also occurs in the event data itself and splitting here is not desired.  
    To mitigate this problem, this module can merge these fragmented events based on some configurable rules.

    Each incoming event will be buffered in a queue identified by <buffer_key>.  
    If a new event arrives and <pattern> does not match for this event, the event will be appended to the buffer.  
    If a new event arrives and <pattern> matches for this event, the buffer will be flushed prior to appending the event.  
    After <flush_interval_in_secs> the buffer will also be flushed.  
    Flushing the buffer will concatenate all contained event data to form one single new event.
  
    buffer_key: key to distinguish between different input streams

    buffer_key: A key to correctly group events.  
    buffer_size: Maximum size of events in buffer. If size is exceeded a flush will be executed.  
    flush_interval_in_secs: If interval is reached, buffer will be flushed.  
    pattern: Pattern to match new events. If pattern matches, a flush will be executed prior to appending the event to buffer.
  
    Configuration template:

    - MergeEvent:
        buffer_key:                 # <default: "%(gambolputty.received_from)s"; type: string; is: optional>
        buffer_size:                # <default: 50; type: integer; is: optional>
        flush_interval_in_secs:     # <default: None; type: None||integer; is: required if pattern is None else optional>
        pattern:                    # <default: None; type: None||string; is: required if flush_interval_in_secs is None else optional>
        match_field:                # <default: "data"; type: string; is: optional>
        receivers:
          - NextModule


#####Permutate

    Creates successive len('target_fields') length permutations of elements in 'source_field'.

    To add some context data to each emitted event 'context_data_field' can specify a field  
    containing a dictionary with the values of 'source_field' as keys.
  
    Configuration template:

    - Permutate:
        source_field:                   # <type: string; is: required>
        target_fields:                  # <type: list; is: required>
        context_data_field:             # <default: ""; type:string; is: optional>
        context_target_mapping:         # <default: {}; type: dict; is: optional if context_data_field == "" else required>
        receivers:
          - NextModule