.. _Output:

Output modules
==============

DevNullSink
-----------

Just discard messeages send to this module.

Configuration template:

::

    - DevNullSink


ElasticSearchSink
-----------------

Store the data dictionary in an elasticsearch index.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

| **action**:      Either index or update. If update be sure to provide the correct doc_id.
| **format**:      Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'.
| If not set the whole event dict is send.
| **nodes**:       Configures the elasticsearch nodes.
| **connection_type**:     One of: 'thrift', 'http'.
| **http_auth**:   'user:password'.
| **use_ssl**:     One of: True, False.
| **index_name**:  Sets the index name. Timepatterns like %Y.%m.%d and dynamic values like $(bar) are allowed here.
| **doc_id**:      Sets the es document id for the committed event data.
| routing:    Sets a routing value (@see: http://www.elasticsearch.org/blog/customizing-your-document-routing/)
| Timepatterns like %Y.%m.%d are allowed here.
| **ttl**:         When set, documents will be automatically deleted after ttl expired.
| Can either set time in milliseconds or elasticsearch date format, e.g.: 1d, 15m etc.
| This feature needs to be enabled for the index.
| @See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-ttl-field.html
| **sniff_on_start**:  The client can be configured to inspect the cluster state to get a list of nodes upon startup.
| Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
| **sniff_on_connection_fail**:  The client can be configured to inspect the cluster state to get a list of nodes upon failure.
| Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
| **consistency**:     One of: 'one', 'quorum', 'all'.
| **store_interval_in_secs**:      Send data to es in x seconds intervals.
| **batch_size**:  Sending data to es if event count is above, even if store_interval_in_secs is not reached.
| **backlog_size**:    Maximum count of events waiting for transmission. If backlog size is exceeded no new events will be processed.

Configuration template:

::

    - ElasticSearchSink:
       action:                          # <default: 'index'; type: string; is: optional; values: ['index', 'update']>
       format:                          # <default: None; type: None||string; is: optional>
       nodes:                           # <type: string||list; is: required>
       connection_type:                 # <default: 'http'; type: string; values: ['thrift', 'http']; is: optional>
       http_auth:                       # <default: None; type: None||string; is: optional>
       use_ssl:                         # <default: False; type: boolean; is: optional>
       index_name:                      # <default: 'lumbermill-%Y.%m.%d'; type: string; is: optional>
       doc_id:                          # <default: '$(lumbermill.event_id)'; type: string; is: optional>
       routing:                         # <default: None; type: None||string; is: optional>
       ttl:                             # <default: None; type: None||integer||string; is: optional>
       sniff_on_start:                  # <default: False; type: boolean; is: optional>
       sniff_on_connection_fail:        # <default: False; type: boolean; is: optional>
       consistency:                     # <default: 'quorum'; type: string; values: ['one', 'quorum', 'all']; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 1000; type: integer; is: optional>


FileSink
--------

Store all received events in a file.

| **file_name**:  absolute path to filen. String my contain pythons strtime directives and event fields, e.g. %Y-%m-%d.
| format: Which event fields to use in the logline, e.g. '$(@timestamp) - $(url) - $(country_code)'
| **store_interval_in_secs**:  sending data to es in x seconds intervals.
| **batch_size**:  sending data to es if event count is above, even if store_interval_in_secs is not reached.
| **backlog_size**:  maximum count of events waiting for transmission. Events above count will be dropped.
| **compress**:  Compress output as gzip or snappy file. For this to be effective, the chunk size should not be too small.

Configuration template:

::

    - FileSink:
       file_name:                       # <type: string; is: required>
       format:                          # <default: '$(data)'; type: string; is: optional>
       store_interval_in_secs:          # <default: 10; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>
       compress:                        # <default: None; type: None||string; values: [None,'gzip','snappy']; is: optional>


GraphiteSink
------------

Send metrics to graphite server.

| **server**:  Graphite server to connect to.
| **port**:  Port carbon-cache is listening on.
| **formats**:  Format of messages to send to graphite, e.g.: ['lumbermill.stats.event_rate_$(interval)s $(event_rate)'].
| **store_interval_in_secs**:  Send data to graphite in x seconds intervals.
| **batch_size**:  Send data to graphite if event count is above, even if store_interval_in_secs is not reached.
| **backlog_size**:  Send count of events waiting for transmission. Events above count will be dropped.

Here a simple example to send http_status statistics to graphite:

...

- Statistics:
interval: 10
fields: ['http_status']

- GraphiteSink:
filter: if $(field_name) == "http_status"
server: 127.0.0.1
batch_size: 1
formats: ['lumbermill.stats.http_200_$(interval)s $(field_counts.200)',
'lumbermill.stats.http_400_$(interval)s $(field_counts.400)',
'lumbermill.stats.http_total_$(interval)s $(total_count)']

...

Configuration template:

::

    - GraphiteSink:
       server:                          # <default: 'localhost'; type: string; is: optional>
       port:                            # <default: 2003; type: integer; is: optional>
       formats:                         # <type: list; is: required>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 1; type: integer; is: optional>
       backlog_size:                    # <default: 50; type: integer; is: optional>


LoggerSink
----------

Send data to lumbermill logger.

formats: Format of messages to send to logger, e.g.:
['############# Statistics #############',
'Received events in $(interval)s: $(total_count)',
'EventType: httpd_access_log - Hits: $(field_counts.httpd_access_log)',
'EventType: Unknown - Hits: $(field_counts.Unknown)']

Configuration template:

::

    - LoggerSink:
       formats:                         # <type: list; is: required>


RedisChannelSink
----------------

Publish incoming events to redis channel.

| **channel**:  Name of redis channel to send data to.
| **server**:  Redis server to connect to.
| **port**:  Port redis server is listening on.
| **db**:  Redis db.
| **password**:  Redis password.
| **format**:  Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set, the whole event dict is send.

Configuration template:

::

    - RedisChannelSink:
       channel:                         # <type: string; is: required>
       server:                          # <default: 'localhost'; type: string; is: optional>
       port:                            # <default: 6379; type: integer; is: optional>
       db:                              # <default: 0; type: integer; is: optional>
       password:                        # <default: None; type: None||string; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>


RedisListSink
-------------

Send events to a redis lists.

| **list**:  Name of redis list to send data to.
| **server**:  Redis server to connect to.
| **port**:  Port redis server is listening on.
| **db**:  Redis db.
| **password**:  Redis password.
| **format**:  Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set the whole event dict is send.
| **store_interval_in_secs**:  Send data to redis in x seconds intervals.
| **batch_size**:  Send data to redis if event count is above, even if store_interval_in_secs is not reached.
| **backlog_size**:  Maximum count of events waiting for transmission. Events above count will be dropped.

Configuration template:

::

    - RedisListSink:
       list:                            # <type: String; is: required>
       server:                          # <default: 'localhost'; type: string; is: optional>
       port:                            # <default: 6379; type: integer; is: optional>
       db:                              # <default: 0; type: integer; is: optional>
       password:                        # <default: None; type: None||string; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>


SQSSink
-------

Send messages to amazon sqs service.

| **aws_access_key_id**:  Your AWS id.
| **aws_secret_access_key**:  Your AWS password.
| **region**:  The region in which to find your sqs service.
| **queue**:  Queue name.
| **format**:  Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'.
| If not set event.data will be send es MessageBody, all other fields will be send as MessageAttributes.
| **store_interval_in_secs**:  Send data to redis in x seconds intervals.
| batch_size: Number of messages to collect before starting to send messages to sqs. This refers to the internal
| receive buffer of this plugin. When the receive buffer is maxed out, this plugin will always send
| the maximum of 10 messages in one send_message_batch call.
| **backlog_size**:  Maximum count of events waiting for transmission. Events above count will be dropped.

values: ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'sa-east-1', 'us-gov-west-1', 'cn-north-1']

