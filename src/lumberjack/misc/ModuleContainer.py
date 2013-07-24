import sys
import thread
import traceback
import BaseModule


class ModuleContainer(BaseModule.BaseModule):

    def initModule(self, module_name):
        """ Initalize a module."""
        self.logger.debug("Initializing module %s." % (module_name))
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class()
            # Call setup of module if method is implemented and pass reference to Lumberjack instance
            try:
                instance.setup(self.lj)
            except AttributeError:
                    pass
        except Exception, e:
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, Exception, e))
            self.lj.shutDown()
        return instance

    def configure(self, configuration):
        self.modules = []
        self.config = configuration
        for module_info in self.config:
            module_instance = self.initModule(module_info['module'])
            # Call configuration of module
            if 'configuration' in module_info:
                try:
                    module_instance.configure(module_info['configuration'])
                except Exception, e:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warn("Could not configure module %s. Exception: %s, Error: %s." % (module_info['module'], etype, evalue))
                    traceback.print_exception(etype, evalue, etb)
                    pass
            self.modules.append(module_instance)
              

    def handleData(self, data):
        for module in self.modules:
            data = module.handleData(data)
        return data