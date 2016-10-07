.. _Input:

Input modules
=============

ElasticSearch
-------------

Get documents from ElasticSearch.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

| **query**:               The query to be executed, in json format.
| search_type:        The default search type just will return all found documents. If set to 'scan' it will return
| 'batch_size' number of found documents, emit these as new events and then continue until all
| documents have been sent.
| **field_mappings**:      Which fields from the result document to add to the new event.
| If set to 'all' the whole document will be sent unchanged.
| If a list is provided, these fields will be copied to the new event with the same field name.
| If a dictionary is provided, these fields will be copied to the new event with a new field name.
| E.g. if you want "_source.data" to be copied into the events "data" field, use a mapping like:
| "{'_source.data': 'data'}.
| For nested values use the dot syntax as described in:
| http://lumbermill.readthedocs.org/en/latest/introduction.html#event-field-notation
| **nodes**:               Configures the elasticsearch nodes.
| **read_timeout**:        Set number of seconds to wait until requests to elasticsearch will time out.
| **connection_type**:     One of: 'thrift', 'http'.
| **http_auth**:           'user:password'.
| **use_ssl**:             One of: True, False.
| **index_name**:          Sets the index name. Timepatterns like %Y.%m.%d are allowed here.
| **sniff_on_start**:      The client can be configured to inspect the cluster state to get a list of nodes upon startup.
| Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
| **sniff_on_connection_fail**:  The client can be configured to inspect the cluster state to get a list of nodes upon failure.
| Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
| query_interval_in_secs:   Get data to es in x seconds intervals. NOT YET IMPLEMENTED!!

Configuration template:

::

    - ElasticSearch:
       query:                           # <default: '{"query": {"match_all": {}}}'; type: string; is: optional>
       search_type:                     # <default: 'normal'; type: string; is: optional; values: ['normal', 'scan']>
       batch_size:                      # <default: 1000; type: integer; is: optional>
       field_mappings:                  # <default: 'all'; type: string||list||dict; is: optional;>
       nodes:                           # <type: string||list; is: required>
       read_timeout:                    # <default: 10; type: integer; is: optional>
       connection_type:                 # <default: 'urllib3'; type: string; values: ['urllib3', 'requests']; is: optional>
       http_auth:                       # <default: None; type: None||string; is: optional>
       use_ssl:                         # <default: False; type: boolean; is: optional>
       index_name:                      # <default: 'lumbermill-%Y.%m.%d'; type: string; is: optional>
       sniff_on_start:                  # <default: True; type: boolean; is: optional>
       sniff_on_connection_fail:        # <default: True; type: boolean; is: optional>
       query_interval_in_secs:          # <default: 5; type: integer; is: optional>
       receivers:
        - NextModule


Kafka
-----

Simple kafka input.


Configuration template:

::

    - Kafka:
       brokers:                         # <type: list; is: required>
       topics:                          # <type: string||list; is: required>
       client_id:                       # <default: 'kafka.consumer.kafka'; type: string; is: optional>
       group_id:                        # <default: None; type: None||string; is: optional>
       fetch_message_max_bytes:         # <default: 1048576; type: integer; is: optional>
       fetch_min_bytes:                 # <default: 1; type: integer; is: optional>
       fetch_wait_max_ms:               # <default: 100; type: integer; is: optional>
       refresh_leader_backoff_ms:       # <default: 200; type: integer; is: optional>
       socket_timeout_ms:               # <default: 10000; type: integer; is: optional>
       auto_offset_reset:               # <default: 'largest'; type: string; is: optional>
       auto_commit_enable:              # <default: False; type: boolean; is: optional>
       auto_commit_interval_ms:         # <default: 60000; type: integer; is: optional>
       consumer_timeout_ms:             # <default: -1; type: integer; is: optional>
       receivers:
        - NextModule


NmapScanner
-----------

Scan network with nmap and emit result as new event.

Configuration template:

::

    - NmapScanner:
       network:                         # <type: string; is: required>
       netmask:                         # <default: '/24'; type: string; is: optional>
       ports:                           # <default: None; type: None||string; is: optional>
       arguments:                       # <default: '-O -F --osscan-limit'; type: string; is: optional>
       interval:                        # <default: 900; type: integer; is: optional>
       receivers:
        - NextModule