Configuration template:

::

    - SQSSink:
       aws_access_key_id:               # <type: string; is: required>
       aws_secret_access_key:           # <type: string; is: required>
       region:                          # <type: string; is: required>
       queue:                           # <type: string; is: required>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>
       receivers:
        - NextModule


StdOutSink
----------

Print the data dictionary to stdout.

| **pretty_print**:  Use pythons pprint function.
| **format**:  Format of messages to send to graphite, e.g.: ['lumbermill.stats.event_rate_$(interval)s $(event_rate)'].

Configuration template:

::

    - StdOutSink:
       pretty_print:                    # <default: True; type: boolean; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
       parser:                          # <default: None; type: None||string; is: optional>


SyslogSink
----------

Send events to syslog.

| **format**:  Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set the whole event dict is send.
| **address**:  Either a server:port pattern or a filepath to a unix socket, e.g. /dev/log.
| **proto**:  Protocol to use.
| facility: Syslog facility to use. List of possible values, @see: http://epydoc.sourceforge.net/stdlib/logging.handlers.SysLogHandler-class.html#facility_names

Configuration template:

::

    - SyslogSink:
       format:                          # <type: string; is: required>
       address:                         # <default: 'localhost:514'; type: string; is: required>
       proto:                           # <default: 'tcp'; type: string; values: ['tcp', 'udp']; is: optional>
       facility:                        # <default: 'user'; type: string; is: optional>


