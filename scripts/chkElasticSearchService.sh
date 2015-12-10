#!/bin/bash
# Check the lumbermill and es service.
# This is done by requesting all logged entries from the last
# five minutes. If this times out or the entry count is below 
# MIN_REQUIERED_QUERY_HITS both services will be (re)started.
MIN_REQUIERED_QUERY_HITS=1
ES_HOST=es-01.dbap.de
IDXS_TO_CHECK="lumbermill* agora-access*"

function logMessage {
	echo $(date)": "$1
}

for IDX in $IDXS_TO_CHECK; do
    NUM_FOUND=$(curl --connect-timeout 2 -m 20 -s -XPOST 'http://'$ES_HOST':9200/'$IDX'/_search' -d '{ "size": 0, "query": { "query_string": { "query": "@timestamp:[now-1m TO now]" } } }'|egrep -o '"hits":."total":[0-9]+')
    if [ "$NUM_FOUND" == "" ]; then
        logMessage "ElasticSearch query did not return any data. Restarting elasticsearch services."
        /etc/init.d/elasticsearch restart
        exit 255
    fi
    QUERY_HITS=$(echo $NUM_FOUND|egrep -o '[0-9]+')
    if [ $QUERY_HITS -lt $MIN_REQUIERED_QUERY_HITS ]; then
        logMessage "ElasticSearch query hits of $QUERY_HITS below threshold of $MIN_REQUIERED_QUERY_HITS. Restarting logparsing services."
        /etc/init.d/lumbermill restart
        /etc/init.d/logstash restart
        exit 255
    fi
done
exit 0