RedisChannel
------------

Subscribes to a redis channels and passes incoming events to receivers.

| **channel**:  Name of redis channel to subscribe to.
| **server**:  Redis server to connect to.
| **port**:  Port redis server is listening on.
| **db**:  Redis db.
| **password**:  Redis password.

Configuration template:

::

    - RedisChannel:
       channel:                         # <type: string; is: required>
       server:                          # <default: 'localhost'; type: string; is: optional>
       port:                            # <default: 6379; type: integer; is: optional>
       db:                              # <default: 0; type: integer; is: optional>
       password:                        # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule


RedisList
---------

Subscribes to a redis channels/lists and passes incoming events to receivers.

| **lists**:  Name of redis lists to subscribe to.
| **server**:  Redis server to connect to.
| **port**:  Port redis server is listening on.
| **batch_size**:  Number of events to return from redis list.
| **db**:  Redis db.
| **password**:  Redis password.
| **timeout**:  Timeout in seconds.

Configuration template:

::

    - RedisList:
       lists:                           # <type: string||list; is: required>
       server:                          # <default: 'localhost'; type: string; is: optional>
       port:                            # <default: 6379; type: integer; is: optional>
       batch_size:                      # <default: 1; type: integer; is: optional>
       db:                              # <default: 0; type: integer; is: optional>
       password:                        # <default: None; type: None||string; is: optional>
       timeout:                         # <default: 0; type: integer; is: optional>
       receivers:
        - NextModule


SQS
---

Read messages from amazon sqs service.

| **aws_access_key_id**:  Your AWS id.
| **aws_secret_access_key**:  Your AWS password.
| **region**:  The region in which to find your sqs service.
| **queue**:  Queue name.
| **attribute_names**:  A list of attributes that need to be returned along with each message.
| **message_attribute_names**:  A list of message attributes that need to be returned.
| **poll_interval_in_secs**:  How often should the queue be checked for new messages.
| **batch_size**:  Number of messages to retrieve in one call.

Configuration template:

::

    - SQS:
       aws_access_key_id:               # <type: string; is: required>
       aws_secret_access_key:           # <type: string; is: required>
       region:                          # <type: string; is: required; values: ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'sa-east-1', 'us-gov-west-1', 'cn-north-1']>
       queue:                           # <type: string; is: required>
       attribute_names:                 # <default: ['All']; type: list; is: optional>
       message_attribute_names:         # <default: ['All']; type: list; is: optional>
       poll_interval_in_secs:           # <default: 1; type: integer; is: optional>
       batch_size:                      # <default: 10; type: integer; is: optional>
       receivers:
        - NextModule


Sniffer
-------

Sniff network traffic. Needs root privileges.

Reason for using pcapy as sniffer lib:
As Gambolputty is intended to be run with pypy, every module should be compatible with pypy.
Creating a raw socket in pypy is no problem but it is (up to now) not possible to bind this
socket to a selected interface, e.g. socket.bind(('lo', 0)) will throw "error: unknown address family".
With pcapy this problem does not exist.

Dependencies:
- pcapy: pypy -m pip install pcapy

Configuration template:

::

    - Sniffer:
       interface:                       # <default: 'any'; type: None||string; is: optional>
       packetfilter:                    # <default: None; type: None||string; is: optional>
       promiscous:                      # <default: False; type: boolean; is: optional>
       key_value_store:                 # <default: None; type: none||string; is: optional>
       receivers:
        - NextModule


Spam
----

Emits events as fast as possible.

Use this module to load test LumberMill. Also nice for testing your regexes.

The event field can either be a simple string. This string will be used to create a default lumbermill event dict.
If you want to provide more custom fields, you can provide a dictionary containing at least a "data" field that
should your raw event string.

events: Send custom event data. For single events, use a string or a dict. If a string is provided, the contents will
be put into the events data field.
if a dict is provided, the event will be populated with the dict fields.
For multiple events, provide a list of stings or dicts.
| **sleep**:  Time to wait between sending events.
| **events_count**:  Only send configured number of events. 0 means no limit.

Configuration template:

::

    - Spam:
       event:                           # <default: ""; type: string||list||dict; is: optional>
       sleep:                           # <default: 0; type: int||float; is: optional>
       events_count:                    # <default: 0; type: int; is: optional>
       receivers:
        - NextModule


