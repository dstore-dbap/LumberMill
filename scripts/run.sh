#!/bin/bash
#cd /opt/LumberMill
HAS_PYPY=$(which pypy)
if [ $? -eq 0 ]; then
    bin/lumbermill.pypy -c $1
else
    bin/lumbermill -c $1
fi