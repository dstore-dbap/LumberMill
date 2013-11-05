# -*- coding: utf-8 -*-
import sys
import re
import abc
import logging
import threading
import cPickle
import Utils
import redis

class BaseModule():
    """
    Base class for all gambolputty modules that will run not run.
    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned ;)

    Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      configuration:
        work_on_copy: True                      # <default: False; type: boolean; is: optional>
        redis_client: RedisClientName           # <default: ""; type: string; is: optional>
        redis_key: XPathParser%(server_name)s   # <default: ""; type: string; is: required if redis_client is True else optional>
        redis_ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:
       - ModuleName
       - ModuleAlias
    """

    module_type = "generic"
    """ Set module type. """

    events_being_processed = 0

    lock = threading.Lock()
    """ Class wide access to locking. """

    @staticmethod
    def incrementEventsBeingProcessedCounter():
        with BaseModule.lock:
            BaseModule.events_being_processed += 1


    @staticmethod
    def decrementEventsBeingProcessedCounter():
        with BaseModule.lock:
            BaseModule.events_being_processed -= 1

    def __init__(self, gp=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp = gp
        self.configuration_data = {}
        self.input_queue = False
        self.output_queues = []
        self.redis_client = False

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
        # Test for dynamic value patterns
        dynamic_var_regex = re.compile('%\((.*?)\)[sd]')
        for key, value in self.configuration_data.iteritems():
            # Make sure that configuration values only get parsed once.
            if isinstance(value, dict) and 'contains_placeholder' in value:
                continue
            contains_placeholder = False
            if isinstance(value, list):
                for _value in value:
                    try:
                        if dynamic_var_regex.search(_value):
                            contains_placeholder = True
                    except:
                        pass
            elif isinstance(value, dict):
                for _key, _value in value.iteritems():
                    try:
                        if dynamic_var_regex.search(_key) or dynamic_var_regex.search(_value):
                            contains_placeholder = True
                    except:
                        pass
            elif isinstance(value, basestring):
                if dynamic_var_regex.search(value):
                    contains_placeholder = True
            self.configuration_data[key] = {'value': value, 'contains_placeholder': contains_placeholder}

    def getConfigurationValue(self, key, mapping_dict=False):
        """
        Get a configuration value. This method encapsulates the internal configuration dictionary and
        takes care of replacing dynamic variables of the pattern e.g. %(field_name)s with the corresponding
        entries of the mapping dictionary. Most of the time, this will be the data dictionary.

        It will also take care to return a default value if the module doc string provided one.
        """
        # Test if requested key exists.
        config_setting = False
        try:
            config_setting = self.configuration_data[key]
        except KeyError:
                # Try to return a default value for requested setting
                try:
                    return self.configuration_metadata[key]['default']
                except KeyError:
                    self.logger.debug("%sCould not find configuration setting for key: %s.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
                    #self.gp.shutDown()
                    return False
        if not isinstance(config_setting, dict):
            self.logger.debug("%sConfiguration for key: %s is incorrect.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
            #self.gp.shutDown()
            return False
        # Return value directly if it does not contain any placeholders or no mapping dictionary was provided.
        if config_setting['contains_placeholder'] == False or mapping_dict == False:
            try:
                return config_setting['value']
            except KeyError:
                # Try to return a default value for requested setting
                try:
                    return self.configuration_metadata[key]['default']
                except KeyError:
                    self.logger.error("%sCould not find configuration value for key: %s and no default value was defined." % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
                    return False
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
            self.temp = self.gp.modules[self.getConfigurationValue('redis_client')][0]['instance']
            self.redis_client = self.gp.modules[self.getConfigurationValue('redis_client')][0]['instance'].getClient()
        except KeyError:
            self.logger.warning("%sWill not use redis client %s because it could not be found. Please be sure it is configured.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('redis_client'), Utils.AnsiColors.ENDC))
        if 'redis_ttl' in self.configuration_data:
            self.redis_ttl = self.getConfigurationValue('redis_ttl')

    def redisClientAvailiable(self):
        return True if self.redis_client and isinstance(self.redis_client, redis.StrictRedis) else False

    def getRedisLock(self, name, timeout=None, sleep=0.1):
        if not self.redisClientAvailiable():
            return None
        return self.redis_client.lock(name, timeout, sleep)

    def setRedisValue(self, key, value, ttl=0, pickle=True):
        if not self.redisClientAvailiable():
            return None
        if pickle is True:
            try:
                value = cPickle.dumps(value)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not store %s:%s in redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, key, value, etype, evalue, Utils.AnsiColors.ENDC))
                raise
        self.redis_client.setex(key, ttl, value)

    def getRedisValue(self, key, unpickle=True):
        if not self.redisClientAvailiable():
            return None
        value = self.redis_client.get(key)
        if unpickle and value:
            try:
                value = cPickle.loads(value)
            except:
                etype, evalue, etb = sys.exc_info()
                print "%sCould not unpickle %s:%s from redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, key, value, etype, evalue, Utils.AnsiColors.ENDC)
                self.logger.error("%sCould not unpickle %s:%s from redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, key, value, etype, evalue, Utils.AnsiColors.ENDC))
                raise
        return value

    def shutDown(self):
        self.is_alive = False

    def getInputQueue(self):
        return self.input_queue

    def setInputQueue(self, queue):
        if queue not in self.output_queues:
            self.input_queue = queue
        else:
            self.logger.error("%sSetting input queue to output queue will create a circular reference. Exiting.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def getOutputQueues(self):
        return self.output_queues

    def addOutputQueue(self, queue, filter = False):
        if queue == self.input_queue:
            self.logger.error("%sSetting input queue to output queue will create a circular reference. Exiting.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
            return
        if filter:
            filter = Utils.compileStringToConditionalObject("matched = %s" % filter, 'data["%s"]')
        if not any(queue == output_queue['queue'] for output_queue in self.output_queues):
            self.output_queues.append({'queue': queue, 'filter': filter})

    def addEventToOutputQueues(self, data):
        for queue in self.output_queues:
            if queue['filter']:
                try:
                    # If the filter fails, the data will not be added to the queue.
                    exec queue['filter']
                    if not matched:
                        continue
                except:
                    return
            try:
                queue['queue'].put(data)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("%sCould not add received data to output queue. Excpeption: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, etype, evalue, Utils.AnsiColors.ENDC))
        self.decrementEventsBeingProcessedCounter()

    def getEventFromInputQueue(self, block=True, timeout=None):
        data = self.input_queue.get(block, timeout) if not self.getConfigurationValue('work_on_copy') else self.input_queue.get().copy()
        self.incrementEventsBeingProcessedCounter()
        self.input_queue.task_done()
        return data

    @abc.abstractmethod
    def handleData(self, data):
        """
        This method has to be implemented by modules.
        """