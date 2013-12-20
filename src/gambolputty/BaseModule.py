# -*- coding: utf-8 -*-
import pprint
import sys
import re
import abc
import logging
import cPickle
import collections
import Utils
import redis
import threading
import multiprocessing

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

    module_can_run_parallel = True

    def __init__(self, gp, stats_collector=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp = gp
        self.configuration_data = {}
        self.input_queue = False
        self.output_queues = []
        self.receivers = []
        self.filter = {}
        self.redis_client = False
        self.callbacks = collections.defaultdict(list)
        self.stats_collector = stats_collector

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
                # Try to return a default value for requested setting.
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
            return config_setting.get('value')
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
            self.redis_client = self.gp.modules[self.getConfigurationValue('redis_client')]['instances'][0].getClient()
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
                self.logger.error("%sCould not unpickle %s:%s from redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, key, value, etype, evalue, Utils.AnsiColors.ENDC))
                raise
        return value

    def shutDown(self):
        pass

    def addReceiver(self, receiver):
        if receiver not in self.receivers:
            self.receivers.append(receiver)

    def sendEventToReceivers(self, event, update_counter=True):
        if not self.receivers:
            self.destroyEvent(event)
            return
        event_dropped = True
        for idx, receiver in enumerate(self.receivers):
            receiver_filter = self.getFilter(receiver)
            if receiver_filter:
                try:
                    matched = False
                    # If the filter fails, the data will not be send to the receiver.
                    exec receiver_filter
                    if not matched:
                        continue
                except:
                    raise
            event_dropped = False
            if isinstance(receiver, threading.Thread) or isinstance(receiver, multiprocessing.Process):
                receiver.getInputQueue().put(event if idx is 0 else event.copy())
                #receiver.getInputQueue().put(event.copy())
            else:
                receiver.handleEvent(event if idx is 0 else event.copy())
                #receiver.handleEvent(event.copy())
        if event_dropped:
            self.destroyEvent(event)

    def registerCallback(self, event_type, callback):
        self.callbacks[event_type].append(callback)

    def destroyEvents(self, events):
        for callback in self.callbacks['on_event_delete']:
            for event in events:
                callback(event)

    def getFilter(self, receiver):
        try:
            return self.filter[receiver.__class__]
        except KeyError:
            return False

    def setFilter(self, filter, receiver):
        self.filter[receiver.__class__] = filter

    def handleEvent(self, event):
        """
        Process the event.

        This is, by default, a wrapper method for the private handleMultiplexEvent method.
        handleMultiplexEvent handles a single incoming event that can trigger multiple outgoing events.
        If you don't need this, just override this method.

        @param event: dictionary
        """
        for event in self.handleMultiplexEvent(event):
            self.sendEventToReceivers(event)

    @abc.abstractmethod
    def handleMultiplexEvent(self, data):
        """
        If a module needs to emit more than just the received event, implement this method.
        """
        self.logger.error("%sPlease implement either the handleEvent or the handleMultiplexEvent in your module.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
        sys.exit(255)