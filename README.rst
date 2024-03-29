.. image:: https://readthedocs.org/projects/lumbermill/badge/?version=latest
   :target: http://lumbermill.readthedocs.org/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: https://travis-ci.org/dstore-dbap/LumberMill.svg?branch=master
   :target: https://travis-ci.org/dstore-dbap/LumberMill
.. image:: https://coveralls.io/repos/github/dstore-dbap/GambolPutty/badge.svg?branch=master
   :target: https://coveralls.io/github/dstore-dbap/GambolPutty?branch=master

LumberMill
===========

Introduction
''''''''''''

Collect, parse and store logs with a configurable set of modules.
Inspired by `logstash <https://github.com/elasticsearch/logstash>`_ but
with a smaller memory footprint and faster startup time. Can also run
multiprocessed to avoid `GIL <http://www.dabeaz.com/GIL/>`_ related restrictions.

Compatibility and Performance
'''''''''''''''''''''''''''''
To run LumberMill you will need Python 3.2+. For Python 2 support, please use an older version of this tool.
For better performance, I heartly recommend running LumberMill with pypy.
The performance gain can be up to 5-6 times events/s throughput running single processed.

Installation
''''''''''''

**via pypi**

::

   pip install LumberMill

**manually**

Clone the github repository to /opt/LumberMill (or any other location that fits you better :):

::

     git clone https://github.com/dstore-dbap/LumberMill.git /opt/LumberMill

Install the dependencies with pip:

::

     cd /opt/LumberMill
     python setup.py install

You may need the MaxMind geo database. Install it with:

::

    mkdir /usr/share/GeoIP
    cd /usr/share/GeoIP
    wget "http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz"
    gunzip GeoLiteCity.dat.gz

Now you can give LumberMill a testdrive with:

::

    wget https://raw.githubusercontent.com/dstore-dbap/LumberMill/master/conf/example-stdin.conf
    echo "I'm a lumberjack, and I'm okay" | bin/lumbermill -c conf/example-stdin.conf

If you get a "command not found" please check your pythonpath setting. Depending on how you installed LumberMill,
the executable can either be found in the bin dir of your python environment (e.g. /usr/lib64/pypy-2.4.0/bin/lumbermill)
or in your default path (e.g. /usr/local/bin/lumbermill).

Other basic configuration examples: https://github.com/dstore-dbap/LumberMill/tree/master/conf/.

For a how-to running LumberMill, Elasticsearch and Kibana on CentOS, feel free to visit
http://www.netprojects.de/collect-visualize-your-logs-with-lumbermill-and-elasticsearch-on-centos/.

Working modules
'''''''''''''''

Event inputs
^^^^^^^^^^^^

-  Beats, read elastic beat inputs, e.g. filebeat.
-  ElasticSearch, get documents from elasticsearch.
-  File, read data from files.
-  Kafka, receive events from apache kafka.
-  NmapScanner, scan network with nmap and emit result as new event.
-  RedisChannel, read events from redis channels.
-  RedisList, read events from redis lists.
-  Sniffer, sniff network traffic.
-  Spam, what it says on the can - spams LumberMill for testing.
-  SQS, read messages from amazons simple queue service.
-  StdIn, read stream from standard in.
-  Tcp, read stream from a tcp socket.
-  Udp, read data from udp socket.
-  UnixSocket, read stream from a named socket on unix like systems.
-  ZeroMQ, read events from a zeromq.

Event parsers
^^^^^^^^^^^^^

-  Base64, parse base64 data.
-  Collectd, parse collectd binary protocol data.
-  CSV, parse a char separated string.
-  DateTime, parse a string to a dateobject and convert it to different date pattern.
-  DomainName, parse a domain name or url to tld, subdomain etc. parts.
-  Inflate, inflates any fields with supported compression codecs.
-  Json, parse a json formatted string.
-  Line, split lines at a seperator and emit each line as new
   event.
