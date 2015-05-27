.. _Input:

Input modules
=============

ElasticSearch
-------------

Get documents from ElasticSearch.

The elasticsearch module takes care of discovering all nodes of the elasticsearch cluster.
Requests will the be loadbalanced via round robin.

| **query:**         The query to be executed, in json format.
| **search_type:**   The default search type just will return all found documents in one chunk. If set to 'scan',
|                    it will return 'size' number of found documents, emit these as new events and then continue until
|                    no more documents can be retrieved. @see: http://elasticsearch-py.readthedocs.org/en/master/helpers.html
| **field_mappings:** Which fields from the result document to add to the new event.
|                     If set to 'all' the whole document will be sent unchanged.
|                     If a list is provided, these fields will be copied to the new event with the same field name.
|                     If a dictionary is provided, these fields will be copied to the new event with the corresponding new field name.
|                     E.g. if you want "_source.data" to be copied into the events "data" field, use a mapping like:
|                     "{'_source.data': 'data'}.
|                     For nested values use the dot syntax as described in:
|                     @see: http://gambolputty.readthedocs.org/en/latest/introduction.html#event-field-notation
| **nodes:**         Configures the elasticsearch nodes.
| **connection_type:** One of: 'thrift', 'http'.
| **http_auth:**     'user:password'.
| **use_ssl:**       One of: True, False.
| **index_name:**    Sets the index name. Timepatterns like %Y.%m.%d are allowed here.
| **sniff_on_start:** The client can be configured to inspect the cluster state to get a list of nodes upon startup.
|                     Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
| **sniff_on_connection_fail:** The client can be configured to inspect the cluster state to get a list of nodes upon failure.
|                               Might cause problems on hosts with multiple interfaces. If connections fail, try to deactivate this.
| **query_interval_in_secs:**   Get data to es in x seconds intervals. NOT YET IMPLEMENTED!!

Configuration template:

::

    - ElasticSearch:
        query:                                    # <default: '{"query": {"match_all": {}}}'; type: string; is: optional>
        search_type:                              # <default: 'normal'; type: string; is: optional; values: ['normal', 'scan']>
        field_mappings:                           # <default: 'all'; type: string||list||dict; is: optional;>
        nodes:                                    # <type: list; is: required>
        connection_type:                          # <default: 'http'; type: string; values: ['thrift', 'http']; is: optional>
        http_auth:                                # <default: None; type: None||string; is: optional>
        use_ssl:                                  # <default: False; type: boolean; is: optional>
        index_name:                               # <default: 'gambolputty-%Y.%m.%d'; type: string; is: optional>
        sniff_on_start:                           # <default: True; type: boolean; is: optional>
        sniff_on_connection_fail:                 # <default: True; type: boolean; is: optional>
        query_interval_in_secs:                   # <default: 5; type: integer; is: optional>


Kafka
-----

Simple kafka input.


Configuration template:

::

    - Kafka:
        brokers:                    # <type: list; is: required>
        topics:                     # <type: string||list; is: required>
        client_id:                  # <default: 'kafka.consumer.kafka'; type: string; is: optional>
        group_id:                   # <default: None; type: None||string; is: optional>
        fetch_message_max_bytes:    # <default: 1048576; type: integer; is: optional>
        fetch_min_bytes:            # <default: 1; type: integer; is: optional>
        fetch_wait_max_ms:          # <default: 100; type: integer; is: optional>
        refresh_leader_backoff_ms:  # <default: 200; type: integer; is: optional>
        socket_timeout_ms:          # <default: 10000; type: integer; is: optional>
        auto_offset_reset:          # <default: 'largest'; type: string; is: optional>
        auto_commit_enable:         # <default: False; type: boolean; is: optional>
        auto_commit_interval_ms:    # <default: 60000; type: integer; is: optional>
        consumer_timeout_ms:        # <default: -1; type: integer; is: optional>
        receivers:
          - NextModule


NmapScanner
-----------

Scan network with nmap and emit result as new event.

Configuration template:

::

    - NmapScanner:
        network:                    # <type: string; is: required>
        netmask:                    # <default: '/24'; type: string; is: optional>
        ports:                      # <default: None; type: None||string; is: optional>
        arguments:                  # <default: '-O -F --osscan-limit'; type: string; is: optional>
        interval:                   # <default: 900; type: integer; is: optional>
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
        channel:                    # <type: string; is: required>
        server:                     # <default: 'localhost'; type: string; is: optional>
        port:                       # <default: 6379; type: integer; is: optional>
        db:                         # <default: 0; type: integer; is: optional>
        password:                   # <default: None; type: None||string; is: optional>
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
        lists:                    # <type: list; is: required>
        server:                   # <default: 'localhost'; type: string; is: optional>
        port:                     # <default: 6379; type: integer; is: optional>
        batch_size:               # <default: 1; type: integer; is: optional>
        db:                       # <default: 0; type: integer; is: optional>
        password:                 # <default: None; type: None||string; is: optional>
        timeout:                  # <default: 0; type: integer; is: optional>
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
        interface:              # <default: 'any'; type: None||string; is: optional>
        packetfilter:           # <default: None; type: None||string; is: optional>
        promiscous:             # <default: False; type: boolean; is: optional>
        key_value_store:        # <default: None; type: none||string; is: optional>
        receivers:
          - NextModule


Spam
----

Emits events as fast as possible.

Use this module to load test GambolPutty. Also nice for testing your regexes.

The event field can either be a simple string. This string will be used to create a default gambolputty event dict.
If you want to provide more custom fields, you can provide a dictionary containing at least a "data" field that
should your raw event string.

| **event**:  Send custom event data. To send a more complex event provide a dict, use a string to send a simple event.
| **sleep**:  Time to wait between sending events.
| **events_count**:  Only send configured number of events. 0 means no limit.

Configuration template:

::

    - Spam:
        event:                    # <default: ""; type: string||dict; is: optional>
        sleep:                    # <default: 0; type: int||float; is: optional>
        events_count:             # <default: 0; type: int; is: optional>
        receivers:
          - NextModule


StdIn
-----

Reads data from stdin and sends it to its output queues.

Configuration template:

::

    - StdIn:
        multiline:                     # <default: False; type: boolean; is: optional>
        stream_end_signal:             # <default: False; type: boolean||string; is: optional>
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

Configuration template:

::

    - UdpServer:
        ipaddress:                       # <default: ''; type: string; is: optional>
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
        path_to_socket:         # <type: string; is: required>
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
        mode:                       # <default: 'server'; type: string; values: ['server', 'client']; is: optional>
        address:                    # <default: '*:5570'; type: string; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        hwm:                        # <default: None; type: None||integer; is: optional>
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
        mode:                       # <default: 'server'; type: string; values: ['server', 'client']; is: optional>
        address:                    # <default: '*:5570'; type: string; is: optional>
        pattern:                    # <default: 'pull'; type: string; values: ['pull', 'sub']; is: optional>
        topic:                      # <default: ''; type: string; is: optional>
        separator:                  # <default: None; type: None||string; is: optional>
        hwm:                        # <default: None; type: None||integer; is: optional>
        receivers:
          - NextModule