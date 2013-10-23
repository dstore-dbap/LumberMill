# -*- coding: utf-8 -*-
import sys
import re
import logging
import threading
import traceback
import cPickle
import Utils

try:
    import thread # Python 2
except ImportError:
    import _thread as thread # Python 3

class BaseModule(threading.Thread):
    """
    Base class for all gambolputty  modules.
    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned ;)
    """

    messages_in_queues = 0
    """ Stores number of messages in all queues. """

    lock = threading.Lock()
    """ Class wide access to locking. """

    module_type = "generic"
    """ Set module type. """


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

    def __init__(self, gp=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        threading.Thread.__init__(self)
        self.daemon = True
        self.gp = gp
        self.allow_setup = True

    def setup(self):
        """
        Setup method to set default values.

        This method will be called by the GambolPutty main class after initializing the module
        and before the configure method of the module is called.

        If you implement this method in child classes, please be sure to first call this method
        before setting any config default values e.g.:
        super(<ClassName>, self).setup()
        self.configuration_data['some_setting'] = <default_value>
        """
        # Make sure setup will only be called once.
        if not self.allow_setup:
            return
        # Initalize some important default values.
        self.input_queue = False
        self.output_queues = []
        self.redis_client = False
        self.configuration_data = { 'work-on-copy': {'value': False, 'configuration_value_type': 'static'},
                                    'redis_ttl': {'value': 60, 'configuration_value_type': 'static'},
                                  }
        self.allow_setup = False

    def configure(self, configuration):
        """
        Configure the module.
        This method will be called by the GambolPutty main class after initializing the module
        and after the configure method of the module is called.
        The configuration parameter contains k:v pairs of the yaml configuration for this module.

        @param configuration: dictionary
        @return: void
        """
        self.configuration_data.update(configuration)
        # Cast "source-fields" configuration option to dictionary if necessary.
        if 'source-fields' in self.configuration_data and not isinstance(self.configuration_data['source-fields'], list):
            self.configuration_data['source-fields'] = [self.configuration_data['source-fields']]
        # Cast "target-fields" configuration option to dictionary if necessary.
        if 'target-fields' in self.configuration_data and not isinstance(self.configuration_data['target-fields'], list):
            self.configuration_data['target-fields'] = [self.configuration_data['target-fields']]
        # Test for dynamic value patterns
        dynamic_var_regex = re.compile('%\((.*?)\)[sd]')
        for key, value in self.configuration_data.iteritems():
            # Make sure that configuration values only get parsed once.
            if isinstance(value, dict) and 'configuration_value_type' in value:
                continue
            configuration_value_type = 'static'
            if isinstance(value, list):
                for _value in value:
                    try:
                        if dynamic_var_regex.search(_value):
                            configuration_value_type = 'dynamic'
                    except:
                        pass
            elif isinstance(value, dict):
                for _key, _value in value.iteritems():
                    try:
                        if dynamic_var_regex.search(_key) or dynamic_var_regex.search(_value):
                            configuration_value_type = 'dynamic'
                    except:
                        pass
            elif isinstance(value, basestring):
                if dynamic_var_regex.search(value):
                    configuration_value_type = 'dynamic'
            self.configuration_data.update({key: {'value': value, 'configuration_value_type': configuration_value_type}})

    def getConfigurationValue(self, key, mapping_dict=False):
        """
        Get a configuration value. This method encapsulates the internal configuration dictionary and
        takes care of replacing dynamic variables of the pattern e.g. %(field_name)s with the corresponding
        entries of the mapping dictionary. Most of the time, this will be the data dictionary.
        """
        try:
            config_setting = self.configuration_data[key]
        except KeyError:
            self.logger.warning("%sCould not find configuration setting for key: %s.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
            return False
        if config_setting['configuration_value_type'] == 'static' or mapping_dict == False:
            return config_setting['value']
        # At the moment, just flat lists and dictionaries are supported.
        # If need arises, recursive parsing of the lists and dictionaries will be added.
        if isinstance(config_setting['value'], list):
            try:
                mapped_values = [v % mapping_dict for v in config_setting['value']]
                return mapped_values
            except KeyError:
                return False
        elif isinstance(config_setting['value'], dict):
            try:
                mapped_keys = [k % mapping_dict for k in config_setting['value'].iterkeys()]
                mapped_values = [v % mapping_dict for v in config_setting['value'].itervalues()]
                return dict(zip(mapped_keys, mapped_values))
            except KeyError:
                return False
        elif isinstance(config_setting['value'], basestring):
            try:
                return config_setting['value'] % mapping_dict
            except KeyError:
                return False

    def initRedisClient(self):
        try:
            self.temp = self.gp.modules[self.getConfigurationValue('redis-client')][0]['instance']
            self.redis_client = self.gp.modules[self.getConfigurationValue('redis-client')][0]['instance'].getClient()
        except KeyError:
            self.logger.warning("%sWill not use redis client %s because it could not be found. Please be sure it is configured.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('redis-client'), Utils.AnsiColors.ENDC))
        if 'redis-ttl' in self.configuration_data:
            self.redis_ttl = self.getConfigurationValue('redis-ttl')

    def setRedisValue(self, key, value, ttl=0):
        if not self.redis_client:
            return None
        pickled_value = cPickle.dumps(value)
        self.redis_client.setex(key, ttl, pickled_value)

    def getRedisValue(self, key):
        if not self.redis_client:
            return None
        pickled_value = self.redis_client.get(key)
        if pickled_value is None:
            return None
        value = cPickle.loads(pickled_value)
        return value

    def shutDown(self):
        self.is_alive = False
        self.gp.shutDown()
        
    def getInputQueue(self):
        return self.input_queue

    def setInputQueue(self, queue):
        if queue not in self.output_queues:
            self.input_queue = queue
        else:
            self.logger.error("%sSetting input queue to output queue will create a circular reference. Exiting.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            self.shutDown()
    
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
        while self.is_alive:
            data = False
            try:
                data = self.input_queue.get() if not self.getConfigurationValue('work-on-copy') else self.input_queue.get().copy()
                self.decrementQueueCounter()
                data = self.handleData(data)
                self.input_queue.task_done()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("%sCould not read data from input queue.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC) )
                traceback.print_exception(exc_type, exc_value, exc_tb)
            if data:
                self.addToOutputQueues(data)