.. _Modifier:

Modifier modules
================

AddDateTime
-----------

Add a field with the current datetime.

Configuration template:

::

    - AddDateTime:
        target_field:        # <default: '@timestamp'; type: string; is: optional>
        format:              # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
        receivers:
          - NextModule


AddDnsLookup
------------

Add dns info for selected fields.

|**action**: Either resolve or revers.
|**source_field**: Source field to use for (reverse) lookups.
|**target_field**: Target field to store result of lookup. If none is provided, the source field will be replaced.
|**nameservers**: List of nameservers to use. If not provided, the system default servers will be used.
|**timeout**: Timeout for lookups in seconds.

Configuration template:

::

    - AddDnsLookup:
       action:             # <default: 'resolve'; type: string; is: optional; values: ['resolve', 'reverse']>
       source_field:       # <default: None; type: string; is: required>
       target_field:       # <default: None; type: None||string; is: optional>
       nameservers:        # <default: None; type: None||string||list; is: optional>
       timeout:            # <default: 1; type: integer; is: optional>
       receivers:
          - NextModule


AddGeoInfo
----------

Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.

Here an example of fields that the module provides:
{'city': 'Hanover', 'region_name': '06', 'area_code': 0, 'time_zone': 'Europe/Berlin', 'dma_code': 0, 'metro_code': None, 'country_code3': 'DEU', 'latitude': 52.36670000000001, 'postal_code': '', 'longitude': 9.716700000000003, 'country_code': 'DE', 'country_name': 'Germany', 'continent': 'EU'}

| **geoip_dat_path**:  path to maxmind geoip database file.
| **source_fields**:  list of fields to use for lookup. The first list entry that produces a hit is used.
| **target**:  field to populate with the geoip data. If none is provided, the field will be added directly to the event.
| geo_info_fields: fields to add. Available field names:
| - area_code
| - city
| - continent
| - country_code
| - country_code3
| - country_name
| - dma_code
| - metro_code
| - postal_code
| - region_name
| - time_zone
| - latitude
| - longitude

Configuration template:

::

    - AddGeoInfo:
        geoip_dat_path:           # <type: string; is: required>
        geo_info_fields:          # <default: None; type: list; is: optional>
        source_fields:            # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
        target_field:             # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule


DropEvent
---------

Drop all events received by this module.

This module is intended to be used with an activated filter.

Configuration template:

::

    - DropEvent:
        receivers:
          - NextModule


ExecPython
----------

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

| **imports**:  Modules to import, e.g. re, math etc.
| **code**:  Code to execute.
| **debug**:  Set to True to output the string that will be executed.

Configuration template:

::

    - ExecPython:
        imports:              # <default: []; type: list; is: optional>
        source:               # <type: string; is: required>
        debug:                # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule


Facet
-----

Collect different values of one field over a defined period of time and pass all
encountered variations on as new event after period is expired.

The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

The event emitted by this module will be of type: "facet" and will have "facet_field",
"facet_count", "facets" and "other_event_fields" fields set.

This module supports the storage of the facet info in an redis db. If redis_store is set,
it will first try to retrieve the facet info from redis via the key setting.

Configuration template:

::

    - Facet:
        source_field:                           # <type:string; is: required>
        group_by:                               # <type:string; is: required>
        add_event_fields:                       # <default: []; type: list; is: optional>
        interval:                               # <default: 5; type: float||integer; is: optional>
        redis_store:                            # <default: None; type: None||string; is: optional>
        redis_ttl:                              # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


FacetV2
-------

Collect different values of one field over a defined period of time and pass all
encountered variations on as new event after period is expired.

The "add_event_fields" configuration will copy the configured event fields into the "other_event_fields" list.

The event emitted by this module will be of type: "facet" and will have "facet_field",
"facet_count", "facets" and "other_event_fields" fields set.

