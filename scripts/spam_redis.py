#!/usr/bin/env python

from __future__ import print_function
import sys
import time
import threading
import Queue
import redis

def usage():
    sys.stdout = sys.stderr
    print('Usage: spam_redis.py [channel||list] name count host [port 5151]')
    sys.exit(2)

if len(sys.argv) < 5:
    usage()
    sys.exit()

redis_type = sys.argv[1]
redis_name = sys.argv[2]
count = int(eval(sys.argv[3]))
host = sys.argv[4]
port = int(sys.argv[5]) if len(sys.argv) == 6 else 6379

class Worker(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.connected = False

    def run(self):
        self.connected = False
        try:
            self.client = redis.Redis(host=host, port=port)
            self.connected = True
        except:
            etype, evalue, etb = sys.exc_info()
            print('Could no connect to redis server at %s:%s. Exception: %s, Error: %s.' % (host, port, etype, evalue))
        while self.connected:
            try:
                message = self.queue.get(timeout=.5)
                if redis_type == 'channel':
                    self.client.publish(redis_name, message)
                else:
                    self.client.rpush(redis_name, message)
            except Queue.Empty:
                break

class RedisLoadTester():

    def __init__(self, num_workers=10):
        self.lock = threading.Lock()
        self.counter = 0
        self.queue = Queue.Queue(10)
        self.num_workers = num_workers

    def start(self, message):
        total_item_count = count
        workers = set()
        for i in xrange(0, self.num_workers):
            worker = Worker(self.queue)
            worker.start()
            workers.add(worker)
            time.sleep(.1)
            if not worker.connected:
                sys.exit()
        print("Start load test.")
        start = time.time()
        for counter in xrange(0, total_item_count):
            if counter % 1000 == 0:
                sys.stdout.write("Message already sent: %s. Mean req/s: %s\r" % (counter+1, counter / (time.time()-start)))
                sys.stdout.flush()
            now = "%f" % time.time()
            self.queue.put(message % now)
        for worker in workers:
            worker.join()
        stop = time.time()
        print("Message sent: %s. Took %s. Mean req/s: %s" % (counter+1, stop-start, total_item_count / (stop-start)))

if __name__ == '__main__':
    lt = RedisLoadTester()
    lt.start("<13>229.25.18.182 - - [28/Jul/2006:10:27:10 -0300] \"GET /cgi-bin/try/9153/?param1=Test&param2=%s HTTP/1.0\" 200 3395 \"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:32.0) Gecko/20100101 Firefox/32.0\"\n")