WebHdfsSink
-----------

Store events in hdfs via webhdfs.

server: webhdfs/https node
| **user**:  Username for webhdfs.
| **path**:  Path to logfiles. String my contain any of pythons strtime directives.
| **name_pattern**:  Filename pattern. String my conatain pythons strtime directives and event fields.
| **format**:  Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set the whole event dict is send.
| **store_interval_in_secs**:  Send data to webhdfs in x seconds intervals.
| **batch_size**:  Send data to webhdfs if event count is above, even if store_interval_in_secs is not reached.
| **backlog_size**:  Maximum count of events waiting for transmission. Events above count will be dropped.
| **compress**:  Compress output as gzip file. For this to be effective, the chunk size should not be too small.

Configuration template:

::

    - WebHdfsSink:
       server:                          # <default: 'localhost:14000'; type: string; is: optional>
       user:                            # <type: string; is: required>
       path:                            # <type: string; is: required>
       name_pattern:                    # <type: string; is: required>
       format:                          # <type: string; is: required>
       store_interval_in_secs:          # <default: 10; type: integer; is: optional>
       batch_size:                      # <default: 1000; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>
       compress:                        # <default: None; type: None||string; values: [None,'gzip','snappy']; is: optional>


ZmqSink
-------

Sends events to zeromq.

| **server**:  Server to connect to. Pattern: hostname:port.
| **pattern**:  Either push or pub.
| **mode**:  Whether to run a server or client. If running as server, pool size is restricted to a single process.
| **topic**:  The channels topic.
| **hwm**:  Highwatermark for sending socket.
| **format**:  Which event fields to send on, e.g. '$(@timestamp) - $(url) - $(country_code)'. If not set the whole event dict is send msgpacked.
| **store_interval_in_secs**:  Send data to redis in x seconds intervals.
| **batch_size**:  Send data to redis if event count is above, even if store_interval_in_secs is not reached.
| **backlog_size**:  Maximum count of events waiting for transmission. Events above count will be dropped.

Configuration template:

::

    - ZmqSink:
       server:                          # <default: 'localhost:5570'; type: string; is: optional>
       pattern:                         # <default: 'push'; type: string; values: ['push', 'pub']; is: optional>
       mode:                            # <default: 'connect'; type: string; values: ['connect', 'bind']; is: optional>
       topic:                           # <default: None; type: None||string; is: optional>
       hwm:                             # <default: None; type: None||integer; is: optional>
       format:                          # <default: None; type: None||string; is: optional>
       store_interval_in_secs:          # <default: 5; type: integer; is: optional>
       batch_size:                      # <default: 500; type: integer; is: optional>
       backlog_size:                    # <default: 5000; type: integer; is: optional>