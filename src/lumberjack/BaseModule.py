import sys
import logging
import threading
import traceback
import Utils

try:
    import thread # Python 2
except ImportError:
    import _thread as thread # Python 3

class BaseModule(threading.Thread):
    """
    Base class for all lumberjack  modules.
    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned ;)
    """

    """ Stores number of messages in all queues """
    messages_in_queues = 0
    lock = threading.Lock()
 
    @staticmethod
    def incrementQueueCounter():
        """
        Static method to keep track of how many events are en-route in queues.
        """
        BaseModule.lock.acquire()
        BaseModule.messages_in_queues += 1
        BaseModule.lock.release()        

    @staticmethod
    def decrementQueueCounter():
        """
        Static method to keep track of how many events are en-route in queues.
        """
        BaseModule.lock.acquire()
        BaseModule.messages_in_queues -= 1
        BaseModule.lock.release()
    
    def __init__(self, lj=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        threading.Thread.__init__(self)
        self.daemon = True
        self.lj = lj

    def setup(self):
        """
        Setup method to set default values.
        This method will be called by the LumberJack main class after initializing the module
        and before the configure method of the module is called.
        """
        self.input_queue = False
        self.output_queues = []
        self.config = { "work_on_copy": False }
        return

    def configure(self, configuration):
        """
        Configure the module.
        This method will be called by the LumberJack main class after initializing the module
        and after the configure method of the module is called.
        The configuration parameter contains k:v pairs of the yaml configuration for this module.

        @param configuration: dictionary
        @return: void
        """
        self.config.update(configuration)

    def shutDown(self):
        self.lj.shutDown()
        
    def getInputQueue(self):
        return self.input_queue

    def setInputQueue(self, queue):
        if queue not in self.output_queues:
            self.input_queue = queue
        else:
            self.logger.error("%sSetting input queue to output queue will create a circular reference. Exiting.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            thread.interrupt_main()        
    
    def getOutputQueues(self):
        return self.output_queues
        
    def addOutputQueue(self, queue, filter_by_marker=False, filter_by_field=False):
        if queue == self.input_queue:
            self.logger.error("%sSetting input queue to output queue will create a circular reference. Exiting.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
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
            self.logger.warning("%sWill not start module %s since no input queue set.%s" % (Utils.AnsiColors.WARNING, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        self.logger.info("%sStarted %s%s" % (Utils.AnsiColors.OKGREEN ,self.__class__.__name__, Utils.AnsiColors.ENDC))
        while self.is_alive:
            data = False
            try:
                data = self.input_queue.get() if not self.config['work_on_copy'] else self.input_queue.get().copy()
                self.decrementQueueCounter()
                data = self.handleData(data)
                self.input_queue.task_done()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("%sCould not read data from input queue.%s" % (Utils.AnsiColors.FAIL, tils.AnsiColors.ENDCU) )
                traceback.print_exception(exc_type, exc_value, exc_tb)
            if data:
                self.addToOutputQueues(data)