-  MsgPack, parse a msgpack encoded string.
-  Regex, parse a string using regular expressions and named
   capturing groups.
-  SyslogPrival, parse the syslog prival value (RFC5424).
-  Url, parse the query string from an url.
-  UserAgent, parse a http user agent string.
-  XPath, parse an XML document via an xpath expression.

Event modifiers
^^^^^^^^^^^^^^^

-  AddDateTime, adds a timestamp field.
-  AddDnsLookup. adds dns data.
-  AddGeoInfo, adds geo info fields.
-  DropEvent, discards event.
-  ExecPython, execute custom python code.
-  Facet, collect all encountered variations of en event value over a
   configurable period of time.
-  HttpRequest, execute an arbritrary http request and store result.
-  Math, execute arbitrary math functions.
-  MergeEvent, merge multiple events to one single event.
-  Field, some methods to change extracted fields, e.g. insert,
   delete, replace, castToInteger etc.
-  Permutate, takes a list in the event data emits events for all
   possible permutations of that list.

Outputs
^^^^^^^

-  DevNull, discards all data that it receives.
-  ElasticSearch, stores data entries in an elasticsearch index.
-  File, store events in a file.
-  Graphite, send metrics to graphite server.
-  Kafka, publish incoming events to kafka topic.
-  Logger, sends data to lumbermill internal logger for output.
-  MongoDb, stores data entries in a mongodb index.
-  RedisChannel, publish incoming events to redis channel.
-  RedisList, publish incoming events to redis list.
-  StdOut, prints all received data to standard out.
-  SQS, sends events to amazons simple queue service.
-  Syslog, send events to syslog.
-  Udp, send events to udp server.
-  WebHdfs, store events in hdfs via webhdfs.
-  Zabbix, send metrics to zabbix.
-  Zmq, sends incoming event to zeromq.

Misc modules
^^^^^^^^^^^^

-  EventBuffer, store received events in a persistent backend until the
   event was successfully handled.
-  Cache, use cache to store and retrieve values, e.g. to store the
   result of the XPathParser modul.
-  SimpleStats, simple statistic module just for event rates etc.
-  Metrics, Configurable fields for different metric data.
-  Tarpit, slows event propagation down - for testing.
-  Throttle, throttle event count over a given time period.

Cluster modules
^^^^^^^^^^^^^^^

-  Pack, base pack module. Handles pack leader and pack member
   discovery.
-  PackConfiguration, syncs leader configuration to pack members.

Plugins
^^^^^^^

-  WebGui, a web interface to LumberMill.
-  WebserverTornado, base webserver module. Handles all incoming
   requests.

Event flow basics
'''''''''''''''''

-  an input module receives an event.
-  the event data will be wrapped in a default event dictionary of the
   following structure: { "data": payload, "lumbermill": { "event\_id":
   unique event id, "event\_type": "Unknown", "received\_from": ip
   address of sender, "source\_module": caller\_class\_name, } }
-  the input module sends the new event to its receivers. Either by
   adding it to a queue or by calling the receivers handleEvent method.
-  if no receivers are configured, the next module in config will be the
   default receiver.
-  each following module will process the event via its handleEvent
   method and pass it on to its receivers.
-  each module can have an input filter and an output filter to manage
   event propagation through the modules.
-  output modules can not have receivers.

Configuration example (with explanations)
'''''''''''''''''''''''''''''''''''''''''

To give a short introduction of how LumberMill works, here is a sample
configuration.
Its receiving apache and nginx access logs via syslog messages from a
syslog server and msgpacked events from
`python-beaver <https://github.com/josegonzalez/python-beaver>`_ and
stores them in an elasticsearch backend.
Below, I will explain each section in more detail.

