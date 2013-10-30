Modifing modules
==========

#####AddDateTime

Add a field with the current datetime.

Configuration example:

    - module: AddDateTime
      configuration:
        target-field: 'my_timestamp' # <default: '@timestamp'; type: string; is: optional>
        format: '%Y-%M-%dT%H:%M:%S'  # <default: '%Y-%m-%dT%H:%M:%S'; type: string; is: optional>
      receivers:
        - NextModule

#####AddGeoInfo

Add country_code and longitude-latitude fields based  on a geoip lookup for a given ip address.

Configuration example:

    - module: AddGeoInfo
      configuration:
        geoip-dat-path: /usr/share/GeoIP/GeoIP.dat          # <type: string; is: required>
        source-fields: ["x_forwarded_for", "remote_ip"]     # <default: ["x_forwarded_for", "remote_ip"]; type: list; is: optional>
      receivers:
        - NextModule

#####HttpRequest

Issue an arbitrary http request and store the response in a configured field.

This module supports the storage of the responses in an redis db. If redis-client is set,
it will first try to retrieve the respone from redis via the key setting.
If that fails, it will execute the http request and store the result in redis.

Configuration example:

    - module: HttpRequest
      configuration:
        url: http://%(server_name)s/some/path   # <type: string; is: required>
        socket-timeout: 25                      # <default: 25; type: integer; is: optional>
        target-field: http_response             # <default: "gambolputty_http_request"; type: string; is: optional>
        redis-client: RedisClientName           # <default: ""; type: string; is: optional>
        redis-key: HttpRequest%(server_name)s   # <default: ""; type: string; is: optional>
        redis-ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
        - NextModule

#####ModifyFields

Simple module to add/delete/change field values.

Configuration examples:

    # Keep all fields listed in source-fields, discard all others.
    - module: ModifyFields
      configuration:
        action: keep                                # <type: string; is: required>
        source-fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Discard all fields listed in source-fields.
    - module: ModifyFields
      configuration:
        action: delete                              # <type: string; is: required>
        source-fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Replace field values in data dictionary with self.getConfigurationValue['with'].
    - module: ModifyFields
      configuration:
        action: replace                             # <type: string; is: required>
        source-field: field1                        # <type: string; is: required>
        regex: ['<[^>]*>', 're.MULTILINE | re.DOTALL'] # <type: list; is: required>
        with: 'Johann Gambolputty'                  # <type: string; is: required>
      receivers:
        - NextModule

    # Map a field value.
    - module: ModifyFields
      configuration:
        action: map                                 # <type: string; is: required>
        source-field: http_status                   # <type: string; is: required>
        map: {100: 'Continue', 200: 'OK', ... }     # <type: dictionary; is: required>
        target-field: http_status                   # <default: "%(source-field)s_mapped"; type: string; is: optional>
      receivers:
        - NextModule

    # Cast field values to integer.
    - module: ModifyFields
      configuration:
        action: castToInteger                       # <type: string; is: required>
        source-fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to float.
    - module: ModifyFields
      configuration:
        action: castToFloat                         # <type: string; is: required>
        source-fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to string.
    - module: ModifyFields
      configuration:
        action: castToString                        # <type: string; is: required>
        source-fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to boolean.
    - module: ModifyFields
      configuration:
        action: castToBoolean                       # <type: string; is: required>
        source-fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule