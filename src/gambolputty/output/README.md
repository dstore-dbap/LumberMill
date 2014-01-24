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
consistency: one of: 'one', 'quorum', 'all'
replication: one of: 'sync', 'async'.
store_interval_in_secs: sending data to es in x seconds intervals.
max_waiting_events: sending data to es if event count is above, even if store_interval_in_secs is not reached.
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
        consistency: 'one'                        # <default: "quorum"; type: string; values: ['one', 'quorum', 'all']; is: optional>
        replication: 'sync'                       # <default: "sync"; type: string;  values: ['sync', 'async']; is: optional>
        store_interval_in_secs: 1                 # <default: 1; type: integer; is: optional>
        max_waiting_events: 500                   # <default: 500; type: integer; is: optional>
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

#####DevNullSink

Just discard messages send to this module.BaseThreadedModule

Configuration example:

    - module: DevNullSink