#/bin/bash
# Remove entries from elasticsearch index older than --day-to-keep days.

/opt/GambolPutty/src/scripts/logstash_index_cleaner.py --host es-01.dbap.de --port 9200 --timeout 60 --prefix gambolputty- --days-to-keep 10
/opt/GambolPutty/src/scripts/logstash_index_cleaner.py --host es-01.dbap.de --port 9200 --timeout 60 --prefix logstash- --days-to-keep 10
/opt/GambolPutty/src/scripts/logstash_index_cleaner.py --host es-01.dbap.de --port 9200 --timeout 60 --prefix agora_access- --days-to-keep 10