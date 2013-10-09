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
    lock = threading.Lock()
 
    @staticmethod
    def incrementQueueCounter():
        BaseModule.lock.acquire()
        BaseModule.messages_in_queues += 1
        BaseModule.lock.release()        

    @staticmethod
    def decrementQueueCounter():
        BaseModule.lock.acquire()
        BaseModule.messages_in_queues -= 1
        BaseModule.lock.release()
    
    def __init__(self, lj=False):
        self.input_queue = False
        self.output_queues = []
        self.config = { "work_on_copy": False }
        self.logger = logging.getLogger(self.__class__.__name__)
        threading.Thread.__init__(self)
        self.daemon = True
        self.lj = lj

    def setup(self):
        return

    def shutDown(self):
        self.lj.shutDown()
        
    def configure(self, configuration):
        self.config.update(configuration)

    def getInputQueue(self):
        return self.input_queue

    def setInputQueue(self, queue):
        if queue not in self.output_queues:
            self.input_queue = queue
        else:
            self.logger.error("Setting input queue to output queue will create a circular reference. Exiting.")
            thread.interrupt_main()        
    
    def getOutputQueues(self):
        return self.output_queues
        
    def addOutputQueue(self, queue, filter_by_marker=False, filter_by_field=False):
        if queue == self.input_queue:
            self.logger.error("Setting input queue to output queue will create a circular reference. Exiting.")
            thread.interrupt_main()
        func = filter_field = None
        if filter_by_marker:
            if filter_by_marker[:1] == "!":
                filter_by_marker = filter_by_marker[1:]
                func = lambda item,marker: False if marker in item['markers'] else True
            else:
                func = lambda item,marker: True if marker in item['markers'] else False
            filter_field = filter_by_marker
        if filter_by_field:
            if filter_by_field[:1] == "!":
                filter_by_field = filter_by_field[1:]
                func = lambda item,field: False if field in item else True
            else:
                func = lambda item,field: True if field in item else False
            filter_field = filter_by_field
        if not any(queue == output_queue['queue'] for output_queue in self.output_queues):
            self.output_queues.append({'queue': queue, 'output_filter': func, 'filter_field': filter_field})

    def addToOutputQueues(self, data):
        try:
            for queue in self.output_queues:
                if not queue['output_filter'] or queue['output_filter'](data, queue['filter_field']):
                    #self.logger.info("Adding data to output_queue %s in %s." % (queue, threading.currentThread()))
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
                data = self.input_queue.get() if not self.config['work_on_copy'] else self.input_queue.get().copy()
                data = self.handleData(data)
                self.input_queue.task_done()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("Could not read data from input queue." )
                traceback.print_exception(exc_type, exc_value, exc_tb)
            finally:
                self.decrementQueueCounter()
            if data:
                self.addToOutputQueues(data)