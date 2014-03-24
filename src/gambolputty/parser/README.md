Parser modules
==========

#####RegexParser

Parse a string by named regular expressions.

Configuration template:

    - RegexParser:
        source_field:                           # <default: 'data'; type: string; is: optional>
        mark_unmatched_as:                      # <default: 'unknown'; type: string; is: optional>
        break_on_match:                         # <default: True; type: boolean; is: optional>
        field_extraction_patterns:              # <type: dict; is: required>
          httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']
        receivers:
          - NextModule

#####LineParser

Line parser.

Will split the data in source fields and emit parts as new events. Original event will be discarded.

source_fields:  Input fields for decode.

Configuration template:

    - LineParser:
        source_fields:                        # <default: 'data'; type: string||list; is: optional>
        seperator:                            # <default: '\n'; type: string; is: optional>
        target_field:                         # <default: 'data'; type:string; is: optional>
        keep_original:                        # <default: False; type: boolean; is: optional>
        receivers:
          - NextHandler

#####UrlParser

Urlencode or decode an event field and extract url parameters.

mode: Either encode or decode data.
source_field: Event field to en/decode.
target_field: Event field to update with en/decode result. If not set source will be replaced.
parse_querystring: Parse url for query parameters and extract them.
querystring_target_field: Event field to update with url parameters.
querystring_prefix: Prefix string to prepend to url parameter keys.

Configuration template:

    - UrlParser:
        mode:                     # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        source_field:             # <type: string; is: required>
        target_field:             # <default: None; type: None||string; is: optional>
        parse_querystring:        # <default: False; type: boolean; is: optional>
        querystring_target_field: # <default: None; type: None||string; is: optional>
        querystring_prefix:       # <default: None; type: string; is: optional>

#####XPathParser

Parse an xml string via xpath.

This module supports the storage of the results in an redis db. If redis-client is set,
it will first try to retrieve the result from redis via the key setting.
If that fails, it will execute the xpath query and store the result in redis.

Configuration template:

    - XPathParser:
        source_field:                          # <type: string; is: required>
        target_field:                          # <default: "gambolputty_xpath"; type: string; is: optional>
        query:                                 # <type: string; is: required>
        redis_store:                           # <default: None; type: None||string; is: optional>
        redis_key:                             # <default: None; type: None||string; is: optional if redis_store is None else required>
        redis_ttl:                             # <default: 60; type: integer; is: optional>

#####CsvParser

Parse a string as csv data.

It will parse the csv and create or replace fields in the internal data dictionary with
the corresponding csv fields.

Configuration template:

    - CsvParser:
        source_field:                           # <default: 'data'; type: string; is: optional>
        escapechar:                             # <default: '\'; type: string; is: optional>
        skipinitialspace:                       # <default: False; type: boolean; is: optional>
        quotechar:                              # <default: '"'; type: string; is: optional>
        delimiter:                              # <default: '|'; type: char; is: optional>
        fieldnames:                             # <default: False; type: [list]; is: optional>
        receivers:
          - NextHandler

#####JsonParser

It will parse the json data and create or replace fields in the internal data dictionary with
the corresponding json fields.

At the moment only flat json files can be processed correctly.

Configuration template:

    - JsonParser:
        mode:                                   # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_field:                           # <default: None; type: None||string; is: optional>
        keep_original:                          # <default: False; type: boolean; is: optional>
        receivers:
          - NextHandler

#####MsgPackParser

It will parse the msgpack data and create or replace fields in the internal data dictionary with
the corresponding json fields.

Configuration template:

    - MsgPackParser:
        mode:                                   # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_field:                           # <default: None; type: None||string; is: optional>
        keep_original:                          # <default: False; type: boolean; is: optional>
        receivers:
          - NextHandler

#####SyslogPrivalParser

It will parse the source field in the event dictionary for the default severity
and facility fields (RFC5424, http://tools.ietf.org/html/rfc5424).
The source field must contain the prival with the pattern: "<\d+>"

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

Configuration template:

    - SyslogPrivalParser:
        source_field: 'syslog_prival'               # <default: 'syslog_prival'; type: string; is: optional>
        map_values: False                           # <default: True; type: boolean; is: optional>
        facility_mappings:  {23: 'Bolton'}          # <default: {}; type: dictionary; is: optional>
        severity_mappings:  {0: 'DeadParrotAlert'}  # <default: {}; type: dictionary; is: optional>
        receivers:
          - NextHandler