This module supports the storage of the facet info in an backend db (At the moment this only works for a redis backend.
This offers the possibility of using this module across multiple instances of GambolPutty.

| **source_field**:  Field to be scanned for unique values.
| **group_by**:  Field to relate the variations to, e.g. ip address.
| **add_event_fields**:  Fields to add from the original event to the facet event.
| **interval**:  Number of seconds to until all encountered values of source_field will be send as new facet event.
| backend: Name of a key::value store plugin. When running multiple instances of gp this backend can be used to
| synchronize events across multiple instances.
| **backend_ttl**:  Time to live for backend entries. Should be greater than interval.

Configuration template:

::

    - Facet:
        source_field:               # <type:string; is: required>
        group_by:                   # <type:string; is: required>
        add_event_fields:           # <default: []; type: list; is: optional>
        interval:                   # <default: 5; type: float||integer; is: optional>
        backend:                    # <default: None; type: None||string; is: optional>
        backend_ttl:                # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


HttpRequest
-----------

Issue an arbitrary http request and store the response in a configured field.

This module supports the storage of the responses in an redis db. If redis_store is set,
it will first try to retrieve the response from redis via the key setting.
If that fails, it will execute the http request and store the result in redis.

Configuration template:

::

    - HttpRequest:
        url:                                    # <type: string; is: required>
        socket_timeout:                         # <default: 25; type: integer; is: optional>
        target_field:                           # <default: "gambolputty_http_request"; type: string; is: optional>
        redis_store:                            # <default: None; type: None||string; is: optional>
        redis_key:                              # <default: None; type: None||string; is: optional if redis_store is None else required>
        redis_ttl:                              # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule


Math
----

Execute arbitrary math functions.

Simple example to cast nginx request time (seconds with milliseconds as float) to apache request time
(microseconds as int):

- Math:
filter: if $(server_type) == "nginx"
target_field: request_time
function: int(float($(request_time)) * 1000)

If interval is set, the results of <function> will be collected for the interval time and the final result
will be calculated via the <results_function>.

| **function**:  the function to be applied to/with the event data.
| **results_function**:  if interval is configured, use this function to calculate the final result.
| **interval**:  Number of seconds to until.
| **target_field**:  event field to store the result in.

Configuration template:

::

    - Math:
        function:                   # <type: string; is: required>
        results_function:           # <default: None; type: None||string; is: optional if interval is None else required>
        interval:                   # <default: None; type: None||float||integer; is: optional>
        target_field:               # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule


MergeEvent
----------

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

| **buffer_key**:  A key to correctly group events.
| **buffer_size**:  Maximum size of events in buffer. If size is exceeded a flush will be executed.
| **flush_interval_in_secs**:  If interval is reached, buffer will be flushed.
| **pattern**:  Pattern to match new events. If pattern matches, a flush will be executed prior to appending the event to buffer.
| **glue**:  Join event data with glue as separator.

Configuration template:

::

    - MergeEvent:
        buffer_key:                 # <default: "$(gambolputty.received_from)"; type: string; is: optional>
        buffer_size:                # <default: 100; type: integer; is: optional>
        flush_interval_in_secs:     # <default: 1; type: None||integer; is: required if pattern is None else optional>
        pattern:                    # <default: None; type: None||string; is: required if flush_interval_in_secs is None else optional>
        match_field:                # <default: "data"; type: string; is: optional>
        glue:                       # <default: ""; type: string; is: optional>
        receivers:
          - NextModule


ModifyFields
------------

Simple module to insert/delete/change field values.

Configuration templates:

::

    # Keep all fields listed in source_fields, discard all others.
    - ModifyFields:
        action: keep                                # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
        receivers:
          - NextModule

    # Discard all fields listed in source_fields.
    - ModifyFields:
        action: delete                              # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
        receivers:
          - NextModule

    # Concat all fields listed in source_fields.
    - ModifyFields:
        action: concat                              # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
        target_field:                               # <type: string; is: required>
        receivers:
          - NextModule

    # Insert a new field with "target_field" name and "value" as new value.
    - ModifyFields:
        action: insert                              # <type: string; is: required>
        target_field:                               # <type: string; is: required>
        value:                                      # <type: string; is: required>
        receivers:
          - NextModule

    # Replace field values matching string "old" in data dictionary with "new".
    - ModifyFields:
        action: string_replace                      # <type: string; is: required>
        source_field:                               # <type: string; is: required>
        old:                                        # <type: string; is: required>
        new:                                        # <type: string; is: required>
        max:                                        # <default: -1; type: integer; is: optional>
        receivers:
          - NextModule

    # Replace field values in data dictionary with self.getConfigurationValue['with'].
    - ModifyFields:
        action: replace                             # <type: string; is: required>
        source_field:                               # <type: string; is: required>
        regex: ['<[^>]*>', 're.MULTILINE | re.DOTALL'] # <type: list; is: required>
        with:                                       # <type: string; is: required>
        receivers:
          - NextModule

    # Map a field value.
    - ModifyFields:
        action: map                                 # <type: string; is: required>
        source_field:                               # <type: string; is: required>
        map:                                        # <type: dictionary; is: required>
        target_field:                               # <default: "$(source_field)_mapped"; type: string; is: optional>
        receivers:
          - NextModule

    # Split source field to target fields based on key value pairs.
    - ModifyFields:
        action: key_value                           # <type: string; is: required>
        line_separator:                             # <type: string; is: required>
        kv_separator:                               # <type: string; is: required>
        source_field:                               # <type: list; is: required>
        target_field:                               # <default: None; type: None||string; is: optional>
        prefix:                                     # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule

    # Split source field to target fields based on key value pairs using regex.
    - ModifyFields:
        action: key_value_regex                     # <type: string; is: required>
        regex:                                      # <type: string; is: required>
        source_field:                               # <type: list; is: required>
        target_field:                               # <default: None; type: None||string; is: optional>
        prefix:                                     # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule

    # Split source field to array at separator.
    - ModifyFields:
      action: split                                 # <type: string; is: required>
      separator:                                    # <type: string; is: required>
      source_field:                                 # <type: list; is: required>
      target_field:                                 # <default: None; type: None||string; is: optional>
      receivers:
        - NextModule

    # Merge source fields to target field as list.
    - ModifyFields:
        action: merge                               # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
        target_field:                               # <type: string; is: reuired>
        receivers:
          - NextModule

    # Merge source field to target field as string.
    - ModifyFields:
        action: join                                # <type: string; is: required>
        source_field:                               # <type: string; is: required>
        target_field:                               # <type: string; is: required>
        separator:                                  # <default: ","; type: string; is: optional>
        receivers:
          - NextModule

    # Cast field values to integer.
    - ModifyFields:
        action: cast_to_int                         # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
        receivers:
          - NextModule

    # Cast field values to float.
    - ModifyFields:
      action: cast_to_float                       # <type: string; is: required>
      source_fields:                              # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to string.
    - ModifyFields:
      action: cast_to_str                         # <type: string; is: required>
      source_fields:                              # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to boolean.
    - ModifyFields:
        action: cast_to_bool                        # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
        receivers:
          - NextModule

    # Create a hash from a field value.
    # If target_fields is provided, it should have the same length as source_fields.
    # If target_fields is not provided, source_fields will be replaced with the hashed value.
    # Hash algorithm can be any of the in hashlib supported algorithms.
    - ModifyFields:
        action: hash                                # <type: string; is: required>
        algorithm: sha1                             # <default: "md5"; type: string; is: optional;>
        salt:                                       # <default: None; type: None||string; is: optional;>
        source_fields:                              # <type: list; is: required>
        target_fields:                              # <default: []; type: list; is: optional>
        receivers:
          - NextModule

Permutate
---------

Creates successive len('target_fields') length permutations of elements in 'source_field'.

To add some context data to each emitted event 'context_data_field' can specify a field
containing a dictionary with the values of 'source_field' as keys.

Configuration template:

::

    - Permutate:
        source_field:                   # <type: string; is: required>
        target_fields:                  # <type: list; is: required>
        context_data_field:             # <default: ""; type:string; is: optional>
        context_target_mapping:         # <default: {}; type: dict; is: optional if context_data_field == "" else required>
        receivers:
          - NextModule