::

    # Sets number of parallel LumberMill processes.
    - Global:
       workers: 2

    # Listen on all interfaces, port 5151.
    - input.Tcp:
       port: 5151
       receivers:
        - RegexParser

    # Listen on all interfaces, port 5152.
    - input.Tcp:
       port: 5152
       mode: stream
       chunksize: 32768

    # Decode msgpacked data.
    - parser.MsgPack:
       mode: stream

    # Extract fields.
    - parser.RegexParser:
       source_field: data
       hot_rules_first: True
       field_extraction_patterns:
        - httpd_access_log: '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'
        - http_common_access_log: '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s(?P<x_forwarded_for>\d+\.\d+\.\d+\.\d+)\s(?P<identd>\w+|-)\s(?P<user>\w+|-)\s\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s\"(?P<url>.*)\"\s(?P<http_status>\d+)\s(?P<bytes_send>\d+)'
        - iptables: '(?P<syslog_prival>\<\d+\>)(?P<log_timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+(?P<host>[\w\-\._]+)\s+kernel:.*?\ iptables\ (?P<iptables_action>.*?)\ :\ IN=(?P<iptables_in_int>.*?)\ OUT=(?P<iptables_out_int>.*?)\ SRC=(?P<iptables_src>.*?)\ DST=(?P<iptables_dst>.*?)\ LEN=(?P<iptables_len>.*?)\ .*?PROTO=(?P<iptables_proto>.*?)\ SPT=(?P<iptables_spt>.*?)\ DPT=(?P<iptables_dpt>.*?)\ WINDOW=.*'
       receivers:
        - misc.SimpleStats:
           filter: $(lumbermill.event_type) != 'Unknown'
        # Print out messages that did not match
        - output.StdOut:
           filter: $(lumbermill.event_type) == 'Unknown'

    # Print out some stats every 10 seconds.
    - misc.SimpleStats:
       interval: 10

    # Extract the syslog prival from events received via syslog.
    - parser.SyslogPrival:
       source_field: syslog_prival

    # Add a timestamp field.
    - modifier.AddDateTime:
       format: '%Y-%m-%dT%H:%M:%S.%f'
       target_field: "@timestamp"

    # Add geo info based on the lookup_fields. The first field in <source_fields> that yields a result from geoip will be used.
    - modifier.AddGeoInfo:
       geoip_dat_path: /usr/share/GeoIP/GeoLiteCity.dat
       source_fields: [x_forwarded_for, remote_ip]
       geo_info_fields: ['latitude', 'longitude', 'country_code']

    # Nginx logs request time in seconds with milliseconds as float. Apache logs microseconds as int.
    # At least cast nginx to integer.
    - modifier.Math:
       filter: if $(server_type) == "nginx"
       target_field: request_time
       function: float($(request_time)) * 1000

    # Map field values of <source_field> to values in <map>.
    - modifier.Field:
       filter: if $(http_status)
       action: map
       source_field: http_status
       map: {100: 'Continue', 200: 'OK', 301: 'Moved Permanently', 302: 'Found', 304: 'Not Modified', 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 500: 'Internal Server Error', 502: 'Bad Gateway'}

    # Kibana’s ‘bettermap’ panel needs an array of floats in order to plot events on map.
    - modifier.Field:
       filter: if $(latitude)
       action: merge
       source_fields: [longitude, latitude]
       target_field: geoip

    # Extarct some fields from the user agent data.
    - parser.UserAgent:
       source_fields: user_agent

    # Parse the url into its components.
    - parser.Url:
       source_field: uri
       target_field: uri_parsed
       parse_querystring: True
       querystring_target_field: params

    # Store events in elastic search.
    - output.ElasticSearch:
       nodes: [localhost]
       store_interval_in_secs: 5

    - output.StdOut

Let me explain it in more detail:

::

    # Sets number of parallel LumberMill processes.
    - Global:
       workers: 2

The Global section lets you configure some global properties of
LumberMill. Here the number of parallel processes is set. In order to
be able to use multiple cores with python (yay to the
`GIL <http://www.dabeaz.com/GIL/>`_) LumberMill can be started with
multiple parallel processes.
Default number of workers is CPU\_COUNT - 1.

