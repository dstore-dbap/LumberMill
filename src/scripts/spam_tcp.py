#!/usr/bin/env python
#
#  tcp_socket_throughput.py
#  TCP Socket Connection Throughput Tester
#  Corey Goldberg (www.goldb.org), 2008
import random
import os
import sys
import time
import socket
from ctypes import c_int, c_bool
import multiprocessing
from multiprocessing.pool import ThreadPool
import threading
import Queue

host = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv) == 3 else 5151

def single():
        start = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((host, port))
        except:
            etype, evalue, etb = sys.exc_info()
            print 'Exception: %s, Error: %s.' % (etype, evalue)
            return
        for counter in xrange(0, 10000):
            if counter % 1000 == 0:
                print counter
            #rand = #"%f-%10.9f" % (time.time(), random.random())
            message ='192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/%s HTTP/1.0" 200 3395\r\n' % counter
            s.send('%s\n' % message)
            time.sleep(.00001) #.0000001
        s.close()
        print "Took %s" % (time.time() - start)

def tcpLoadTestWorkLoad(item):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((host, port))
        s.send('%s\n' % item)
        s.close()
    except:
        etype, evalue, etb = sys.exc_info()
        print 'Exception: %s, Error: %s.' % (etype, evalue)
        return

class Worker(threading.Thread):

    def __init__(self, queue, callback):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.callback = callback

    def run(self):
        while True:
            try:
                item = self.queue.get(timeout=.5)
                self.callback(item)
            except Queue.Empty:
                # do whatever background check needs doing
                break

class TcpLoadTester():

    def __init__(self, num_workers=100):
        self.lock = threading.Lock()
        self.counter = 0
        self.queue = Queue.Queue(num_workers)
        self.num_workers = num_workers

    def start(self, callback):
        total_item_count = 5000
        workers = set()
        print "Start load test."
        for i in xrange(0, self.num_workers):
            worker = Worker(self.queue, callback)
            worker.start()
            workers.add(worker)
        start = time.time()
        for counter in xrange(0, total_item_count):
            if counter % 100 == 0:
                print counter
            message ='192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/%s HTTP/1.0" 200 3395\r\n' % counter
            self.queue.put(message)
        for worker in workers:
            worker.join()
        stop = time.time()
        print "Finished. Took %s. Mean req/s: %s" % (stop-start, total_item_count / (stop-start))

if __name__ == '__main__':
    #single()
    #controller = Controller()
    #controller.start()
    lt = TcpLoadTester()
    lt.start(tcpLoadTestWorkLoad)


