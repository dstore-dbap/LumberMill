# -*- coding: utf-8 -*-
import redis

#!/usr/bin/env python
#
#  tcp_socket_throughput.py
#  TCP Socket Connection Throughput Tester
#  Corey Goldberg (www.goldb.org), 2008

import sys
import time
import socket
from ctypes import c_int, c_bool
from multiprocessing import Process, Value, Lock


host = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv) == 3 else 6379

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
        self.alive = Value(c_bool)

    def start(self):
        self.alive = True
        for i in range(process_count):
            agent = Agent(self.count_ref, self.alive)
            agent.start()
        print 'started %d threads' % (i + 1)
        while self.alive:
            line = 'connects/sec: %s' % self.count_ref.value
            reset(self.count_ref)
            print chr(0x08) * len(line)
            print line
            time.sleep(1)

class Agent(Process):
    def __init__(self, count_ref, parent_alive):
        Process.__init__(self)
        self.daemon = True
        self.client = redis.Redis(host=host, port=port)
        self.count_ref = count_ref
        self.parent_alive = parent_alive

    def run(self):
        start = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        alive = True
        while alive:
            if time.time() >= start + 20:
                self.parent_alive = alive = False
            try:
                now = "%f" % time.time()
                message ='192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/%s HTTP/1.0" 200 3395' % now
                self.client.publish('GamboPutty', '%s\n' % message)
                increment(self.count_ref)
                s.close()
                time.sleep(.0000001) #.0000001
            except:
                self.parent_alive = alive = False
                etype, evalue, etb = sys.exc_info()
                print 'Exception: %s, Error: %s.' % (etype, evalue)

if __name__ == '__main__':
    controller = Controller()
    controller.start()

