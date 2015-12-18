# -*- coding: utf-8 -*-
import signal
import sys

import yaml

from lumbermill.BaseModule import BaseModule
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.misc import TimedFunctionManager


@ModuleDocstringParser
class PackConfiguration(BaseModule.BaseModule):
    """
    Synchronize configuration from leader to pack members.
    Any changes to the leaders configuration will be synced to all pack followers.

    Locally configured modules of pack members will not be overwritten by the leaders configuration.

    Module dependencies: ['Pack']

    pack: Name of the pack module. Defaults to the standard Pack module.
    ignore_modules: List of module names to exclude from sync process.
    interval: Time in seconds between checks if master config did change.

    Configuration template:

    - PackConfiguration:
       pack:                            # <default: 'Pack'; type: string; is: optional>
       ignore_modules:                  # <default: []; type: list; is: optional>
       interval: 10                     # <default: 60; type: integer; is: optional>
    """

    module_type = "stand_alone"
    """Set module type"""

    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        #self.logger.setLevel(logging.DEBUG)
        # Get pack module instance.
        mod_info = self.lumbermill.getModuleInfoById(self.getConfigurationValue('pack'))
        if not mod_info:
            self.logger.error("Could not start cluster configuration module. Required pack module %s not found. Please check your configuration." % (self.getConfigurationValue('pack')))
            self.lumbermill.shutDown()
            return
        self.pack = mod_info['instances'][0]
        if self.pack.is_leader:
            self.update_config_func = self.getMasterConfigurationUpdateFunc()
            self.pack.addHandler(action='update_configuration_request', callback=self.leaderHandleUpdateConfigurationRequest)
        else:
            self.pack.addHandler(action='discovery_finish', callback=self.followerHandleDiscoveryFinishRequest)
            self.pack.addHandler(action='update_configuration_reply', callback=self.followerHandleUpdateConfigurationReply)
            self.pack.addHandler(action='push_updated_configuration', callback=self.followerHandleUpdateConfigurationReply)

    def syncConfigurationToPack(self, configuration):
        """
        Push configuration to all pack members.

        In contrast to followers asking for new configurations, the leader can push a new config to all followers
        via a call to this function.
        """
        message = self.pack.getDefaultMessageDict(action='push_updated_configuration', custom_dict={'configuration': configuration})
        self.pack.sendMessageToPack(message)

    def getMasterConfigurationUpdateFunc(self):
        @setInterval(self.getConfigurationValue('interval'))
        def checkForUpdatedMasterConfiguration():
            filtered_running_configuration = self.filterIgnoredModules(self.lumbermill.getConfiguration())
            if self.filtered_startup_config != filtered_running_configuration:
                self.filtered_startup_config = filtered_running_configuration
                self.syncConfigurationToPack(self.filtered_startup_config)
        return checkForUpdatedMasterConfiguration

    def followerHandleDiscoveryFinishRequest(self, sender, message):
        """
        Request configuration from pack leader.
        """
        message = self.pack.getDefaultMessageDict(action='update_configuration_request')
        self.logger.debug('Requested configuration from leader %s.' % self.pack.discovered_leader.getHostName())
        self.pack.sendMessageToPackLeader(message)

    def leaderHandleUpdateConfigurationRequest(self, sender, message):
        """
        Receive update configuration requests and handle them.
        """
        try:
            pack_follower = self.pack.pack_followers[sender[0]]
        except KeyError:
            return
        message = self.pack.getDefaultMessageDict(action='update_configuration_reply', custom_dict={'configuration': self.filtered_startup_config})
        self.logger.debug('Sending update configuration reply to %s' % pack_follower.getHostName())
        self.pack.sendMessageToPackFollower(pack_follower, message)

    def followerHandleUpdateConfigurationReply(self, sender, message):
        sender_ip = sender[0]
        if not self.pack.discovered_leader or sender_ip != self.pack.discovered_leader.getIp():
            return
        self.logger.debug('Got update configuration reply from %s.' % self.pack.discovered_leader.getHostName())
        leader_configuration = message['configuration']
        leader_configuration = self.filterIgnoredModules(leader_configuration)
        if leader_configuration != self.filtered_startup_config:
            self.logger.info("Got new pack configuration from %s." % (self.pack.discovered_leader.getHostName()))
            self.lumbermill.setConfiguration(leader_configuration, merge=True)
            try:
                with open(self.lumbermill.getConfigurationFilePath(), 'w') as outfile:
                    outfile.write(yaml.dump(self.lumbermill.getConfiguration(), default_flow_style=False))
                # Send signal to reload LumberMill.
                signal.alarm(1)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not update configuration file %s. Exception: %s, Error: %s." % (self.lumbermill.getConfigurationFilePath(), etype, evalue))

    def filterIgnoredModules(self, configuration):
        filtered_configuration = []
        for idx, module_info in enumerate(configuration):
            if type(module_info) is dict:
                module_name = module_info.keys()[0]
            elif type(module_info) is str:
                module_name = module_info
            else:
                self.logger.error('Unknown module configuration. Module: %s.' % module_info)
                self.lumbermill.shutDown()
            # Never sync Pack modules.
            if module_name in ['Pack', 'PackConfiguration']:
                continue
            # Filter ignored modules.
            if module_name not in self.getConfigurationValue('ignore_modules'):
                filtered_configuration.append(module_info)
        return filtered_configuration

    def start(self):
        # Get currently running configuration.
        self.filtered_startup_config = self.filterIgnoredModules(self.lumbermill.getConfiguration())
        if self.pack.is_leader:
            TimedFunctionManager.startTimedFunction(self.update_config_func)