StdIn
-----

Reads data from stdin and sends it to its output queues.

Configuration template:

::

    - StdIn:
       multiline:                       # <default: False; type: boolean; is: optional>
       stream_end_signal:               # <default: False; type: boolean||string; is: optional>
       receivers:
        - NextModule


TcpServer
---------

Reads data from tcp socket and sends it to its outputs.
Should be the best choice perfomancewise if you are on Linux and are running with multiple workers.

| **interface**:   Ipaddress to listen on.
| **port**:        Port to listen on.
| **timeout**:     Sockettimeout in seconds.
| **tls**:         Use tls or not.
| **key**:         Path to tls key file.
| **cert**:        Path to tls cert file.
| **mode**:        Receive mode, line or stream.
| **simple_separator**:   If mode is line, set separator between lines.
| **regex_separator**:    If mode is line, set separator between lines. Here regex can be used.
| **chunksize**:   If mode is stream, set chunksize in bytes to read from stream.
| **max_buffer_size**:  Max kilobytes to in receiving buffer.

Configuration template:

::

    - TcpServer:
       interface:                       # <default: ''; type: string; is: optional>
       port:                            # <default: 5151; type: integer; is: optional>
       timeout:                         # <default: None; type: None||integer; is: optional>
       tls:                             # <default: False; type: boolean; is: optional>
       key:                             # <default: False; type: boolean||string; is: required if tls is True else optional>
       cert:                            # <default: False; type: boolean||string; is: required if tls is True else optional>
       mode:                            # <default: 'line'; type: string; values: ['line', 'stream']; is: optional>
       simple_separator:                # <default: '\n'; type: string; is: optional>
       regex_separator:                 # <default: None; type: None||string; is: optional>
       chunksize:                       # <default: 16384; type: integer; is: optional>
       max_buffer_size:                 # <default: 10240; type: integer; is: optional>
       receivers:
        - NextModule


UdpServer
---------

Reads data from udp socket and sends it to its output queues.

| **interface**:   Ipaddress to listen on.
| **port**:        Port to listen on.
| **timeout**:     Sockettimeout in seconds.

Configuration template:

::

    - UdpServer:
       interface:                       # <default: '0.0.0.0'; type: string; is: optional>
       port:                            # <default: 5151; type: integer; is: optional>
       timeout:                         # <default: None; type: None||integer; is: optional>
       receivers:
        - NextModule


UnixSocket
----------

Reads data from an unix socket and sends it to its output queues.

Configuration template:

::

    - UnixSocket:
       path_to_socket:                  # <type: string; is: required>
       receivers:
        - NextModule


Zmq
---

Read events from a zeromq.


| **mode**:  Whether to run a server or client.
| **address**:  Address to connect to. Pattern: hostname:port. If mode is server, this sets the addresses to listen on.
| **pattern**:  One of 'pull', 'sub'.
| **hwm**:  Highwatermark for sending/receiving socket.

Configuration template:

::

    - Zmq:
       mode:                            # <default: 'server'; type: string; values: ['server', 'client']; is: optional>
       address:                         # <default: '*:5570'; type: string; is: optional>
       pattern:                         # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
       topic:                           # <default: ''; type: string; is: optional>
       hwm:                             # <default: None; type: None||integer; is: optional>
       receivers:
        - NextModule


ZmqTornado
----------

Read events from a zeromq.

| **mode**:  Whether to run a server or client.
| **address**:  Address to connect to. Pattern: hostname:port. If mode is server, this sets the addresses to listen on.
| **pattern**:  One of 'pull', 'sub'.
| **hwm**:  Highwatermark for sending/receiving socket.
| **separator**:  When using the sub pattern, messages can have a topic. Set separator to split message from topic.

Configuration template:

::

    - ZmqTornado:
       mode:                            # <default: 'server'; type: string; values: ['server', 'client']; is: optional>
       address:                         # <default: '*:5570'; type: string; is: optional>
       pattern:                         # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
       topic:                           # <default: ''; type: string; is: optional>
       separator:                       # <default: None; type: None||string; is: optional>
       hwm:                             # <default: None; type: None||integer; is: optional>
       receivers:
        - NextModule