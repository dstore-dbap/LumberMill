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

    - ElasticSearchSink:
        nodes: [                                  # <type: list; is: required>
        connection_type:                          # <default: "http"; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_prefix:                             # <default: 'gambolputty-'; type: string; is: required if index_name is False else optional>
        index_name:                               # <default: ""; type: string; is: required if index_prefix is False else optional>
        doc_id:                                   # <default:  type: string; is: optional>
        ttl:                                      # <default: None; type: None||string; is: optional>
        consistency:                              # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication:                              # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs:                   # <default: 5; type: integer; is: optional>
        batch_size:                               # <default: 500; type: integer; is: optional>
        backlog_size:                             # <default: 5000; type: integer; is: optional>


#####ElasticSearchMultiProcessSink

!!IMPORTANT!!: In contrast to the normal ElasticSearchSink module, this module uses multiple processes to store
the events in the elasticsearch backend. This module is experimental and may cause strange side effects.
The performance gain is considerable though:
 - when run under CPython it is around 20% - 30%
 - when run under pypy it is around 40% - 60%

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

    - ElasticSearchMultiProcessSink:
        nodes:                                    # <type: list; is: required>
        connection_type:                          # <default: "http"; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_prefix:                             # <default: 'gambolputty-'; type: string; is: required if index_name is False else optional>
        index_name:                               # <default: ""; type: string; is: required if index_prefix is False else optional>
        doc_id:                                   # <default: "%(gambolputty.event_id)s"; type: string; is: optional>
        ttl:                                      # <default: None; type: None||string; is: optional>
        consistency:                              # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication:                              # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs:                   # <default: 5; type: integer; is: optional>
        batch_size:                               # <default: 500; type: integer; is: optional>
        backlog_size:                             # <default: 5000; type: integer; is: optional>

#####StdOutSink

Print the data dictionary to stdout.

Configuration example:

    - StdOutSink:
        pretty_print:           # <default: True; type: boolean; is: optional>
        format:                 # <default: ''; type: string; is: optional>

#####SyslogSink

Send events to syslog.

address: Either a server:port pattern or a filepath to an unix socket, e.g. /dev/log.
proto: Protocol to use.
facility: Syslog facility to use. List of possible values, @see: http://epydoc.sourceforge.net/stdlib/logging.handlers.SysLogHandler-class.html#facility_names
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'

Configuration example:

    - SyslogSink:
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

    - FileSink:
        path:                                 # <type: string; is: required>
        name_pattern:                         # <type: string; is: required>
        format:                               # <type: string; is: required>
        store_interval_in_secs:               # <default: 10; type: integer; is: optional>
        batch_size:                           # <default: 500; type: integer; is: optional>
        backlog_size:

#####WebHdfsSink

Store events in hdfs via webhdfs.

server: webhdfs/https node
user: Username for webhdfs.
path: Path to logfiles. String my contain any of pythons strtime directives.
name_pattern: Filename pattern. String my conatain pythons strtime directives and event fields.
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'
store_interval_in_secs: Send data to hdfs in x seconds intervals.
batch_size: Send data to hdfs if event count is above, even if store_interval_in_secs is not reached.
backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.
compress: Compress output as gzip file. For this to be effective, the batch size should not be too small.

Configuration example:

    - WebHdfsSink:
        server:                               # <default: 'localhost:14000'; type: string; is: optional>
        user:                                 # <type: string; is: required>
        path:                                 # <type: string; is: required>
        name_pattern:                         # <type: string; is: required>
        format:                               # <type: string; is: required>
        store_interval_in_secs:               # <default: 10; type: integer; is: optional>
        batch_size:                           # <default: 1000; type: integer; is: optional>
        backlog_size:                         # <default: 5000; type: integer; is: optional>
        compress:                             # <default: None; type: None||string; values: [None,'gzip','snappy']; is: optional>

#####RedisChannelSink

Publish incoming events to redis channel.

channel: Name of redis channel to send data to.
server: Redis server to connect to.
port: Port redis server is listening on.
db: Redis db.
password: Redis password.
format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send.

Configuration example:

    - RedisChannelSink:
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
        format:                     # <default: None; type: None||string; is: optional>

#####RedisListSink:

Send events to a redis lists.

list: Name of redis list to send data to.
server: Redis server to connect to.
port: Port redis server is listening on.
db: Redis db.
password: Redis password.
format: Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'. If not set the whole event dict is send.
store_interval_in_secs: Send data to redis in x seconds intervals.
batch_size: Send data to redis if event count is above, even if store_interval_in_secs is not reached.
backlog_size: Maximum count of events waiting for transmission. Events above count will be dropped.

Configuration example:

    - RedisListSink:
        list:                     # <type: String; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        format:                   # <default: None; type: None||string; is: optional>
        store_interval_in_secs:   # <default: 5; type: integer; is: optional>
        batch_size:               # <default: 500; type: integer; is: optional>
        backlog_size:             # <default: 5000; type: integer; is: optional>

#####GraphiteSink

Send metrics to graphite server.

server: Graphite server to connect to.
port: Port carbon-cache is listening on.
formats: Format of messages to send to graphite, e.g.: ['gambolputty.stats.event_rate_%(interval)ds %(event_rate)s'].
store_interval_in_secs: Send data to graphite in x seconds intervals.
batch_size: Send data to graphite if event count is above, even if store_interval_in_secs is not reached.
backlog_size: Send count of events waiting for transmission. Events above count will be dropped.

Configuration example:

    - GraphiteSink:
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 2003; type: integer; is: optional>
        formats:                  # <type: list; is: required>
        store_interval_in_secs:   # <default: 5; type: integer; is: optional>
        batch_size:               # <default: 1; type: integer; is: optional>
        backlog_size:             # <default: 5000; type: integer; is: optional>

#####DevNullSink

Just discard messages send to this module.BaseThreadedModule

Configuration example:

    - DevNullSink