Modifing modules
==========

#####AddDateTime

Add a field with the current datetime.

Configuration example:

    - module: AddDateTime
      target_field: 'my_timestamp' # <default: '@timestamp'; type: string; is: optional>
      format: '%Y-%M-%dT%H:%M:%S'  # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
      receivers:
        - NextModule

#####AddGeoInfo

Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.

Configuration example:

    - module: AddGeoInfo
      geoip_dat_path: /usr/share/GeoIP/GeoIP.dat          # <type: string; is: required>
      source_fields: ["x_forwarded_for", "remote_ip"]     # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
      receivers:
        - NextModule

#####HttpRequest

Issue an arbitrary http request and store the response in a configured field.

This module supports the storage of the responses in an redis db. If redis-client is set,
it will first try to retrieve the respone from redis via the key setting.
If that fails, it will execute the http request and store the result in redis.

Configuration example:

    - module: HttpRequest
      url:                                    # <type: string; is: required>
      socket_timeout:                         # <default: 25; type: integer; is: optional>
      target_field:                           # <default: "gambolputty_http_request"; type: string; is: optional>
      redis_store:                            # <default: None; type: None||string; is: optional>
      redis_key:                              # <default: None; type: None||string; is: optional if redis_client == "" else required>
      redis_ttl:                              # <default: 60; type: integer; is: optional>
      receivers:
        - NextModule

#####Permutate

Configuration example:

    - module: Permutate
      source_field: facets                # <type: string; is: required>
      target_fields: ['field1', 'field2'] # <type: list; is: required>
      length: 2                           # <default: None; type: None||integer; is: optional>
      context_data_field: context_data    # <default: ""; type:string; is: optional>
      receivers:
        - NextModule

#####ModifyFields

Simple module to add/delete/change field values.

Configuration examples:

    # Keep all fields listed in source-fields, discard all others.
    - module: ModifyFields
      action: keep                                # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Discard all fields listed in source-fields.
    - module: ModifyFields
      action: delete                              # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Concat all fields listed in source_fields.
    - module: ModifyFields
      action: concat                              # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      target_field: field5                        # <type: string; is: required>
      receivers:
        - NextModule

    # Insert a new field with "target_field" name an "value" as new value.
    - module: ModifyFields
      action: insert                              # <type: string; is: required>
      target_field: "New field"                   # <type: string; is: required>
      value: "%(field1)s - %(field2)s are new."  # <type: string; is: required>
      receivers:
        - NextModule

    # Replace field values in data dictionary with self.getConfigurationValue['with'].
    - module: ModifyFields
      action: replace                             # <type: string; is: required>
      source_field: field1                        # <type: string; is: required>
      regex: ['<[^>]*>', 're.MULTILINE | re.DOTALL'] # <type: list; is: required>
      with: 'Johann Gambolputty'                  # <type: string; is: required>
      receivers:
        - NextModule

    # Replace field values matching string "old" in data dictionary with "new".
    - module: ModifyFields
      action: string_replace                      # <type: string; is: required>
      source_field: field1                        # <type: string; is: required>
      old:                                        # <type: string; is: required>
      new:                                        # <type: string; is: required>
      max:                                        # <default: -1; type: integer; is: optional>
      receivers:
        - NextModule

    # Map a field value.
    - module: ModifyFields
      action: map                                 # <type: string; is: required>
      source_field: http_status                   # <type: string; is: required>
      map: {100: 'Continue', 200: 'OK', ... }     # <type: dictionary; is: required>
      target_field: http_status                   # <default: "%(source_field)s_mapped"; type: string; is: optional>
      receivers:
        - NextModule

    # Cast field values to integer.
    - module: ModifyFields
      action: castToInteger                       # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to float.
    - module: ModifyFields
      action: castToFloat                         # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to string.
    - module: ModifyFields
      action: castToString                        # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to boolean.
    - module: ModifyFields
      action: castToBoolean                       # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule