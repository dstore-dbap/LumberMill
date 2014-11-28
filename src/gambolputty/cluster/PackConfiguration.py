# -*- coding: utf-8 -*-
import signal
import BaseModule
import Decorators
import Utils


@Decorators.ModuleDocstringParser
class PackConfiguration(BaseModule.BaseModule):
    """
    Synchronize configuration from leader to pack members.
    Any changes to the leaders configuration will be synced to all pack followers.

    Locally configured modules of pack members will not be overwritten by the leaders configuration.

    Module dependencies: ['Cluster']

    cluster: Name of the cluster module.
    ignore_modules: List of module names to exclude from sync process.
    interval: Time in seconds between checks if master config did change.

    Configuration template:

    - PackConfiguration:
        pack:                                   # <default: 'Pack'; type: string; is: optional>
        ignore_modules: [WebGui,LocalModule]    # <default: []; type: list; is: optional>
        interval: 10                            # <default: 60; type: integer; is: optional>
    """

    module_type = "stand_alone"
    """Set module type"""

    can_run_forked = False

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        #self.logger.setLevel(logging.DEBUG)
        # Get pack module instance.
        mod_info = self.gp.getModuleInfoById(self.getConfigurationValue('pack'))
        if not mod_info:
            self.logger.error("Could not start cluster configuration module. Required pack module %s not found. Please check your configuration." % (self.getConfigurationValue('pack')))
            self.gp.shutDown()
            return
        self.pack_module = mod_info['instances'][0]
        if self.pack_module.leader:
            self.update_config_func = self.getMasterConfigurationUpdateFunc()
            self.pack_module.addHandler(action='discovery_finish', callback=self.handleDiscoveryFinish)
        else:
            self.pack_module.addHandler(action='update_configuration_call', callback=self.handleUpdateConfigurationCall)

    def syncConfigurationToPack(self, configuration):
        message = self.pack_module.getDefaultMessageDict(action='update_configuration_call', custom_dict={'configuration': configuration})
        self.pack_module.sendMessageToPack(message)

    def getMasterConfigurationUpdateFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('interval'))
        def updateMasterConfiguration():
            filtered_running_configuration = self.filterIgnoredModules(self.gp.getConfiguration())
            if self.filtered_startup_config != filtered_running_configuration:
                self.filtered_startup_config = filtered_running_configuration
                self.syncConfigurationToPack(self.filtered_startup_config)
        return updateMasterConfiguration

    def handleDiscoveryFinish(self, message, pack_member):
        """
        Sync current configuration to newly discovered hosts.
        """
        message = self.pack_module.getDefaultMessageDict(action='update_configuration_call', custom_dict={'configuration': self.filtered_startup_config})
        self.logger.debug('handleDiscoveryReply called.')
        self.pack_module.sendMessageToPackMember(message, pack_member)

    def handleUpdateConfigurationCall(self, message, pack_member):
        """
        Receive update configuration calls and handle them.
        """
        leader_configuration = message['configuration']
        leader_configuration = self.filterIgnoredModules(leader_configuration)
        if leader_configuration != self.filtered_startup_config:
            self.logger.info("Got new pack configuration from %s." % (pack_member.getHostName()))
            self.gp.setConfiguration(leader_configuration, merge=True)
            # Send signal to reload GambolPutty.
            signal.alarm(1)

    def filterIgnoredModules(self, configuration):
        filtered_configuration = []
        for idx, module_info in enumerate(configuration):
            # Never sync pack modules.
            if not 'module' in module_info or module_info['module'] in ['Pack', 'PackConfiguration']:
                continue
            # Filter ignored modules.
            if module_info['module'] not in self.getConfigurationValue('ignore_modules'):
                filtered_configuration.append(module_info)
        return filtered_configuration

    def run(self):
        # Get currently running configuration.
        self.filtered_startup_config = self.filterIgnoredModules(self.gp.getConfiguration())
        if self.pack_module.leader:
            Utils.TimedFunctionManager.startTimedFunction(self.update_config_func)

