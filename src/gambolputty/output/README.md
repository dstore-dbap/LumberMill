Output modules
==========

#####ElasticSearchSink

Store the data dictionary in an elasticsearch index.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

nodes: configures the elasticsearch nodes.
connection_type: one of: 'thrift', 'http'
http_auth: 'user:password'
use_ssl: one of: True, False
index_prefix: es index prefix to use, will be appended with '%Y.%m.%d'.
index_name: sets a fixed name for the es index.
doc_id: sets the es document id for the committed event data.
ttl: When set, documents will be automatically deleted after ttl expired.
     Can either set time in microseconds or elasticsearch date format, e.g.: 1d, 15m etc.
     This feature needs to be enabled for the index.
     @See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-ttl-field.html
consistency: one of: 'one', 'quorum', 'all'
replication: one of: 'sync', 'async'.
store_interval_in_secs: sending data to es in x seconds intervals.
batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.

Configuration example:

    - module: ElasticSearchSink
        nodes: ["localhost:9200"]                 # <type: list; is: required>
        connection_type: http                     # <default: "thrift"; type: string; values: ['thrift', 'http']; is: optional>
        http_auth: 'user:password'                # <default: None; type: None||string; is: optional>
        use_ssl: True                             # <default: False; type: boolean; is: optional>
        index_prefix: agora_access-               # <default: 'gambolputty-'; type: string; is: required if index_name is False else optional>
        index_name: "Fixed index name"            # <default: ""; type: string; is: required if index_prefix is False else optional>
        doc_id: 'data'                            # <default: "data"; type: string; is: optional>
        ttl:                                      # <default: None; type: None||string; is: optional>
        consistency: 'one'                        # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication: 'sync'                       # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs: 1                 # <default: 5; type: integer; is: optional>
        batch_size: 500                           # <default: 500; type: integer; is: optional>
        backlog_size: 5000                        # <default: 5000; type: integer; is: optional>


#####ElasticSearchMultiProcessSink

Same configuration as above but with multiple processes.

!!IMPORTANT!!: In contrast to the normal ElasticSearchSink module, this module uses multiple processes to store
the events in the elasticsearch backend. This module is experimental and may cause strange side effects.
The performance gain is considerable though:
 - when run under CPython it is around 20% - 30%
 - when run under pypy it is around 40% - 60%

#####StdOutSink

Print the data dictionary to stdout.

Configuration example:

    - module: StdOutSink
      pretty_print: True      # <default: True; type: boolean; is: optional>

#####SyslogSink

Send events to syslog.

address: Either a server:port pattern or a filepath to an unix socket, e.g. /dev/log.
proto: Protocol to use.
facility: Syslog facility to use. List of possible values, @see: http://epydoc.sourceforge.net/stdlib/logging.handlers.SysLogHandler-class.html#facility_names
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'

Configuration example:

    - module: SyslogSink
      address:              # <default: 'localhost:514'; type: string; is: required>
      proto:                # <default: 'tcp'; type: string; values: ['tcp', 'udp']; is: optional>
      facility:             # <default: 'user'; type: string; is: optional>
      format:               # <type: string; is: required>

#####FileSink

Store events in a file.

path: Path to logfiles. String my contain any of pythons strtime directives.
name_pattern: Filename pattern. String my conatain pythons strtime directives and event fields.
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'
store_interval_in_secs: sending data to es in x seconds intervals.
batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.

Configuration example:

    - module: FileSink
      path:                                 # <type: string; is: required>
      name_pattern:                         # <type: string; is: required>
      format:                               # <type: string; is: required>
      store_interval_in_secs:               # <default: 1; type: integer; is: optional>
      batch_size:                   # <default: 500; type: integer; is: optional>
      backlog_size:                         # <default: 5000; type: integer; is: optional>

#####WebHdfsSink

Store events in hdfs via webhdfs.

server: webhdfs/https node
user: Username for webhdfs.
path: Path to logfiles. String my contain any of pythons strtime directives.
name_pattern: Filename pattern. String my conatain pythons strtime directives and event fields.
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'
store_interval_in_secs: Sending data to es in x seconds intervals.
batch_size: Sending data to es if event count is above, even if store_interval_in_secs is not reached.
backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.
compress: Compress output as gzip file. For this to be effective, the batch size should not be too small.

Configuration example:

    - module: WebHdfsSink
      server:                               # <default: 'localhost:14000'; type: string; is: optional>
      user:                                 # <type: string; is: required>
      path:                                 # <type: string; is: required>
      name_pattern:                         # <type: string; is: required>
      format:                               # <type: string; is: required>
      store_interval_in_secs:               # <default: 10; type: integer; is: optional>
      batch_size:                           # <default: 1000; type: integer; is: optional>
      backlog_size:                         # <default: 5000; type: integer; is: optional>
      compress:                             # <default: True; type: boolean; is: optional>

#####RedisChannelSink

Publish incoming events to redis channel.

format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send.

Configuration example:

    - module: RedisChannelSink
      channel: my_channel         # <type: string; is: required>
      server: redis.server        # <default: 'localhost'; type: string; is: optional>
      port: 6379                  # <default: 6379; type: integer; is: optional>
      db: 0                       # <default: 0; type: integer; is: optional>
      password: None              # <default: None; type: None||string; is: optional>
      format:                     # <default: None; type: string; is: optional>
      fields:                     # <default: None; type: None||list; is: optional>

#####DevNullSink

Just discard messages send to this module.BaseThreadedModule

Configuration example:

    - module: DevNullSink