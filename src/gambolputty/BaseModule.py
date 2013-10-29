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

    Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: False; type: string; is: optional>
      pool-size: 4                              # <default: 1; type: integer; is: optional>
      configuration:
        work-on-copy: True                      # <default: False; type: boolean; is: optional>
        redis-client: RedisClientName           # <default: False; type: string; is: optional>
        redis-key: XPathParser%(server_name)s   # <default: False; type: string; is: optional>
        redis-ttl: 600                          # <default: 60; type: integer; is: optional>
      receivers:                                # <type: list, is: required>
       - ModuleName
       - ModuleAlias
    """

    lock = threading.Lock()
    """ Class wide access to locking. """

    module_type = "generic"
    """ Set module type. """


    def __init__(self, gp=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        threading.Thread.__init__(self)
        self.daemon = True
        self.gp = gp
        self.allow_setup = True
        self.input_queue = False
        self.output_queues = []
        self.configuration_data = {}

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
                    self.logger.error("%sCould not find configuration setting for key: %s.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
                    self.shutDown()
                    return False
        if not isinstance(config_setting, dict):
            self.logger.error("%sConfiguration for key: %s is incorrect.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
            self.shutDown()
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
                    self.shutDown()
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
            self.temp = self.gp.modules[self.getConfigurationValue('redis-client')][0]['instance']
            self.redis_client = self.gp.modules[self.getConfigurationValue('redis-client')][0]['instance'].getClient()
        except KeyError:
            self.logger.warning("%sWill not use redis client %s because it could not be found. Please be sure it is configured.%s" % (Utils.AnsiColors.FAIL, self.getConfigurationValue('redis-client'), Utils.AnsiColors.ENDC))
        if 'redis-ttl' in self.configuration_data:
            self.redis_ttl = self.getConfigurationValue('redis-ttl')

    def setRedisValue(self, key, value, ttl=0):
        if not self.getConfigurationValue('redis-client'):
            return None
        pickled_value = cPickle.dumps(value)
        self.redis_client.setex(key, ttl, pickled_value)

    def getRedisValue(self, key):
        if not self.getConfigurationValue('redis-client'):
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

    def __addOutputQueue(self, queue, filter_by_marker=False, filter_by_field=False):
        func = filter_field = None
        if filter_by_marker:
            if filter_by_marker[:1] == "!":
                filter_by_marker = filter_by_marker[1:]
                func = lambda item,marker: False if marker in item['markers'] else True
            else:
                func = lambda item,marker: True if marker in item['markers'] else False
            filter_field = filter_by_marker
        elif filter_by_field:
            if filter_by_field[:1] == "!":
                filter_by_field = filter_by_field[1:]
                func = lambda item,field: False if field in item else True
            else:
                func = lambda item,field: True if field in item else False
            filter_field = filter_by_field

    def addOutputQueue(self, queue, filter = False):
        if queue == self.input_queue:
            self.logger.error("%sSetting input queue to output queue will create a circular reference. Exiting.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            self.shutDown()
            return
        if filter:
            filter = Utils.compileAstConditionalFilterObject(filter)
        if not any(queue == output_queue['queue'] for output_queue in self.output_queues):
            self.output_queues.append({'queue': queue, 'filter': filter})

    def addToOutputQueues(self, data):
        for queue in self.output_queues:
            if queue['filter']:
                try:
                    # If the filter fails, the data will not be added to the queue.
                    exec queue['filter']
                    if not matched:
                        return
                except:
                    return
            try:
                queue['queue'].put(data)
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
                data = self.handleData(data)
                self.input_queue.task_done()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("%sCould not read data from input queue.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC) )
                traceback.print_exception(exc_type, exc_value, exc_tb)
            if data:
                self.addToOutputQueues(data)