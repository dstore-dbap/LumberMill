GambolPutty
==========

Why is it that the world never remembered the name of Johann Gambolputty de von Ausfern- schplenden- schlitter- crasscrenbon- fried- digger- dingle- dangle- dongle- dungle- burstein- von- knacker- thrasher- apple- banger- horowitz- ticolensic- grander- knotty- spelltinkle- grandlich- grumblemeyer- spelterwasser- kurstlich- himbleeisen- bahnwagen- gutenabend- bitte- ein- nürnburger- bratwustle- gerspurten- mitz- weimache- luber- hundsfut- gumberaber- shönedanker- kalbsfleisch- mittler- aucher von Hautkopft of Ulm?

A simple stream parser in python. To run GambolPutty you will need Python 2.5+.

To analyze i.e. log data, this tool offers a simple approach to parse the streams using regular expressions.

The different modules can be combined in any order.

##### Working modules:

#### Event inputs

* StdInHandler, read stream from standard in
* TcpServerThreaded, read stream from a tcp socket
* TcpServerTornado, read stream from a tcp socket, faster on Linux
* Spam, what it says on the can - spams GambolPutty for testing.

#### Event parsers

* RegexParser, parse a string using regular expressions and named capturing groups
* CSVParser, parse a char separated string
* JsonParser, parse a json formatted string
* UrlParser, parse the query string from an url
* XPathParser, parse an XML document via an xpath expression

#### Field modifiers

* AddDateTime, adds a timestamp field
* AddGeoInfo, adds geo info fields
* ModifyFields, some methods to change extracted fields, e.g. insert, delete, replace, castToInteger etc.
* HttpRequest, execute an arbritrary http request and store result
* Permutate, takes a list in the event data emits events for all possible permutations of that list

#### Outputs
* DevNullSink, discards all data that it receives
* StdOutHandler, prints all received data to standard out
* ElasticSearchOutput, stores data entries in an elasticsearch index

#### Misc modules

* RedisClient, use redis to store and retrieve values, e.g. to store the result of the XPathParser modul
* Facet, collect all encountered variations of en event value over a configurable presiod of time
* Statistics, simple statistic module
* Tarpit, slows event propagation down - for testing.

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
* each following module will process the event via its handleEvent method and pass it on to its
  receivers.

### Configuration basics

The configuration is stored in a yaml formatted file.
Each module configuration follows the same pattern:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      configuration:
        work-on-copy: True                      # <default: False; type: boolean; is: optional>
        redis-client: RedisClientName           # <default: ""; type: string; is: optional>
        redis-key: XPathParser%(server_name)s   # <default: ""; type: string; is: optional>
        redis-ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
       - ModuleName
       - ModuleAlias:
           filter: event_type == 'httpd_access_log'

* module: specifies the module name and maps to the class name of the module.
* alias: use to set an alias name if you run more than just one instance of a module.
* configuration['work-on-copy']: create a copy of the default event dictionary and pass this on to following modules
* receivers: ModuleName or ModuleAlias of the receiving modules. If a filter is provided, only matching events will be send to receiver.

for modules that support the storage of intermediate values in redis:
* configuration['redis-client']: name of the redis client as set in the configuration.
* configuration['redis-key']: key used to store the data in redis.
* configuration['redis-ttl']: ttl of the stored data in redis.

For configuration details of each module refer to its docstring.

### Example usage

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

For a more complex configuration refer to the gambolputty.example configuration file in the conf folder.

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
	- module: TcpServerThreaded
	  configuration:
        interface: localhost
        port: 5151
	...