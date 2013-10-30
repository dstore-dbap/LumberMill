GambolPutty
==========

A simple stream parser in python. To run GambolPutty you will need Python 2.5+.

To analyze i.e. log data, this tool offers a simple approach to parse the streams using regular expressions.

The different modules can be combined in any order. Each module runs in its own thread and data is passed 
via python queues between the running modules.

Running this with pypy instead of python increases performance noticeably! So be sure to run it via pypy.

##### Working modules:

#### Event inputs

* StdInHandler, read stream from standard in 
* TcpServerThreaded, read stream from a tcp socket

#### Event parsers

* RegexParser, parse a string using regular expressions and named capturing groups
* CSVParser, parse a char separated string
* JsonParser, parse a json formatted string
* UrlParser, parse the query string from an url
* XPathParser, parse an XML document via an xpath expression

#### Field modifiers

* AddDateTime, adds a timestamp field
* AddGeoInfo, adds geo info fields
* ModifyFields, some methods to change extracted fields, e.g. delete, replace, castToInteger etc.
* HttpRequest, execute an arbritrary http request and store result

#### Outputs
* DevNullSink, discards all data that it receives
* StdOutHandler, prints all received data to standard out
* ElasticSearchOutput, stores data entries in an elasticsearch index

#### Misc modules

* ModuleContainer, wrap modules in a container reducing the overhead to run each module in it's own thread
* RedisClient, use redis to store and retrieve values, e.g. to store the result of the XPathParser modul
* Statistics, simple statistic module

GambolPutty makes use of the following projects:

* https://pypi.python.org/pypi/simplejson
* https://bitbucket.org/xi/pyyaml
* https://pypi.python.org/pypi/pygeoip/
* https://pypi.python.org/pypi/elasticsearch/

### Event flow basics

* an input module receives an event.
* the event data will be wrapped in a default event dictionary of the following structure:
    { "received_from": False, "data": received event, "markers": [] }
* the input module adds the default event dictionary to its output queues as configured in the config file.
* each following module will read from its input queue and adds the result to its output queues.

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