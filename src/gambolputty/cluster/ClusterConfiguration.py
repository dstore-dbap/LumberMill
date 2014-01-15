# -*- coding: utf-8 -*-
import sys
import signal
import BaseModule
import Decorators
import Utils

@Decorators.ModuleDocstringParser
class ClusterConfiguration(BaseModule.BaseModule):
    """
    Synchronize configuration from master to slaves.
    The running master configuration will be stored in the required redis backend.
    Any changes to the masters configuration will be synced to the redis backend.
    Slaves will check in an configurabe interval if any changes were made to the
    configuration. If so, the new configuration will be imported from redis backend
    and a reload will be executed.

    Locally configured modules in slaves will not be overwritten by the master configuration.

    Configuration example:

    - module: ClusterConfiguration
      ignore_modules: [WebGui,LocalModule]    # <default: None; type: None||list; is: optional>
      redis_client: RedisClientName           # <type: string; is: required>
      redis_key: Cluster1:configuration       # <default: 'gambolputty:configuration'; type: string; is: optional>
      redis_ttl: 600                          # <default: 3600; type: integer; is: optional>
      interval: 10                            # <default: 60; type: integer; is: optional>
    """

    module_type = "stand_alone"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.master = True if self.cluster.my_master == None else False
        if self.master:
            self.update_config_func = self.getMasterConfigurationUpdateFunc()
        else:
            self.update_config_func = self.getSlaveConfigurationUpdateFunc()

    def getMasterConfigurationUpdateFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('interval'))
        def updateConfiguration():
            redis_configuration = self.redis_client.getValue(self.getConfigurationValue('redis_key'))
            running_configuration = self.filterIgnoredModules(self.gp.configuration)
            if running_configuration != redis_configuration:
                self.syncConfigurationToRedis(running_configuration)
        return updateConfiguration

    def getSlaveConfigurationUpdateFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('interval'))
        def updateConfiguration():
            redis_configuration = self.redis_client.getValue(self.getConfigurationValue('redis_key'))
            redis_configuration = self.filterIgnoredModules(redis_configuration)
            if type(redis_configuration) is not list:
                return
            running_configuration = self.filterIgnoredModules(self.gp.configuration)
            if running_configuration != redis_configuration:
                self.logger.info("%sGot new cluster configuration %s.%s" % (Utils.AnsiColors.LIGHTBLUE, self.getConfigurationValue('redis_key'), Utils.AnsiColors.ENDC))
                self.gp.setConfiguration(redis_configuration, merge=True)
                # Send signal to reload GambolPutty.
                signal.alarm(1)
        return updateConfiguration

    def filterIgnoredModules(self, configuration):
        filtered_configuration = []
        if self.getConfigurationValue('ignore_modules'):
            for module_info in self.gp.configuration:
                if 'module' not in module_info or module_info['module'] in self.getConfigurationValue('ignore_modules'):
                    continue
                filtered_configuration.append(module_info)
        return filtered_configuration

    def syncConfigurationToRedis(self, configuration):
        try:
            self.logger.info("%sUpdating %s cluster configuration.%s" % (Utils.AnsiColors.LIGHTBLUE, self.getConfigurationValue('redis_key'), Utils.AnsiColors.ENDC))
            self.redis_client.setValue(self.getConfigurationValue('redis_key'), configuration, self.getConfigurationValue('redis_ttl'))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("%sCould not store configuration data in redis. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, etype, evalue, Utils.AnsiColors.ENDC))
            pass

    def run(self):
        if not self.redis_client:
            self.logger.error('%sRedis backend for clustered configuration not available.%s' % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
            self.gp.shutDown()
            return
        self.update_config_func()

