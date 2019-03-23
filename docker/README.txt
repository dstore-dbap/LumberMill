To build docker image (execute this is the root folder of the LumberMill repository):
>docker build -f lumbermill/dockerfile -t lumbermill .

To start LumberMill docker container (execute this in the root folder of the LumberMill repository):
>sudo docker run -it --rm -p5151:5151 -v $(pwd):/opt/LumberMill/ lumbermill /opt/LumberMill/bin/lumbermill.pypy -c <path to configuration>

While developing, start container and get a shell:
>sudo docker run -it --rm -p5151:5151 -v $(pwd):/opt/LumberMill/ lumbermill /bin/bash

For running tests against services like mongodb or filebeat, use the docker-compose file:
>sudo docker-compose up

At the moment, this will start containers for:
 - lumbermill
 - elasticsearch
 - mongodb
 - filebeat
 - redis
