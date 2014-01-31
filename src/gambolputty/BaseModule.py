# -*- coding: utf-8 -*-
import pprint
import re
import socket
import abc
import logging
import collections
import sys
import Utils

class BaseModule():
    """
    Base class for all gambolputty modules that will run not run.
    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned ;)

    Configuration example:

    - module: SomeModuleName
      alias: AliasModuleName                    # <default: ""; type: string; is: optional>
      redis_client: RedisClientName             # <default: ""; type: string; is: optional>
      redis_key: XPathParser%(server_name)s     # <default: ""; type: string; is: required if redis_client is True else optional>
      redis_ttl: 600                            # <default: 60; type: integer; is: optional>
      ...
      receivers:
       - ModuleName
       - ModuleAlias
    """

    module_type = "generic"
    """ Set module type. """

    can_run_parallel = False

    def __init__(self, gp, stats_collector=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp = gp
        self.configuration_data = {}
        self.receivers = {}
        self.filters = {}
        self.redis_client = None
        self.timed_function_events = []
        self.callbacks = collections.defaultdict(list)
        self.stats_collector = stats_collector

    def configure(self, configuration=None):
        """
        Configure the module.
        This method will be called by the GambolPutty main class after initializing the module
        and after the configure method of the module is called.
        The configuration parameter contains k:v pairs of the yaml configuration for this module.

        @param configuration: dictionary
        @return: void
        """
        if configuration:
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
        # Init redis_client if configured.
        self.initRedisClient()

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
                    self.logger.warning("%sCould not find configuration setting for required setting: %s.%s" % (Utils.AnsiColors.WARNING, key, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
                    #return False
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

    def shutDown(self, silent=False):
        if not silent:
            self.logger.info('%sShutting down %s.%s' % (Utils.AnsiColors.LIGHTBLUE, self.__class__.__name__, Utils.AnsiColors.ENDC))
        self.stopTimedFunctions()

    def addReceiver(self, receiver_name, receiver):
        if not hasattr(receiver, 'receiveEvent') and not hasattr(receiver, 'put'):
            self.logger.error("%sCould not add receiver %s to %s. Seems to be incompatible, no <receiveEvent> nor <put> method found.%s" % (Utils.AnsiColors.FAIL, receiver, self.__class__, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
        self.receivers[receiver_name] = receiver

    def registerCallback(self, event_type, callback):
        if callback not in self.callbacks[event_type]:
            self.callbacks[event_type].append(callback)

    def destroyEvent(self, event=False, event_list=False):
        for callback in self.callbacks['on_event_delete']:
            if event_list:
                for event in event_list:
                    callback(event)
            else:
                callback(event)
        event = None

    def getFilter(self, receiver_name):
        try:
            return self.filters[receiver_name]
        except KeyError:
            return False

    def setFilter(self, receiver_name, filter):
        self.filters[receiver_name] = filter
        # Replace default sendEvent method with filtered one.
        self.sendEvent = self.sendEventFiltered

    def getFilteredReceivers(self, event):
        if not self.filters:
            return self.receivers
        filterd_receivers = {}
        for receiver_name, receiver in self.receivers.iteritems():
            receiver_filter = self.getFilter(receiver_name)
            if not receiver_filter:
                filterd_receivers[receiver_name] = receiver
                continue
            try:
                matched = False
                # If the filter succeeds, the data will be send to the receiver. The filter needs the event variable to work correctly.
                exec receiver_filter
                if matched:
                    filterd_receivers[receiver_name] = receiver
            except:
                raise
        return filterd_receivers

    def sendEvent(self, event):
        if not self.receivers:
            self.destroyEvent(event)
            return
        copy_event = False
        for receiver in self.receivers.itervalues():
            try:
                receiver.receiveEvent(event if copy_event is False else event.copy())
                copy_event = True
            except AttributeError:
                try:
                    receiver.put(event if copy_event is False else event.copy())
                except AttributeError:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("%s%s failed to receive event. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, receiver.__class__.__name__, etype, evalue, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()

    def sendEventFiltered(self, event):
        receivers = self.getFilteredReceivers(event)
        if not receivers:
            self.destroyEvent(event)
            return
        copy_event = False
        for receiver in receivers.itervalues():
            try:
                receiver.receiveEvent(event if copy_event is False else event.copy())
                copy_event = True
            except AttributeError:
                try:
                    receiver.put(event if copy_event is False else event.copy())
                except AttributeError:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("%s%s failed to receive event. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, receiver.__class__.__name__, etype, evalue, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()

    def receiveEvent(self, event):
        for event in self.handleEvent(event):
            self.sendEvent(event)

    @abc.abstractmethod
    def handleEvent(self, event):
        """
        Process the event.

        This is, by default, a wrapper method for the private handleMultiplexEvent method.
        handleMultiplexEvent handles a single incoming event that can trigger multiple outgoing events.
        If you don't need this, just override this method.

        @param event: dictionary
        """
        yield event

    def initRedisClient(self):
        if not self.getConfigurationValue('redis_client') or self.getConfigurationValue('redis_client') == "":
            return
        redis_client_instances = self.gp.getModuleByName(self.getConfigurationValue('redis_client'))
        if redis_client_instances:
            self.redis_client = redis_client_instances['instances'][0]

    def startTimedFunction(self, timed_function, *args, **kwargs):
        """
        Start a timed function and keep track of all running functions.
        """
        event = timed_function(*args, **kwargs)
        self.timed_function_events.append(event)
        return event

    def stopTimedFunctions(self, event=False):
        """
        Stop all timed functions. They are started as daemon, so when a reaload occurs, they will not finish cause the
        main thread still is running. This takes care of this issue.
        """
        #print "Stopping func"
        if not self.timed_function_events:
            return
        # Clear provided event only.
        if event and event in self.timed_function_events:
            event.set()
            self.timed_function_events.remove(event)
            return
        # Clear all timed functions
        for event in self.timed_function_events:
            event.set()
        self.timed_function_events = []