::

    # Listen on all interfaces, port 5151.
    - input.Tcp:
       port: 5151
       receivers:
        - RegexParser

Starts a tcp server listening on all local interfaces port 5151. Each
module comes with a set of default values, so you only need to provide
settings you need to customize.
For a description of the default values of a module, refer to the
README.md in the modules directory or its docstring.
By default, a module will send its output to the next module in the
configuration. To set a custom receiver, set the receivers value.
This module will send its output directly to RegexParser.

::

    # Listen on all interfaces, port 5152.
    - input.Tcp:
       port: 5152
       mode: stream
       chunksize: 32768

Also starts a tcp server, listening on port 5152. The first tcp server
uses newline as separator (which is the default) for each received
event.
Here, the sever reads in max. 32k of data and passes this on to the next
module.

::

    # Decode msgpacked data.
    - parser.MsgPack:
       mode: stream

Decode the received data from the above tcp server in msgpack format.
This can be used to e.g. handle data send via
`python-beaver <https://github.com/josegonzalez/python-beaver>`_

::

    # Extract fields.
    - parser.Regex:
       source_field: data
       hot_rules_first: True
       field_extraction_patterns:
        - httpd_access_log: '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s+(?P<identd>\w+|-)\s+(?P<user>\w+|-)\s+\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s+\"(?P<url>.*)\"\s+(?P<http_status>\d+)\s+(?P<bytes_send>\d+)'
        - http_common_access_log: '(?P<remote_ip>\d+\.\d+\.\d+\.\d+)\s(?P<x_forwarded_for>\d+\.\d+\.\d+\.\d+)\s(?P<identd>\w+|-)\s(?P<user>\w+|-)\s\[(?P<datetime>\d+\/\w+\/\d+:\d+:\d+:\d+\s.\d+)\]\s\"(?P<url>.*)\"\s(?P<http_status>\d+)\s(?P<bytes_send>\d+)'
        - iptables: '(?P<syslog_prival>\<\d+\>)(?P<log_timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+(?P<host>[\w\-\._]+)\s+kernel:.*?\ iptables\ (?P<iptables_action>.*?)\ :\ IN=(?P<iptables_in_int>.*?)\ OUT=(?P<iptables_out_int>.*?)\ SRC=(?P<iptables_src>.*?)\ DST=(?P<iptables_dst>.*?)\ LEN=(?P<iptables_len>.*?)\ .*?PROTO=(?P<iptables_proto>.*?)\ SPT=(?P<iptables_spt>.*?)\ DPT=(?P<iptables_dpt>.*?)\ WINDOW=.*'
       receivers:
        - misc.SimpleStats:
           filter: $(lumbermill.event_type) != 'Unknown'
        # Print out messages that did not match
        - output.StdOut:
           filter: $(lumbermill.event_type) == 'Unknown'

Use regular expressions to extract fields from a log event.
source\_field sets the field to apply the regex to.
With hot\_rules\_first set to True, the expressions will be applied in
order of their hit counts.
httpd\_access\_log will set the event type to "httpd\_access\_log" if
the expression matches.
Named groups are used to set the field names. Grok patterns from
Logstash can also be used.
In the receivers section, we can find output filters. These can be used
to only send selected events to the receiving module.
As to the notation of event fields in such filters, please refer to the
"Event field notation" section later in this document.
In this example the output filter uses the event metadata lumbermill
field. This data is set by LumberMill for every event received and
would look like this:

::

       'lumbermill': {'event_id': '90818a85f3aa3af302390bbe77fbc1c87800',
                       'event_type': 'Unknown',
                       'pid': 7800,
                       'received_by': 'vagrant-centos65.vagrantup.com',
                       'received_from': '127.0.0.1:61430',
                       'source_module': 'TcpServer'}}

