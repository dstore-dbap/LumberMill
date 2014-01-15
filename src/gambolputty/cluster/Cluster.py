# -*- coding: utf-8 -*-
import multiprocessing
import sys
import BaseModule
import threading
import Utils
from Decorators import ModuleDocstringParser



@ModuleDocstringParser
class Cluster(BaseModule.BaseModule):
    """
    Container module for all cluster related plugins.

    Configuration example:

    - module: Cluster
      master: master.gp.server   # <default: None; type: None||string; is: optional>
    """

    module_type = "stand_alone"
    """ Set module type. """

    def configure(self, configuration):
        self.modules = {}
        self.my_master = self.getConfigurationValue('master')
        for idx, module_info in enumerate(configuration['submodules']):
            module_instance = self.gp.initModule(module_info['module'])
            module_instance.cluster = self
            # Call configuration of module
            try:
                module_instance.configure(module_info)
            except Exception, e:
                etype, evalue, etb = sys.exc_info()
                self.logger.warn("%sCould not configure module %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, module_info['module'], etype, evalue, Utils.AnsiColors.ENDC))
                pass
            self.modules[module_info['module']] = {'idx': idx,
                                                   'instances': [module_instance],
                                                   'type': module_instance.module_type,
                                                   'queue_size': module_info[ 'queue_size'] if 'queue_size' in module_info else self.gp.default_queue_size,
                                                   'configuration': module_info}

    def run(self):
        for module_name, module_info in self.modules.iteritems():
            self.logger.info("%sUsing submodule %s%s." % (Utils.AnsiColors.LIGHTBLUE, module_name, Utils.AnsiColors.ENDC))
            instance = module_info['instances'][0]
            try:
                if isinstance(instance, threading.Thread) or isinstance(instance, multiprocessing.Process):
                    # The default 'start' method of threading.Thread will call the 'run' method of the module.
                    instance.start()
                elif getattr(instance, "run", None):
                    # Call 'run' method directly.
                    instance.run()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("%sError calling run/start method of %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, module_name, etype, evalue, Utils.AnsiColors.ENDC))