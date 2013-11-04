# -*- coding: utf-8 -*-
import sys
import traceback
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class ModuleContainer(BaseThreadedModule.BaseThreadedModule):

    def initModule(self, module_name):
        """ Initalize a module."""
        self.logger.debug("Initializing module %s." % (module_name))
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class(self.gp)
        except Exception, e:
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, Exception, e))
            self.gp.shutDown()
        return instance

    def configure(self, configuration):
        self.modules = []
        for module_configuration in configuration:
            module_instance = self.initModule(module_configuration['module'])
            # Call configuration of module
            if 'configuration' in module_configuration:
                try:
                    module_instance.configure(module_configuration['configuration'])
                except Exception, e:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warn("Could not configure module %s. Exception: %s, Error: %s." % (module_configuration['module'], etype, evalue))
                    traceback.print_exception(etype, evalue, etb)
                    pass
            self.modules.append(module_instance)

    def run(self):
        for module in self.modules:
            # Init redis client if it is configured by the module
            if 'redis_client' in module.configuration_data:
                module.initRedisClient()
        # Call parent run method
        BaseThreadedModule.BaseThreadedModule.run(self)

    def handleData(self, event):
        for module in self.modules:
            for event in module.handleData(event if 'work_on_copy' not in module.configuration_data else event.copy()):
                pass
        yield event
