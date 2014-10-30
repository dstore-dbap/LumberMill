# -*- coding: utf-8 -*-
import os
import pprint
import re
import abc
import logging
import sys
import ConfigurationValidator
import Utils


class BaseModule:
    """
    Base class for all gambolputty modules.

    If you happen to override one of the methods defined here, be sure to know what you
    are doing. You have been warned ;)

    Configuration template:

    - module: SomeModuleName
        id:                               # <default: ""; type: string; is: optional>
        filter:                           # <default: None; type: None||string; is: optional>
        add_fields:                       # <default: {}; type: dict; is: optional>
        delete_fields:                    # <default: []; type: list; is: optional>
        event_type:                         # <default: None; type: None||string; is: optional>
        ...
        receivers:
          - ModuleName
          - ModuleAlias
    """

    module_type = "generic"
    """ Set module type. """
    can_run_forked = True

    def __init__(self, gp):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.gp = gp
        self.receivers = {}
        self.configuration_data = {}
        self.input_filter = None
        self.output_filters = {}
        self.process_id = os.getpid()

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
        self.dynamic_var_regex = re.compile('\$\((.*?)\)[sdf\.\d+]*')
        for key, value in self.configuration_data.items():
            # Make sure that configuration values only get parsed once.
            if isinstance(value, dict) and 'contains_placeholder' in value:
                continue
            contains_placeholder = False
            if isinstance(value, list):
                for i, _value in enumerate(value):
                    try:
                        if self.dynamic_var_regex.search(_value):
                            value[i] = self.dynamic_var_regex.sub(r"%(\1)s", _value)
                            contains_placeholder = True
                    except:
                        pass
                if contains_placeholder:
                    self.configuration_data[key] = value
            elif isinstance(value, dict):
                for _key, _value in value.items():
                    try:
                        if self.dynamic_var_regex.search(_key) or self.dynamic_var_regex.search(_value):
                            new_key = self.dynamic_var_regex.sub(r"%(\1)s", _key)
                            new_value = self.dynamic_var_regex.sub(r"%(\1)s", _value)
                            value[new_key] = new_value
                            del value[_key]
                            contains_placeholder = True
                    except:
                        pass
                if contains_placeholder:
                    self.configuration_data[key] = value
            elif isinstance(value, basestring):
                if self.dynamic_var_regex.search(value):
                    value = self.dynamic_var_regex.sub(r"%(\1)s", value)
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
            receiver_name, receiver_filter_config = iter(receiver_config.items()).next()
            self.addOutputFilter(receiver_name, receiver_filter_config['filter'])
        # Set default actions.
        self.delete_fields = self.getConfigurationValue('delete_fields')
        self.add_fields = self.getConfigurationValue('add_fields')
        self.event_type = self.getConfigurationValue('event_type')
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
        if config_setting['contains_placeholder'] == False or not mapping_dict:
            return config_setting.get('value')
        return Utils.mapDynamicValue(config_setting.get('value'), mapping_dict, use_strftime)

    def addReceiver(self, receiver_name, receiver):
        if self.module_type != "output":
            self.receivers[receiver_name] = receiver

    def setInputFilter(self, filter_string):
        filter_string_tmp = re.sub('^if\s+', "", filter_string)
        filter_string_tmp = "lambda event : " + self.dynamic_var_regex.sub(r"event.get('\1', False)", filter_string_tmp)
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
        filter_string_tmp = "lambda event : " + self.dynamic_var_regex.sub(r"event.get('\1', False)", filter_string_tmp)
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
        for receiver_name, receiver in self.receivers.items():
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

    def prepareRun(self):
        # Wrap queue with BufferedQueue. This is done here since the buffer uses a thread to flush buffer in
        # given intervals. The thread will not survive a fork of the main process. So we need to start this
        # after the fork was executed.
        for receiver_name, receiver in self.receivers.items():
            if hasattr(receiver, 'put'):
                #print("Adding buffered queue for %s" % receiver_name)
                self.receivers[receiver_name] = Utils.BufferedQueue(receiver, self.gp.queue_buffer_size)

    def commonActions(self, event):
        #if not self.input_filter or self.input_filter_matched:
        # Delete fields if configured.
        for field in self.delete_fields:
            event.pop(field, None)
        if self.add_fields:
            for field_name, field_value in Utils.mapDynamicValue(self.add_fields, event).items():
                event[field_name] = field_value
        if self.event_type:
            event['gambolputty']['event_type'] = Utils.mapDynamicValue(self.event_type, event)
        return event

    def sendEvent(self, event, apply_common_actions=True):
        if not self.receivers:
            return
        if(apply_common_actions):
            event = self.commonActions(event)
        if len(self.receivers) > 1:
            event_clone = event.copy()
        copy_event = False
        for receiver in self.receivers.values():
            #print("Sending event from %s to %s" % (self, receiver))
            if hasattr(receiver, 'receiveEvent'):
                receiver.receiveEvent(event if not copy_event else event_clone.copy())
            else:
                receiver.put(event if not copy_event else event_clone.copy())
            copy_event = True

    def sendEventFiltered(self, event, apply_common_actions=True):
        receivers = self.getFilteredReceivers(event)
        if not receivers:
            return
        if(apply_common_actions):
            event = self.commonActions(event)
        if len(receivers) > 1:
            event_clone = event.copy()
        copy_event = False
        for receiver in receivers.values():
            #print("Sending event from %s to %s" % (self, receiver))
            if hasattr(receiver, 'receiveEvent'):
                receiver.receiveEvent(event if not copy_event else event_clone.copy())
            else:
                receiver.put(event if not copy_event else event_clone.copy())
            copy_event = True

    def receiveEvent(self, event=None):
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
            self.sendEvent(event,apply_common_actions=False)

    @abc.abstractmethod
    def handleEvent(self, event):
        """
        Process the event.

        @param event: dictionary
        """
        yield event

    def shutDown(self):
        self.alive = False
        #self.logger.info('%sShutting down %s.%s' % (Utils.AnsiColors.LIGHTBLUE, self.__class__.__name__, Utils.AnsiColors.ENDC))