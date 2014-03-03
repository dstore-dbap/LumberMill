# -*- coding: utf-8 -*-
import pprint
import re
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
      id:                               # <default: ""; type: string; is: optional>
      filter:                           # <default: None; type: None||string; is: optional>
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
        self.receivers = {}
        self.configuration_data = {}
        self.input_filter = None
        self.output_filters = {}
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
        dynamic_var_regex = re.compile('%\((.*?)\)[sdf\.\d+]+')
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
        # Add input filter.
        if self.getConfigurationValue('filter'):
            self.setInputFilter(self.getConfigurationValue('filter'))
        if 'receivers' not in self.configuration_data:
            return
         # Add output filter per receiver if configured.
        for receiver_config in self.getConfigurationValue('receivers'):
            if not isinstance(receiver_config, dict):
                continue
            receiver_name, receiver_filter_config = receiver_config.iteritems().next()
            self.addOutputFilter(receiver_name, receiver_filter_config['filter'])

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
                    if mapping_dict:
                        # Wrap dict to support nested dicts in string formatting via dot notation.
                        return self.configuration_metadata[key]['default'] % mapping_dict
                    return self.configuration_metadata[key]['default']
                except KeyError:
                    self.logger.warning("%sCould not find configuration setting for required setting: %s.%s" % (Utils.AnsiColors.WARNING, key, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
                    #return False
        if not isinstance(config_setting, dict):
            self.logger.debug("%sConfiguration for key: %s is incorrect.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
            #self.gp.shutDown()
            return False
        if config_setting['contains_placeholder'] == False or mapping_dict == False:
            return config_setting.get('value')
        return self.mapDynamicValue(config_setting.get('value'), mapping_dict)

    def mapDynamicValue(self, value, mapping_dict):
        # At the moment, just flat lists and dictionaries are supported.
        # If need arises, recursive parsing of the lists and dictionaries will be added.
        if isinstance(value, list):
            try:
                mapped_values = [v % mapping_dict for v in value]
                return mapped_values
            except KeyError:
                return False
        elif isinstance(value, dict):
            try:
                mapped_keys = [k % mapping_dict for k in value.iterkeys()]
                mapped_values = [v % mapping_dict for v in value.itervalues()]
                return dict(zip(mapped_keys, mapped_values))
            except KeyError:
                return False
        elif isinstance(value, basestring):
            try:
                return value % mapping_dict
            except KeyError:
                return False

    def shutDown(self, silent=False):
        if not silent:
            self.logger.info('%sShutting down %s.%s' % (Utils.AnsiColors.LIGHTBLUE, self.__class__.__name__, Utils.AnsiColors.ENDC))
        self.stopTimedFunctions()

    def addReceiver(self, receiver_name, receiver):
        if self.module_type != "output":
            self.receivers[receiver_name] = receiver

    def setInputFilter(self, filter_string):
        #filter = Utils.compileStringToConditionalObject("matched = %s" % filter_string, 'event.get("%s", False)')
        filter = eval("lambda event : %s" % filter_string)
        self.input_filter = filter
        # Replace default receiveEvent method with filtered one.
        self.receiveEvent = self.receiveEventFiltered

    def addOutputFilter(self, receiver_name, filter_string):
        filter = Utils.compileStringToConditionalObject("matched = %s" % filter_string, 'event.get("%s", False)')
        self.output_filters[receiver_name] = filter
        # Replace default sendEvent method with filtered one.
        self.sendEvent = self.sendEventFiltered

    def getFilteredReceivers(self, event):
        if not self.output_filters:
            return self.receivers
        filterd_receivers = {}
        for receiver_name, receiver in self.receivers.iteritems():
            if receiver_name not in self.output_filters:
                filterd_receivers[receiver_name] = receiver
                continue
            matched = False
            try:
                exec self.output_filters[receiver_name]
            except:
                raise
            # If the filter succeeds, the data will be send to the receiver. The filter needs the event variable to work correctly.
            if matched:
                filterd_receivers[receiver_name] = receiver
        return filterd_receivers

    def sendEvent(self, event):
        if not self.receivers:
            return
        if len(self.receivers) > 1:
            event_clone = event.copy()
        copy_event = False
        for receiver in self.receivers.itervalues():
            if hasattr(receiver, 'receiveEvent'):
                receiver.receiveEvent(event if copy_event is False else event_clone.copy())
            else:
                receiver.put(event if copy_event is False else event_clone.copy())
            copy_event = True

    def sendEventFiltered(self, event):
        receivers = self.getFilteredReceivers(event)
        if not receivers:
            return
        if len(receivers) > 1:
            event_clone = event.copy()
        copy_event = False
        for receiver in receivers.itervalues():
            try:
                receiver.receiveEvent(event if copy_event is False else event_clone.copy())
            except AttributeError:
                try:
                    receiver.put(event if copy_event is False else event_clone.copy())
                except AttributeError:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("%s%s failed to receive event. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, receiver.__class__.__name__, etype, evalue, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
            copy_event = True

    def receiveEvent(self, event):
        for event in self.handleEvent(event):
            self.sendEvent(event)

    def receiveEventFiltered(self, event):
        matched = False
        try:
            matched = self.input_filter(event)
            # exec self.input_filter
        except:
            pass
        # If the filter succeeds, send event to modules handleEvent method else just send it to receivers.
        if not matched:
            self.sendEvent(event)
        else:
            for event in self.handleEvent(event):
                self.sendEvent(event)

    @abc.abstractmethod
    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        """
        yield event

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

