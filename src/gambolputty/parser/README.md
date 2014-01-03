Parser modules
==========

#####RegexParser

Parse a string by named regular expressions.

Configuration example:

    - module: RegexParser
      configuration:
        source_field: field1                    # <default: 'data'; type: string; is: optional>
        target_field: event_type                # <default: 'event_type'; type: string; is: optional>
        mark_unmatched_as: unknown              # <default: 'unknown'; type: string; is: optional>
        break_on_match: True                    # <default: True; type: boolean; is: optional>
        field_extraction_patterns:              # <type: [string,list]; is: required>
          httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']

#####UrlParser

Parse and extract url parameters.

Configuration example:

    - module: UrlParser
      configuration:
        source_field: uri       # <type: string; is: required>

#####XPathParser

Parse an xml string via xpath.

This module supports the storage of the results in an redis db. If redis-client is set,
it will first try to retrieve the result from redis via the key setting.
If that fails, it will execute the xpath query and store the result in redis.

Configuration example:

    - module: XPathParser
      configuration:
        source_field: 'xml_data'                                # <type: string; is: required>
        query:  '//Item[@%(server_name)s]/@NodeDescription'     # <type: string; is: required>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_key: HttpRequest%(server_name)s   # <default: ""; type: string; is: optional if redis_client is False else required>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>

#####CsvParser

Parse a string as csv data.

It will parse the csv and create or replace fields in the internal data dictionary with
the corresponding csv fields.

Configuration example:

    - module: CsvParser
      configuration:
        source_field: 'data'                    # <default: 'data'; type: string; is: optional>
        escapechar: \                           # <default: '\'; type: string; is: optional>
        skipinitialspace: False                 # <default: False; type: boolean; is: optional>
        quotechar: '"'                          # <default: '"'; type: string; is: optional>
        delimiter: ';'                          # <default: '|'; type: char; is: optional>
        fieldnames: ["gumby", "brain", "specialist"]        # <default: False; type: [list]; is: optional>
      receivers:
        - NextHandler

#####JsonParser

It will parse the json data and create or replace fields in the internal data dictionary with
the corresponding json fields.

At the moment only flat json files can be processed correctly.

Configuration example:

    - module: JsonParser
      configuration:
        source_field: 'data'                    # <default: 'data'; type: string; is: optional>
      receivers:
        - NextHandler

#####SyslogPrivalParser

It will parse the source field in the event dictionary for the default severity
and facility fields (RFC5424, http://tools.ietf.org/html/rfc5424).
The source field must contain the prival with the pattern: "<d+>"

Numerical             Facility
 Code

  0             kernel messages
  1             user-level messages
  2             mail system
  3             system daemons
  4             security/authorization messages
  5             messages generated internally by syslogd
  6             line printer subsystem
  7             network news subsystem
  8             UUCP subsystem
  9             clock daemon
 10             security/authorization messages
 11             FTP daemon
 12             NTP subsystem
 13             log audit
 14             log alert
 15             clock daemon (note 2)
 16             local use 0  (local0)
 17             local use 1  (local1)
 18             local use 2  (local2)
 19             local use 3  (local3)
 20             local use 4  (local4)
 21             local use 5  (local5)
 22             local use 6  (local6)
 23             local use 7  (local7)

Numerical         Severity
 Code

  0       Emergency: system is unusable
  1       Alert: action must be taken immediately
  2       Critical: critical conditions
  3       Error: error conditions
  4       Warning: warning conditions
  5       Notice: normal but significant condition
  6       Informational: informational messages
  7       Debug: debug-level messages

Configuration example:

    - module: SyslogPrivalParser
      configuration:
        source_field: 'syslog_prival'               # <default: 'syslog_prival'; type: string; is: optional>
        map_values: False                           # <default: True; type: boolean; is: optional>
        facility_mappings:  {23: 'Bolton'}          # <default: {}; type: dictionary; is: optional>
        severity_mappings:  {0: 'DeadParrotAlert'}  # <default: {}; type: dictionary; is: optional>
      receivers:
        - NextHandler