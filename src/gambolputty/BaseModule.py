# -*- coding: utf-8 -*-
import os
import re
import abc
import logging
import sys
import ConfigurationValidator
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
        self.stats_collector = stats_collector
        self.pid_on_init = os.getpid()

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
        dynamic_var_regex = re.compile('%\(.*?\)[sdf\.\d+]+')
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
        self.checkConfiguration()

    def checkConfiguration(self):
        configuration_errors = ConfigurationValidator.ConfigurationValidator().validateModuleInstance(self)
        if configuration_errors:
            self.logger.error("%sCould not configure module %s. Problems: %s.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, configuration_errors, Utils.AnsiColors.ENDC))
            self.gp.shutDown()

    def getConfigurationValue(self, key, mapping_dict={}, use_strftime=False):
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
                    if mapping_dict or use_strftime:
                        return Utils.mapDynamicValue(self.configuration_metadata[key]['default'], mapping_dict, use_strftime)
                    return self.configuration_metadata[key]['default']
                except KeyError:
                    self.logger.warning("%sCould not find configuration setting for required setting: %s.%s" % (Utils.AnsiColors.WARNING, key, Utils.AnsiColors.ENDC))
                    self.gp.shutDown()
                    #return False
        if not isinstance(config_setting, dict):
            self.logger.debug("%sConfiguration for key: %s is incorrect.%s" % (Utils.AnsiColors.FAIL, key, Utils.AnsiColors.ENDC))
            return False
        if config_setting['contains_placeholder'] == False or mapping_dict == False:
            return config_setting.get('value')
        return Utils.mapDynamicValue(config_setting.get('value'), mapping_dict, use_strftime)

    def __mapDynamicValue(self, value, mapping_dict):
        return Utils.mapDynamicValue(value, mapping_dict)

    def shutDown(self, silent=False):
        if not silent:
            self.logger.info('%sShutting down %s.%s' % (Utils.AnsiColors.LIGHTBLUE, self.__class__.__name__, Utils.AnsiColors.ENDC))

    def addReceiver(self, receiver_name, receiver):
        if self.module_type != "output":
            self.receivers[receiver_name] = receiver

    def setInputFilter(self, filter_string):
        filter_string_tmp = re.sub('^if\s+', "", filter_string)
        filter_string_tmp = "lambda event : " + re.sub('%\((.*?)\)', r"event.get('\1', False)", filter_string_tmp)
        try:
            filter = eval(filter_string_tmp)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sFailed to compile filter: %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, filter_string, etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
        self.input_filter = filter
        # Replace default receiveEvent method with filtered one.
        self.receiveEvent = self.receiveEventFiltered

    def addOutputFilter(self, receiver_name, filter_string):
        filter_string_tmp = re.sub('^if\s+', "", filter_string)
        filter_string_tmp = "lambda event : " + re.sub('%\((.*?)\)', r"event.get('\1', False)", filter_string_tmp)
        try:
            filter = eval(filter_string_tmp)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sFailed to compile filter: %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, filter_string, etype, evalue, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
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
            try:
                matched = self.output_filters[receiver_name](event)
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
            e = event if not copy_event else event_clone.copy()
            if hasattr(receiver, 'receiveEvent'):
                receiver.receiveEvent(e)
            else:
                receiver.put(event if not copy_event else event_clone.copy())
            copy_event = True

    def sendEventFiltered(self, event):
        receivers = self.getFilteredReceivers(event)
        if not receivers:
            return
        if len(receivers) > 1:
            event_clone = event.copy()
        copy_event = False
        for receiver in receivers.itervalues():
            if hasattr(receiver, 'receiveEvent'):
                receiver.receiveEvent(event if not copy_event else event_clone.copy())
            else:
                receiver.put(event if not copy_event else event_clone.copy())
            copy_event = True

    def receiveEvent(self, event):
        for event in self.handleEvent(event):
            if event:
                self.sendEvent(event)

    def receiveEventFiltered(self, event):
        matched = self.input_filter(event)
        if matched:
            for event in self.handleEvent(event):
                if event:
                    self.sendEvent(event)
        else:
            self.sendEvent(event)

    @abc.abstractmethod
    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        """
        yield event