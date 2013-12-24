#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tcp_socket_throughput.py
#  TCP Socket Connection Throughput Tester
#  Corey Goldberg (www.goldb.org), 2008

import sys
import time
import socket
from ctypes import c_int, c_bool
from multiprocessing import Process, Value, Lock
import logging
import logging.handlers
import os
import random

#host = sys.argv[1]
#port = int(sys.argv[2]) if len(sys.argv) == 3 else 6379

process_count = 5  # concurrent sender agents

counter_lock = Lock()
def increment(counter):
    with counter_lock:
        counter.value += 1

def reset(counter):
    with counter_lock:
        counter.value = 0

class Controller:
    def __init__(self):
        self.count_ref = Value(c_int)

    def start(self):
        for i in range(process_count):
            agent = Agent(self.count_ref)
            agent.start()
        print 'started %d threads' % (i + 1)
        while self.count_ref.value > 0:
            line = 'connects/sec: %s' % self.count_ref.value
            reset(self.count_ref)
            print chr(0x08) * len(line)
            print line
            time.sleep(1)

class Agent(Process):
    def __init__(self, count_ref):
        Process.__init__(self)
        self.daemon = True
        self.logger = logging.getLogger('MyLogger')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.handlers.SysLogHandler(address = '/dev/log')
        self.logger.addHandler(handler)
        self.count_ref = count_ref
        random.seed(os.getpid())

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for counter in xrange(0, 1000):
            try:
                rand = "%f-%04.3f" % (time.time(), random.random())
                message ='192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/%s HTTP/1.0" 200 3395' % rand
                self.logger.error(message)
                increment(self.count_ref)
                s.close()
                time.sleep(.01) #.0000001
            except:
                etype, evalue, etb = sys.exc_info()
                print 'Exception: %s, Error: %s.' % (etype, evalue)

if __name__ == '__main__':
    controller = Controller()
    controller.start()

