import sys
import traceback
import BaseModule


class ModuleContainer(BaseModule.BaseModule):

    def initModule(self, module_name):
        """ Initalize a module."""
        self.logger.debug("Initializing module %s." % (module_name))
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class(self.gp)
            # Call setup of module if method is implemented
            try:
                instance.setup()
            except AttributeError:
                pass
        except Exception, e:
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, Exception, e))
            self.shutDown()
        return instance

    def configure(self, configuration):
        self.modules = []
        for module_configuration in configuration:
            module_instance = self.initModule(module_configuration['module'])
            # Call setup of module if method is implemented and pass reference to GambolPutty instance
            try:
                module_instance.setup()
            except AttributeError:
                pass
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

    def handleData(self, data):
        for module in self.modules:
            data = module.handleData(data) #  if 'work-on-copy' not in module.configuration_data else data.copy()
        return data