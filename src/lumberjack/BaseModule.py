import sys
import time
import logging
import threading
import traceback
try:
    import thread # Python 2
except ImportError:
    import _thread as thread # Python 3

class BaseModule(threading.Thread):
    
    messages_in_queues = 0
    
    def __init__(self):
        self.input_queue = False
        self.output_queues = []
        self.config = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        threading.Thread.__init__(self)
        self.daemon = True
        self.lock = threading.Lock()

    def setup(self, lj):
        self.lj = lj
        
    def configure(self, configuration):
        self.config = configuration

    def getInputQueue(self):
        return self.input_queue

    def incrementQueueCounter(self):
        self.lock.acquire()
        BaseModule.messages_in_queues += 1
        self.lock.release()        

    def decrementQueueCounter(self):
        self.lock.acquire()
        BaseModule.messages_in_queues -= 1
        self.lock.release()
        
    def setInputQueue(self, queue):
        if queue not in self.output_queues:
            self.input_queue = queue
        else:
            self.logger.error("Setting input queue to output queue will create a circular reference. Exiting.")
            thread.interrupt_main()        
    
    def getOutputQueues(self):
        return self.output_queues
        
    def addOutputQueue(self, queue, filter_by_marker=False):
        if queue == self.input_queue:
            self.logger.error("Setting input queue to output queue will create a circular reference. Exiting.")
            thread.interrupt_main()
        func = None   
        if filter_by_marker:
            func = lambda item,marker: True if marker in item['markers'] else False
        if not any(queue == output_queue['queue'] for output_queue in self.output_queues):
            self.output_queues.append({'queue': queue, 'output_filter': func, 'marker': filter_by_marker})

    def addToOutputQueues(self, data):
        try:
            for queue in self.output_queues:
                if not queue['output_filter'] or queue['output_filter'](data, queue['marker']):
                    #self.logger.info("Adding %s to output_queue %s in %s." % (data, queue, threading.currentThread()))
                    queue['queue'].put(data)
                    self.incrementQueueCounter()
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not add received data to output queue. Excpeption: %s, Error: %s." % (etype, evalue))

    def run(self):
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        while True:
            data = False
            try:
                item = self.input_queue.get()
                data = self.handleData(item)
                self.input_queue.task_done()
                self.decrementQueueCounter()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("Could not read data from input queue." )
                traceback.print_exception(exc_type, exc_value, exc_tb)
                time.sleep(1)
            if data:
                self.addToOutputQueues(data)