This data is stored in a separate field to make it easier to drop it
prior to store it in some backend.

::

    # Print out some stats every 10 seconds.
    - misc.SimpleStats:
       interval: 10

Prints out some simple stats every interval seconds.

::

    # Extract the syslog prival from events received via syslog.
    - parser.SyslogPrivalParser:
       source_field: syslog_prival

Parses syslog prival values to human readable ones based on
`RFC5424 <http://tools.ietf.org/html/rfc5424>`_.

::

    # Add a timestamp field.
    - parser.AddDateTime:
       format: '%Y-%m-%dT%H:%M:%S.%f'
       target_field: "@timestamp"

Adds a timestamp field to the event. When you want to use kibana to view
your event data, this field is required.

::

    # Add geo info based on the lookup_fields. The first field in <source_fields> that yields a result from geoip will be used.
    - parser.AddGeoInfo:
       geoip_dat_path: /usr/share/GeoIP/GeoLiteCity.dat
       source_fields: [x_forwarded_for, remote_ip]
       geo_info_fields: ['latitude', 'longitude', 'country_code']

Adds geo information fields to the event based on ip addresses found in
source\_fields. The first ip address in source\_fields that yields a
result will be used.

::

    # Nginx logs request time in seconds with milliseconds as float. Apache logs microseconds as int.
    # At least cast nginx to integer.
    - parser.Math:
       filter: if $(server_type) == "nginx"
       target_field: request_time
       function: float($(request_time)) * 1000

As it says in the comment. Nginx and apache use different time formats
for the request time field. This module lets you adjust the field to
accommodate for that.
Also an input filter is used here. Only matching events will be modified
by this module.

::

    # Map field values of <source_field> to values in <map>.
    - modifier.Field:
       filter: if $(http_status)
       action: map
       source_field: http_status
       map: {100: 'Continue', 200: 'OK', 301: 'Moved Permanently', 302: 'Found', 304: 'Not Modified', 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 500: 'Internal Server Error', 502: 'Bad Gateway'}

This module shows how you can map event fields to new values. In this
example numeric http status codes are mapped to human readable values.

::

    # Kibana’s ‘bettermap’ panel needs an array of floats in order to plot events on map.
    - modifier.Field:
       filter: if $(latitude)
       action: merge
       source_fields: [longitude, latitude]
       target_field: geoip

Kibanas bettermap module expects the geodata to be found in one single
field. With this module the fields longitude and latitude are merged
into the geoip field.

::

    # Extarct some fields from the user agent data.
    - parser.UserAgent:
       source_fields: user_agent
       target_field: user_agent_info

Extract user agent information from the user\_agent field. This module
will set fields like user\_agent\_info.bot,
user\_agent\_info.browser.name etc.

::

    # Parse the url into its components.
    - parser.Url:
       source_field: uri
       target_field: uri_parsed
       parse_querystring: True
       querystring_target_field: params

Extract details from the uri field. This module will set fields like
uri\_parsed.scheme, uri\_parsed.path, uri\_parsed.query etc.

::

    # Store events in elastic search.
    - output.ElasticSearch:
       nodes: [localhost]
       store_interval_in_secs: 5

Send the received events to elasticsearch servers. nodes will set the
nodes to connect to.

::

    - output.StdOut

Events received by this module will be printed out to stdout. The
RegexParser module was configured to send unmatched events to this
module.

The different modules can be combined in any order.

To run LumberMill you will need Python 2.5+.
For better performance I recommend running LumberMill with pypy. Tested
with pypy-2.0.2, pypy-2.2.1, pypy-2.3 and pypy-2.4.
For IPC ZeroMq is used instead of the default multiprocessing.Queue.
This resulted in nearly 3 times of the performance with
multiprocessing.Queue.

Configuration basics
''''''''''''''''''''

The configuration is stored in a yaml formatted file. Each module
configuration follows the same pattern:

