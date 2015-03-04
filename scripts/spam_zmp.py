# -*- coding: utf-8 -*-
import zmq
import sys
import time
import threading
import Queue

def usage():
    sys.stdout = sys.stderr
    print('Usage: spam_zmq.py -m [push|pub] -c count host [port 5151]')
    print('When using pub the topic will be set to "LoadTest"')
    sys.exit(2)

if len(sys.argv) < 5:
    usage()
    sys.exit()

mode = sys.argv[2]
count = int(eval(sys.argv[4]))
host = sys.argv[5]
port = int(sys.argv[6]) if len(sys.argv) == 7 else 5151

if mode not in ['push', 'pub'] or type(count) is not int or type(port) is not int:
    usage()

class Worker(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.connected = False

    def run(self):
        context = zmq.Context()
        if mode == 'push':
            sock = context.socket(zmq.PUSH)
        else:
            sock = context.socket(zmq.PUB)
        try:
            sock.connect('tcp://%s:%s' % (host, port))
            self.connected = True
        except:
            etype, evalue, etb = sys.exc_info()
            print("Failed to connect to %s:%s. Exception: %s, Error: %s." % (host, port, etype, evalue))
            self.connected = False
        while self.connected:
            try:
                message = self.queue.get(timeout=.5)
                if mode == 'push':
                    sock.send(message)
                else:
                    sock.send('LoadTest %s' % message)
            except Queue.Empty:
                self.connected = False
                break
        sock.close()
        return

class ZmqLoadTester():

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
    lt = ZmqLoadTester(5)
    lt.start("<13>229.25.18.182 - - [28/Jul/2006:10:27:10 -0300] \"GET /cgi-bin/try/9153/?param1=Test&param2=%s HTTP/1.0\" 200 3395 \"Mozilla/5.0 (Linux; U; Android 2.3.5; en-in; HTC_DesireS_S510e Build/GRJ90) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1\"")