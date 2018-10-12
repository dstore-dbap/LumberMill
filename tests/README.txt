For local tests that need external services like elasticsearch or redis, I recommend using docker images.
The configuration, which

To install and use a redis docker container for running tests:
>docker pull redis
>docker run -d --rm --name redis -p 6379:6379 redis

To install and use an elasticsearch docker container for running tests:
>docker pull elasticsearch
>docker run -d --rm --name elasticsearch -p 9200:9200 elasticsearch

To install and use an elasticsearch docker container for running tests:
>docker pull elasticsearch
>docker run -d --rm --name elasticsearch -p 9200:9200 elasticsearch