::

    - category.SomeModuleName:
        id: AliasModuleName                     # <default: ""; type: string; is: optional>
        filter: if $(cache_status) == "-"
        add_fields: {'my_new_field': 'my_new_value'}
        delete_fields: ['drop_this_field', 'drop_that_field']
        event_type: my_custom_type
        receivers:
         - ModuleName
         - ModuleAlias:
             filter: if $('event_type') == 'httpd_access_log'

-  module: specifies the module name and maps to the class name of the
   module.
-  id: use to set an alias name if you run more than just one instance
   of a module.
-  filter: apply a filter to incoming events. Only matching events will
   be handled by this module.
-  add\_fields: if the event is handled by the module add this fields to
   the event.
-  delete\_fields: if the event is handled by the module delete this
   fields from the event.
-  event\_type: if the event is handled by the module set event\_type to
   this value.
-  receivers: ModuleName or id of the receiving modules. If a filter is
   provided, only matching events will be send to receiver. If no
   receivers are configured, the next module in config will be the
   default receiver.

For modules that support the storage of intermediate values in redis: \*
configuration['redis-client']: name of the redis client as set in the
configuration. \* configuration['redis-key']: key used to store the data
in redis. \* configuration['redis-ttl']: ttl of the stored data in
redis.

For configuration details of each module refer to its docstring.

Event field notation
''''''''''''''''''''

The following examples refer to this event data:

::

    {'bytes_send': '3395',
     'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0" 200 3395\n',
     'datetime': '28/Jul/2006:10:27:10 -0300',
     'lumbermill': {
                    'event_id': '715bd321b1016a442bf046682722c78e',
                    'event_type': 'httpd_access_log',
                    "received_from": '127.0.0.1',
                    "source_module": 'StdIn',
      },
     'http_status': '200',
     'identd': '-',
     'remote_ip': '192.168.2.20',
     'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
     'fields': ['nobody', 'expects', 'the'],
     'params':  { u'spanish': [u'inquisition']},
     'user': '-'}

Notation in configuration fields like source\_field or target\_field
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just use the field name. If referring to a nested dict or a list, use
dots:

::

    - parser.Regex:
        source_field: fields.2

    - parser.Regex:
        source_field: params.spanish

Notation in strings
^^^^^^^^^^^^^^^^^^^

Use $(variable\_name) notation. If referring to a nested dict or a list,
use dots:

::

    - output.ElasticSearch:
        index_name: 1perftests
        doc_id: $(fields.0)-$(params.spanish.0)

Notation in module filters
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use $(variable\_name) notation. If referring to a nested dict, use dots:

::

    - output.StdOut:
        filter: if $(fields.0) == "nobody" and $(params.spanish.0) == 'inquisition'

Filters
-------

Modules can have an input filter:

::

    - output.StdOut:
        filter: if $(remote_ip) == '192.168.2.20' and re.match('^GET', $(url))

Modules can have an output filter:

::

    - parser.Regex:
        ...
        receivers:
          - output.StdOut:
              filter: if $(remote_ip) == '192.168.2.20' and $(hostname).startswith("www.")



A rough sketch for using LumberMill with syslog-ng
'''''''''''''''''''''''''''''''''''''''''''''''''''

Send e.g. apache access logs to syslog (/etc/httpd/conf/httpd.conf):

::

    ...
    CustomLog "| /usr/bin/logger -p local1.info -t apache2" common
    ...

Configure the linux syslog-ng service to send data to a tcp address
(/etc/syslog-ng.conf):

::

    ...
    destination d_lumbermill { tcp( localhost port(5151) ); };
    filter f_httpd_access { facility(local1); };
    log { source(s_sys); filter(f_httpd_access); destination(d_lumbermill); flags(final);};
    ... 

Configure LumberMill to listen on localhost
5151(./conf/lumbermill.conf):

::

    ...
    - input.Tcp:
        interface: localhost
        port: 5151
    ...

Work in progress.
