For local tests that need external services like elasticsearch or redis, I recommend using docker images.
The configuration, which

To install and use a redis docker container for running tests:
>docker pull redis
>docker run -d --rm --name redis -p 6379:6379 redis

To install and use an elasticsearch docker container for running tests:
>docker pull elasticsearch:7.16.2
>docker run --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:7.16.2
