GambolPutty
==========

A simple stream parser in python. To run GambolPutty you will need Python 2.5+.

To analyze i.e. log data, this tool offers a simple approach to parse the streams using regular expressions.

The different modules can be combined in any order. Each module runs in its own thread and data is passed 
via python queues between the running modules.

Running this with pypy instead of python increases performance noticeably! So be sure to run it via pypy.

Working modules:

* StdInHandler, read stream from standard in 
* TcpServerThreaded, read stream from a tcp socket  
* TcpServerTwisted, same as above but using python twisted
* RegexStringParser, parse a string using regular expressions and named capturing groups
* CSVParser, parse a char separated string
* JsonParser, parse a json formatted string
* AddDateTime, adds a timestamp field
* AddGeoInfo, adds geo info fields
* ModifyFields, some methods to change extracted fields, e.g. delete, replace, castToInteger etc.
* DevNullSink, discards all data that it receives
* StdOutHandler, prints all received data to standard out
* ElasticSearchStorageHandler, stores data entries in an elasticsearch index
* DataAggregator, aggregate a configurable number of data entries before passing them on (useful for bulk updates)
* ModuleContainer, wrap modules in a container reducing the overhead to run each module in it's own thread
* Statistics, simple statistic module

GambolPutty makes use of the following projects:

* simplejson
* pyyaml
* pygeoip

### Example usage

#####Simple example to get you started ;)

	echo '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395' | python GambolPutty.pyy -c ./conf/lumberjack.conf.stdin-example

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

#####A rough sketch for using GambolPutty with syslog-ng:

Send e.g. apache access logs to syslog (/etc/httpd/conf/httpd.conf):

	...
	CustomLog "| /usr/bin/logger -p local1.info -t apache2" common
	...

	
Configure the linux syslog-ng service to send data to a tcp address (/etc/syslog-ng.conf):

	...
	destination d_lumberjack { tcp( localhost port(5151) ); };
	filter f_httpd_access { facility(local1); };
	log { source(s_sys); filter(f_httpd_access); destination(d_lumberjack); flags(final);};
	...	

Configure GambolPutty to listen on localhost 5151(./conf/lumberjack.conf):

	...
	- module: TcpServerThreaded
	  configuration:
        interface: localhost
        port: 5151
	...