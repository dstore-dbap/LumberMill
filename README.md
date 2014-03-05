GambolPutty
==========

Why is it that the world never remembered the name of Johann Gambolputty de von Ausfern- schplenden- schlitter- crasscrenbon- fried- digger- dingle- dangle- dongle- dungle- burstein- von- knacker- thrasher- apple- banger- horowitz- ticolensic- grander- knotty- spelltinkle- grandlich- grumblemeyer- spelterwasser- kurstlich- himbleeisen- bahnwagen- gutenabend- bitte- ein- nürnburger- bratwustle- gerspurten- mitz- weimache- luber- hundsfut- gumberaber- shönedanker- kalbsfleisch- mittler- aucher von Hautkopft of Ulm?

A simple log message manager in python. To run GambolPutty you will need Python 2.5+.

To analyze i.e. log data, this tool offers a simple approach to parse the streams using regular expressions.

The different modules can be combined in any order.

##### Working modules:

#### Event inputs

* RedisChannel, read events from redis channels.
* RedisList, read events from redis lists.
* Spam, what it says on the can - spams GambolPutty for testing.
* StdInHandler, read stream from standard in.
* TcpServerThreaded, read stream from a tcp socket.
* TcpServerTornado, read stream from a tcp socket, faster on Linux.
* UnixSocket, read stream from a named socket on unix like systems.
* Zmq, read events from a zeromq.

#### Event parsers

* CSVParser, parse a char separated string.
* JsonParser, parse a json formatted string.
* LineParser, split lines at a seperator and emit each line as new event.
* MsgPackParser, parse a msgpack encoded string.
* RegexParser, parse a string using regular expressions and named capturing groups.
* SyslogPrivalParser, parse the syslog prival value (RFC5424).
* UrlParser, parse the query string from an url.
* XPathParser, parse an XML document via an xpath expression.

#### Field modifiers

* AddDateTime, adds a timestamp field.
* AddGeoInfo, adds geo info fields.
* HttpRequest, execute an arbritrary http request and store result.
* ModifyFields, some methods to change extracted fields, e.g. insert, delete, replace, castToInteger etc.
* Permutate, takes a list in the event data emits events for all possible permutations of that list.

#### Outputs

* DevNullSink, discards all data that it receives.
* ElasticSearchSink, stores data entries in an elasticsearch index.
* ElasticSearchMultiProcessSink, same as above but multiprocessed.
* FileSink, store events in a file.
* RedisChannelSink, publish incoming events to redis channel.
* StdOutSink, prints all received data to standard out.
* SyslogSink, send events to syslog.
* WebHdfsSink, store events in hdfs via webhdfs.

#### Misc modules

* ExecPython, execute custom python code.
* Facet, collect all encountered variations of en event value over a configurable period of time.
* RedisClient, use redis to store and retrieve values, e.g. to store the result of the XPathParser modul.
* Statistics, simple statistic module.
* TrackEvents, keep track of events being processed and requeue them after e.g. a crash.
* Tarpit, slows event propagation down - for testing.

#### Cluster modules
* Cluster, base cluster module. Handles pack leader and pack member discovery.
* ClusterConfiguration, syncs leader configuration to pack members.

#### Webserver modules
* WebGui, a web interface to GambolPutty.
* WebserverTornado, base webserver module. Handles all incoming requests.

GambolPutty makes use of the following projects:

* https://pypi.python.org/pypi/simplejson
* https://bitbucket.org/xi/pyyaml
* https://pypi.python.org/pypi/pygeoip/
* https://pypi.python.org/pypi/elasticsearch/

### Event flow basics
* an input module receives an event.
* the event data will be wrapped in a default event dictionary of the following structure:
    { "event_type": "Unknown", "received_from": False, "data": "", "markers": [] }
* the input module sends the new event to its receivers. Either by adding it to a queue or by calling the
  receivers handleEvent method.
* if no receivers are configured, the next module in config will be the default receiver.
* each following module will process the event via its handleEvent method and pass it on to its
  receivers.

### Configuration basics

