.. _Parser:

Parser modules
==============

CollectdParser
--------------

Parse collectd binary protocol data.

This module can receive binary data from the collectd network plugin.

Decode:
It will parse the collectd binary data and create or replace fields in the internal data dictionary with
the corresponding collectd data.
Encode:
Encode selected fields or all to collectd binary protocol.

Configuration template:

::

    - CollectdParser:
        action:                                 # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_field:                           # <default: None; type: None||string; is: optional>
        keep_original:                          # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule


CsvParser
---------

Parse a string as csv data.

It will parse the csv and create or replace fields in the internal data dictionary with
the corresponding csv fields.

Configuration template:

::

    - CsvParser:
        source_field:                           # <default: 'data'; type: string; is: optional>
        escapechar:                             # <default: '\'; type: string; is: optional>
        skipinitialspace:                       # <default: False; type: boolean; is: optional>
        quotechar:                              # <default: '"'; type: string; is: optional>
        delimiter:                              # <default: '|'; type: string; is: optional>
        fieldnames:                             # <default: False; type: list; is: optional>
        receivers:
          - NextModule


InflateParser
-------------

Inflate any field with supported compression codecs.

It will take the source fields and decompress them with the configured codecs. At the moment only gzip an zlib are
supported.

source_fields: single field or list of fields to decompress.
target_fields: single field or list of fields to fill with decompressed data.
               If not provided, contents of source_fields will be replaced.
compression:   compression lib to use for decompression

Configuration template:

::

    - CsvParser:
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_fields:                          # <default: None; type: None||string||list; is: optional>
        compression:                            # <default: 'gzip'; type: string; is: optional; values: ['gzip', 'zlib']>
        receivers:
          - NextModule


JsonParser
----------

Json codec.

Decode:
It will parse the json data in source fields and create or replace fields in the internal data dictionary with
the corresponding json fields.

Encode:
It will build a new list of source fields and create json of this list.

At the moment only flat json files can be processed correctly.

| **action**:  Either encode or decode data.
| **source_fields**:   Input fields for de/encode.
| If encoding, you can set this field to 'all' to encode the complete event dict.
| **target_field**:    Target field for de/encode result.
| If decoding and target is not set, the event dict itself will be updated with decoded fields.
| **keep_original**:   Switch to keep or drop the original fields used in de/encoding from the event dict.

Configuration template:

::

    - JsonParser:
        action:                                 # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        mode:                                   # <default: 'line'; type: string; values: ['line','stream']; is: optional>
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_field:                           # <default: None; type: None||string; is: optional>
        keep_original:                          # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule


LineParser
----------

Line parser.

Decode:
Will split the data in source fields and emit parts as new events. Original event will be discarded.

| **source_fields**:   Input fields for decode.

Configuration template:

::

    - LineParser:
        source_fields:                        # <default: 'data'; type: string||list; is: optional>
        seperator:                            # <default: '\n'; type: string; is: optional>
        target_field:                         # <default: 'data'; type:string; is: optional>
        keep_original:                        # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule


MsgPackParser
-------------

Decode:
It will parse the msgpack data and create or replace fields in the internal data dictionary with
the corresponding json fields.
Encode:
Encode selected fields or all to msgpack format.

Configuration template:

::

    - MsgPackParser:
        action:                                 # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        mode:                                   # <default: 'line'; type: string; values: ['line','stream']; is: optional>
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_field:                           # <default: None; type: None||string; is: optional>
        keep_original:                          # <default: False; type: boolean; is: optional>
        receivers:
          - NextModule


RegexParser
-----------

Parse a string by named regular expressions.

If regex matches, fields in the data dictionary will be set as defined in the named regular expression.
Additionally the field "gambolputty.event_type" will be set containing the name of the regex.
In the example below this would be "httpd_access_log".

It is also possible to define multiple regexes with the same name. This allows for different log patterns
for the same log type, e.g. apache access logs and nginx access logs.

| **source_field**:  Field to apply the regex to.
| **mark_unmatched_as**:  Set <gambolputty.event_type> to this value if regex did not match.
| **break_on_match**:  Stop applying regex patterns after first match.
| **hot_rules_first**:  Apply regex patterns based on their hit count.

Configuration template:

::

    - RegexParser:
        source_field:                           # <default: 'data'; type: string; is: optional>
        mark_unmatched_as:                      # <default: 'Unknown'; type: string; is: optional>
        break_on_match:                         # <default: True; type: boolean; is: optional>
        hot_rules_first:                        # <default: True; type: boolean; is: optional>
        field_extraction_patterns:              # <type: list; is: required>
          - httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']
        receivers:
          - NextModule


SyslogPrivalParser
------------------

It will parse the source field in the event dictionary for the default severity
and facility fields (RFC5424, http://tools.ietf.org/html/rfc5424).
The source field must contain the prival with the pattern: "\d+"

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

::

    - SyslogPrivalParser:
        source_field: 'syslog_prival'               # <default: 'syslog_prival'; type: string; is: optional>
        map_values: False                           # <default: True; type: boolean; is: optional>
        facility_mappings:  {23: 'Bolton'}          # <default: {}; type: dictionary; is: optional>
        severity_mappings:  {0: 'DeadParrotAlert'}  # <default: {}; type: dictionary; is: optional>
        receivers:
          - NextModule


UrlParser
---------

Urlencode or decode an event field and extract url parameters.

| **action**:  Either encode or decode data.
| **source_field**:  Event field to en/decode.
| **target_field**:  Event field to update with en/decode result. If not set source will be replaced.
| **parse_querystring**:  Parse url for query parameters and extract them.
| **querystring_target_field**:  Event field to update with url parameters.
| **querystring_prefix**:  Prefix string to prepend to url parameter keys.

Configuration template:

::

    - UrlParser:
        action:                   # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        source_field:             # <type: string; is: required>
        target_field:             # <default: None; type: None||string; is: optional>
        parse_querystring:        # <default: False; type: boolean; is: optional>
        querystring_target_field: # <default: None; type: None||string; is: optional>
        querystring_prefix:       # <default: None; type: None||string; is: optional>
        receivers:
          - NextModule


UserAgentParser
---------------

Parse http user agent string

A string like:

"Mozilla/5.0 (Linux; U; Android 2.3.5; en-in; HTC_DesireS_S510e Build/GRJ90) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"

will produce this dictionary:

'user_agent_info': {   'device': {   'family': u'HTC DesireS'},
'os': {   'family': 'Android',
'major': '2',
'minor': '3',
'patch': '5',
'patch_minor': None},
'user_agent': {   'family': 'Android',
'major': '2',
'minor': '3',
'patch': '5'}}}

| **source_fields**:   Input field to parse.
| **target_field**:  field to update with parsed info fields.

Configuration template:

::

    - LineParser:
        source_fields:               # <type: string||list; is: required>
        target_field:                # <default: 'user_agent_info'; type:string; is: optional>
        receivers:
          - NextModule


XPathParser
-----------

Parse an xml string via xpath.

This module supports the storage of the results in an redis db. If redis-client is set,
it will first try to retrieve the result from redis via the key setting.
If that fails, it will execute the xpath query and store the result in redis.

Configuration template:

::

    - XPathParser:
        source_field:                          # <type: string; is: required>
        target_field:                          # <default: "gambolputty_xpath"; type: string; is: optional>
        query:                                 # <type: string; is: required>
        redis_store:                           # <default: None; type: None||string; is: optional>
        redis_key:                             # <default: None; type: None||string; is: optional if redis_store is None else required>
        redis_ttl:                             # <default: 60; type: integer; is: optional>
        receivers:
          - NextModule