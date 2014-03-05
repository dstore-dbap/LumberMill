Modifing modules
==========

#####AddDateTime

Add a field with the current datetime.

Configuration example:

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

Configuration example:

    - AddGeoInfo:
        geoip_dat_path:           # <type: string; is: required>
        geo_info_fields:          # <default: None; type: list; is: optional>
        source_fields:            # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
        target:                   # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule

#####HttpRequest

Issue an arbitrary http request and store the response in a configured field.

This module supports the storage of the responses in an redis db. If redis-client is set,
it will first try to retrieve the respone from redis via the key setting.
If that fails, it will execute the http request and store the result in redis.

Configuration example:

    - HttpRequest:
        url:                                    # <type: string; is: required>
        socket_timeout:                         # <default: 25; type: integer; is: optional>
        target_field:                           # <default: "gambolputty_http_request"; type: string; is: optional>
        redis_store:                            # <default: None; type: None||string; is: optional>
        redis_key:                              # <default: None; type: None||string; is: optional if redis_store is None else required>
        redis_ttl:                              # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule

#####Permutate

Configuration example:

    - Permutate:
        source_field:                   # <type: string; is: required>
        target_fields:                  # <type: list; is: required>
        context_data_field:             # <default: ""; type:string; is: optional>
        context_target_mapping:         # <default: {}; type: dict; is: optional if context_data_field == "" else required>
        receivers:
          - NextModule

#####ModifyFields

Module to apply common string manipulation, e.g. split, join, trim, etc. on event fields.

Configuration examples:

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

    # Insert a new field with "target_field" name an "value" as new value.
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
        target_field:                               # <default: "%(source_field)s_mapped"; type: string; is: optional>
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

    - ModifyFields
        action: split                                 # <type: string; is: required>
        separator:                                    # <type: string; is: required>
        source_field:                                 # <type: string; is: required>
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

    # Merge source fields to target field as string.
    - ModifyFields:
        action: join                                # <type: string; is: required>
        source_fields:                              # <type: list; is: required>
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