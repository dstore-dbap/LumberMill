Output modules
==========

#####ElasticSearchSink

DEPRACTED

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

Configuration template:

    - ElasticSearchSink:
        nodes:                                    # <type: list; is: required>
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

Store the data dictionary in an elasticsearch index.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

format:     Which event fields to send on, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'.
            If not set the whole event dict is send.
nodes:      Configures the elasticsearch nodes.
connection_type:    One of: 'thrift', 'http'
http_auth:  'user:password'
use_ssl:    One of: True, False
index_name: Sets the index name. Timepatterns like %Y.%m.%d are allowed here.
doc_id:     Sets the es document id for the committed event data.
routing:    Sets a routing value (@see: http://www.elasticsearch.org/blog/customizing-your-document-routing/)
            Timepatterns like %Y.%m.%d are allowed here.
ttl:        When set, documents will be automatically deleted after ttl expired.
            Can either set time in microseconds or elasticsearch date format, e.g.: 1d, 15m etc.
            This feature needs to be enabled for the index.
            @See: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-ttl-field.html
consistency:    One of: 'one', 'quorum', 'all'
replication:    One of: 'sync', 'async'.
store_interval_in_secs:     Send data to es in x seconds intervals.
batch_size: Sending data to es if event count is above, even if store_interval_in_secs is not reached.
backlog_size:   Maximum count of events waiting for transmission. If backlog size is exceeded no new events will be processed.

Configuration example:

    - ElasticSearchMultiProcessSink:
        format:                                   # <default: None; type: None||string; is: optional>
        nodes:                                    # <type: list; is: required>
        connection_type:                          # <default: "http"; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_name:                               # <default: 'gambolputty-%Y.%m.%d'; type: string; is: optional>
        doc_id:                                   # <default: "%(gambolputty.event_id)s"; type: string; is: optional>
        routing:                                  # <default: None; type: None||string; is: optional>
        ttl:                                      # <default: None; type: None||string; is: optional>
        consistency:                              # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication:                              # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs:                   # <default: 5; type: integer; is: optional>
        batch_size:                               # <default: 500; type: integer; is: optional>
        backlog_size:                             # <default: 1000; type: integer; is: optional>

#####StdOutSink

Print the data dictionary to stdout.

Configuration template:

    - StdOutSink:
        pretty_print:           # <default: True; type: boolean; is: optional>
        format:                 # <default: ''; type: string; is: optional>

#####LoggerSink

Send data to gambolputty logger.

formats: Format of messages to send to logger, e.g.:
         ['############# Statistics #############',
          'Received events in %(interval)ds: %(total_count)d',
          'EventType: httpd_access_log - Hits: %(field_values.httpd_access_log)d',
          'EventType: Unknown - Hits: %(field_values.Unknown)d']

    Configuration template:

    - LoggerSink:
        formats:    # <type: list; is: required>

#####SyslogSink

Send events to syslog.

address: Either a server:port pattern or a filepath to an unix socket, e.g. /dev/log.
proto: Protocol to use.
facility: Syslog facility to use. List of possible values, @see: http://epydoc.sourceforge.net/stdlib/logging.handlers.SysLogHandler-class.html#facility_names
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'

Configuration template:

    - SyslogSink:
        address:              # <default: 'localhost:514'; type: string; is: required>
        proto:                # <default: 'tcp'; type: string; values: ['tcp', 'udp']; is: optional>
        facility:             # <default: 'user'; type: string; is: optional>
        format:               # <type: string; is: required>

#####FileSink

Store all received events in a file.

file_name: Absolut filename. String my contain pythons strtime directives and event fields, e.g. "/var/log/mylog-%Y-%m-%d.log"
format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'
store_interval_in_secs: sending data to es in x seconds intervals.
batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.
compress: Compress output as gzip file. For this to be effective, the chunk size should not be too small.

Configuration example:

    - FileSink:
        file_name:                            # <type: string; is: required>
        format:                               # <default: '%(data)s'; type: string; is: optional>
        store_interval_in_secs:               # <default: 10; type: integer; is: optional>
        batch_size:                           # <default: 500; type: integer; is: optional>
        backlog_size:                         # <default: 5000; type: integer; is: optional>
        compress:                             # <default: None; type: None||string; values: [None,'gzip','snappy']; is: optional>

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

Configuration template:

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

Configuration template:

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

Configuration template:

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

Here a simple example to send http_status statistics to graphite:

    ...

    - Statistics:
        interval: 10
        fields: ['http_status']

    - GraphiteSink:
        filter: if %(field_name) == "http_status"
        server: 127.0.0.1
        batch_size: 1
        formats: ['gambolputty.stats.http_200_%(interval)ds %(field_counts.200)d',
                  'gambolputty.stats.http_400_%(interval)ds %(field_counts.400)d',
                  'gambolputty.stats.http_total_%(interval)ds %(total_count)d']

    ...

Configuration template:

    - GraphiteSink:
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 2003; type: integer; is: optional>
        formats:                  # <type: list; is: required>
        store_interval_in_secs:   # <default: 5; type: integer; is: optional>
        batch_size:               # <default: 1; type: integer; is: optional>
        backlog_size:             # <default: 5000; type: integer; is: optional>

#####DevNullSink

Just discard messages send to this module.BaseThreadedModule

Configuration template:

    - DevNullSink