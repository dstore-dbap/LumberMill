#!/bin/bash
# Check the lumberjack and es service.
# This is done by requesting all logged entries from the last
# five minutes. If this times out or the entry count is below 
# MIN_REQUIERED_QUERY_HITS both services will be (re)started.
MIN_REQUIERED_QUERY_HITS=1

function logMessage {
	echo $(date)": "$1
}

NUM_FOUND=$(curl --connect-timeout 2 -m 20 -s -XPOST 'http://es-01.dbap.de:9200/logstash*/_search' -d '{ "size": 0, "query": { "query_string": { "query": "@timestamp:[now-1m TO now]" } } }'|egrep -o '"hits":."total":[0-9]+')
if [ "$NUM_FOUND" == "" ]; then
	logMessage "ElasticSearch did not return an answer to the status query. Restarting ElasticSearch and LumberJack services."
	/etc/init.d/elasticsearch restart
	sleep 5
	/etc/init.d/lumberjack restart
	exit 255
fi
QUERY_HITS=$(echo $NUM_FOUND|egrep -o '[0-9]+')
if [ $QUERY_HITS -lt $MIN_REQUIERED_QUERY_HITS ]; then
	logMessage "ElasticSearch query hits of $QUERY_HITS below threshold of $MIN_REQUIERED_QUERY_HITS. Restarting ElasticSearch and LumberJack services."
	/etc/init.d/elasticsearch restart
	sleep 5
	/etc/init.d/lumberjack restart
	exit 255
fi
exit 0

