# -*- coding: utf-8 -*-
import sys
import time
import threading
import Queue
import boto3


def usage():
    sys.stdout = sys.stderr
    print('Usage: spam_sqs.py -c count region aws_id aws_key queue_name')
    sys.exit(2)

if len(sys.argv) < 7:
    usage()
    sys.exit()

aws_regions = ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'sa-east-1', 'us-gov-west-1', 'cn-north-1']

count = int(eval(sys.argv[2]))
region = sys.argv[3]
aws_id = sys.argv[4]
aws_key = sys.argv[5]
queue_name = sys.argv[6]

if type(count) is not int or region not in aws_regions:
    usage()
    sys.exit(255)

class Worker(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = queue
        self.connected = False

    def run(self):
        try:
            sqs_client = boto3.resource('sqs', region_name=region,
                                               api_version=None,
                                               use_ssl=True,
                                               verify=None,
                                               endpoint_url=None,
                                               aws_access_key_id=aws_id,
                                               aws_secret_access_key=aws_key,
                                               aws_session_token=None,
                                               config=None)
            self.connected = True
        except:
            etype, evalue, etb = sys.exc_info()
            print("Could not connect to sqs service. Exception: %s, Error: %s." % (etype, evalue))
            return
        try:
            sqs_queue = sqs_client.get_queue_by_name(QueueName=queue_name)
        except:
            etype, evalue, etb = sys.exc_info()
            print("Could not connect to sqs queue %s. Exception: %s, Error: %s." % (queue_name, etype, evalue))
            return
        while self.connected:
            try:
                message = self.queue.get(timeout=.5)
                sqs_queue.send_message(MessageBody=message)
            except Queue.Empty:
                self.connected = False
                break
        return

class SqsLoadTester():

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
    lt = SqsLoadTester(5)
    lt.start("<13>229.25.18.182 - - [28/Jul/2006:10:27:10 -0300] \"GET /cgi-bin/try/9153/?param1=Test&param2=%s HTTP/1.0\" 200 3395 \"Mozilla/5.0 (Linux; U; Android 2.3.5; en-in; HTC_DesireS_S510e Build/GRJ90) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1\"")