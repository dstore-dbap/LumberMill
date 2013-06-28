#!/usr/bin/python
# -*- coding: UTF-8 -*-
########################################################
# 
########################################################

module_dirs = {'message_inputs': {},
               'message_classifiers': {},
               'message_parsers': {},
               'field_modifiers': {},
               'message_outputs': {},
               'misc': {}}

import sys
import os
import time
import logging
import logging.config
import Queue
import threading
import yaml

# Expand the include path to out libs and modules.
# TODO: Check for problems with similar named modules in 
# different module directories.
pathname = os.path.abspath(__file__)
pathname = pathname[:pathname.rfind("/")]
sys.path.append(pathname+"/lib");
[sys.path.append(pathname+"/lib/"+mod_dir) for mod_dir in module_dirs]

class LumberJack:

    worker_pool = False
    modules = {}
    
    def __init__(self):
        # get our logging facility
        self.logger = logging.getLogger(self.__class__.__name__)
        self.readConfiguration()

    def produceQueue(queue_max_size = 25):
        return Queue.Queue(queue_max_size)
 
    def readConfiguration(self):
        try:
            conf_file=open("conf/lumberjack.conf")
            self.configuration =  yaml.load(conf_file)
        except Exception,e:
            self.logger.error("Could not read config file in ./conf/lumberjack.conf. Exception: %s, Error: %s." % (Exception,e))
            sys.exit(255)
         
    def initModulesFromConfig(self, section_type="default"):
        """ Initalize all modules from the current config.
            To initalize all needed modules, parse the config file and find all
            modules that will be needed to run properly.
            """
        # Init modules as defined in config
        for module_info in self.configuration:
            pool_size = module_info['pool-size'] if "pool-size" in module_info else 1
            for _ in range(pool_size):
                module_instance = self.initModule(module_info['module'])
                module_name = module_info['module']
                # Use alias if it was set in configuration.
                if 'alias' in module_info:
                    module_name = module_info['alias']
                # Call configuration of module
                if 'configuration' in module_info:
                    try:
                        module_instance.configure(module_info['configuration'])
                    except Exception,e:
                        self.logger.warn("Could not configure module %s. Exception: %s, Error: %s." % (module_info['module'], Exception, e))
                        pass
                try:
                    self.modules[module_name].append({'instance': module_instance, 
                                                      'configuration': module_info['configuration'] if 'configuration' in module_info else None, 
                                                      'receivers': module_info['receivers'] if 'receivers' in module_info else None})
                except:
                    self.modules[module_name] = [{'instance': module_instance,
                                                  'configuration': module_info['configuration'] if 'configuration' in module_info else None,
                                                  'receivers': module_info['receivers'] if 'receivers' in module_info else None}]
        
    def initModule(self, module_name):
        """ Initalize a module."""
        #try:
        self.logger.debug("Initializing module %s." % (module_name))
        #main_module = __import__("lib.%s" % module_type, fromlist=[class_name])
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class()
        except Exception, e:
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, Exception, e))
            sys.exit(255)
        return instance

    def initEventStream(self):
        """ Connect modules via queues."""
        # All modules are initialized, connect producer and consumers via a queue.
        queues = {}
        for module_name,instances in self.modules.iteritems():
            for instance in instances:
                if "receivers" not in instance or instance['receivers'] is None:
                    continue
                for receiver_data in instance["receivers"]:
                    if isinstance(receiver_data, str):
                        receiver_name = receiver_data
                        filter_by_marker = False
                    else:
                        receiver_name, config = receiver_data.iteritems().next()
                        filter_by_marker = config['filter-by-marker']
                    name = instance['alias'] if 'alias' in instance else module_name
                    self.logger.debug("%s will send its output to %s." % (name, receiver_name))
                    if receiver_name not in self.modules:
                        self.logger.warning("Could not add %s as receiver for %s. Module not found." % (receiver_name, name))
                        continue
                    for receiver_instance in self.modules[receiver_name]:
                        if receiver_name not in queues:
                            queues[receiver_name] = self.produceQueue()
                        if not receiver_instance["instance"].getInputQueue():
                            receiver_instance["instance"].setInputQueue(queues[receiver_name])
                        instance["instance"].addOutputQueue(queues[receiver_name], filter_by_marker)
 
    def runModules(self):                           
        # All modules are completely configured, call modules run method if it exists.
        for module_name, instances in self.modules.iteritems():
            for instance in instances:
                name = instance['alias'] if 'alias' in instance else module_name
                self.logger.debug("Calling start/run method of %s." % name)
                try:
                    if(isinstance(instance["instance"], threading.Thread)):
                        instance["instance"].start()
                    else:
                        instance["instance"].run()
                except Exception,e:
                    self.logger.warning("Error calling run/start method of %s. Exception: %s, Error: %s." % (name, Exception, e))

if "__main__" == __name__:
    config_pathname = os.path.abspath(sys.argv[0])
    config_pathname = config_pathname[:config_pathname.rfind("/")]+"/conf"
    logging.config.fileConfig('%s/logger.conf' % config_pathname)
    lj = LumberJack()
    lj.initModulesFromConfig()
    lj.initEventStream()
    lj.runModules()
    while True:
        time.sleep(1)