The configuration is stored in a yaml formatted file.
Each module configuration follows the same pattern:

    - SomeModuleName:
        id: AliasModuleName                     # <default: ""; type: string; is: optional>
        filter: if %(cache_status) == "-"
        redis-client: RedisClientName           # <default: ""; type: string; is: optional>
        redis-key: XPathParser%(server_name)s   # <default: ""; type: string; is: optional>
        redis-ttl: 600                          # <default: 60; type: integer; is: optional>
        receivers:
         - ModuleName
         - ModuleAlias:
             filter: if %('event_type') == 'httpd_access_log'

* module: specifies the module name and maps to the class name of the module.
* id: use to set an alias name if you run more than just one instance of a module.
* receivers: ModuleName or ModuleAlias of the receiving modules. If a filter is provided, only matching events will be send to receiver.
  If no receivers are configured, the next module in config will be the default receiver.

for modules that support the storage of intermediate values in redis:
* configuration['redis-client']: name of the redis client as set in the configuration.
* configuration['redis-key']: key used to store the data in redis.
* configuration['redis-ttl']: ttl of the stored data in redis.

For configuration details of each module refer to its docstring.

### Example usage

#### Event field notation

The following examples refer to this event data:

	{'bytes_send': '3395',
	 'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0" 200 3395\n',
	 'datetime': '28/Jul/2006:10:27:10 -0300',
	 'http_status': '200',
	 'identd': '-',
	 'message_type': 'httpd_access_log',
	 'received_from': 'stdin',
	 'remote_ip': '192.168.2.20',
	 'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
	 'fields': ['nobody', 'expects', 'the'],
	 'params':  { u'spanish': [u'inquisition']},
	 'user': '-'}

##### Notation in configuration fields like source_field or target_field:

Just use the field name. If referring to a nested dict or a list, use dots:

    - RegexParser:
        source_field: fields.2

    - RegexParser:
        source_field: params.spanish

##### Notation in strings:

Use the python % formatting for strings. If referring to a nested dict or a list, use dots:

    - ElasticSearchMultiProcessSink:
        index_name: 1perftests
        doc_id: '%(fields.0)s-%(params.spanish)s'

##### Notation in module filters:

Wrap the field name in %(field_name). If referring to a nested dict, use dots, like this:

    - StdOutSink:
        filter: if %(fields.0) == "nobody" and %(params.spanish) == '192.168.2.20'

#### Filter

Modules can have an input filter , like this:

    - StdOutSink:
        filter: if %(params.spanish) == '192.168.2.20' and re.match('^GET', %(url))

Modules can have an output filter , like this:

    - RegexParser:
        ...
        receivers:
          - StdOutSink:
              filter: if %(params.spanish) == '192.168.2.20' and re.match('^GET', %(url))

##### Simple example to get you started ;)

	echo '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395' | python GambolPutty.py -c ./conf/gambolputty.conf.stdin-example

This should produce the following output:

	{'bytes_send': '3395',
	 'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395\n',
	 'datetime': '28/Jul/2006:10:27:10 -0300',
	 'http_status': '200',
	 'identd': '-',
	 'markers': ['match'],
	 'message_type': 'httpd_access_log',
	 'received_from': 'stdin',
	 'remote_ip': '192.168.2.20',
	 'url': 'GET /cgi-bin/try/ HTTP/1.0',
	 'user': '-'}

For a more complex configuration refer to the gambolputty.conf.tcp-example configuration file in the conf folder.

For a small how-to running GambolPutty on CentOS, feel free to visit http://www.netprojects.de/collect-visualize-your-logs-with-gambolputty-and-elasticsearch-on-centos/.

##### A rough sketch for using GambolPutty with syslog-ng:

Send e.g. apache access logs to syslog (/etc/httpd/conf/httpd.conf):

	...
	CustomLog "| /usr/bin/logger -p local1.info -t apache2" common
	...

	
Configure the linux syslog-ng service to send data to a tcp address (/etc/syslog-ng.conf):

	...
	destination d_gambolputty { tcp( localhost port(5151) ); };
	filter f_httpd_access { facility(local1); };
	log { source(s_sys); filter(f_httpd_access); destination(d_gambolputty); flags(final);};
	...	

Configure GambolPutty to listen on localhost 5151(./conf/gambolputty.conf):

	...
	- TcpServerThreaded:
        interface: localhost
        port: 5151
	...