#!/usr/bin/python
# -*- coding: UTF-8 -*-
import Utils
import BaseQueue
import ConfigurationValidator
import StatisticCollector as StatisticCollector
import collections

module_dirs = ['input',
               'parser',
               'modifier',
               'misc',
               'output']

import sys
import os
import time
import getopt
import logging.config
import threading
import yaml
import pprint

# Expand the include path to our libs and modules.
# TODO: Check for problems with similar named modules in 
# different module directories.
pathname = os.path.abspath(__file__)
pathname = pathname[:pathname.rfind("/")]
[sys.path.append(pathname + "/" + mod_dir) for mod_dir in module_dirs]

class Node:
    def __init__(self, module):
        self.children = []
        self.module = module

    def addChild(self, node):
        self.children.append(node)

def hasLoop(node, stack=[]):
    if not stack:
        stack.append(node)
    for current_node in node.children:
        if current_node in stack:
            return [current_node]
        stack.append(current_node)
        return hasLoop(current_node, stack)
    return []


class GambolPutty:
    """A stream parser with configurable modules and message paths.
    
    GambolPutty helps to parse text based streams by providing a framework of modules.
    These modules can be combined via a simple configuration in any way you like. Have
    a look at the example config gambolputty.conf.example in the conf folder.
    
    This is the main class that reads the configuration, includes the needed modules
    and connects them via queues as configured.
    """

    def __init__(self, path_to_config_file):
        self.is_alive = True
        self.modules = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.readConfiguration(path_to_config_file)

    def produceQueue(self, queue_max_size=0):
        """Returns a queue with queue_max_size"""
        return BaseQueue.BaseQueue(queue_max_size)

    def readConfiguration(self, path_to_config_file):
        """Loads and parses the configuration

        :param path_to_config_file: path to the configuration file
        :type path_to_config_file: str
        """
        try:
            conf_file = open(path_to_config_file)
            self.configuration = yaml.load(conf_file)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not read config file %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, path_to_config_file, etype, evalue, Utils.AnsiColors.ENDC))
            sys.exit(255)

    def initModule(self, module_name):
        """ Initalize a module.
        
        :param module_name: module to initialize
        :type module_name: string
        """
        self.logger.debug("Initializing module %s." % (module_name))
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class(self)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not init module %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, module_name, etype, evalue, Utils.AnsiColors.ENDC))
            sys.exit(255)
        return instance

    def runModules(self):
        """Start the configured modules
        
        Start each module in its own thread
        """
        # All modules are completely configured, call modules run method if it exists.
        #pprint.pprint(self.modules.items())
        #pprint.pprint(sorted(self.modules.items(), key=lambda x: x[1]['idx']))
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for instance in module_info['instances']:
                name = module_info['alias'] if 'alias' in module_info else module_name
                # Init redis client if it is configured by the module
                if 'redis_client' in instance.configuration_data:
                    instance.initRedisClient()
                self.logger.debug("Calling start/run method of %s." % name)
                try:
                    if (isinstance(instance, threading.Thread)):
                        instance.start()
                    else:
                        instance.run()
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warning("Error calling run/start method of %s. Exception: %s, Error: %s." % (name, etype, evalue))
            self.logger.info("%sStarted module %s with pool size of %s%s" % (Utils.AnsiColors.LIGHTBLUE , module_name, len(module_info['instances']),Utils.AnsiColors.ENDC))

    def initModulesFromConfig(self):
        """ Initalize all modules from the current config.
        
            The pool size defines how many threads for this module will be started.
        """
        configurationValidator = ConfigurationValidator.ConfigurationValidator()
        # Init modules as defined in config
        for idx,module_info in enumerate(self.configuration):
            pool_size = module_info['pool_size'] if "pool_size" in module_info else 1
            module_instances = []
            for _ in range(pool_size):
                module_instance = self.initModule(module_info['module'])
                # Set module name. Use alias if it was set in configuration.
                module_name = module_info['module'] if 'alias' not in module_info else module_info['alias']
                # Call configuration of module
                configuration = module_info['configuration'] if 'configuration' in module_info else {}
                try:
                    module_instance.configure(configuration)
                    configuration_errors = configurationValidator.validateModuleInstance(module_instance)
                    if configuration_errors:
                        self.logger.error("%sCould not configure module %s. Problems: %s.%s" % (Utils.AnsiColors.FAIL, module_info['module'], configuration_errors, Utils.AnsiColors.ENDC))
                        self.shutDown()
                        break
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("%sCould not configure module %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.FAIL, module_info['module'], etype, evalue, Utils.AnsiColors.ENDC))
                    self.shutDown()
                    break
                module_instances.append(module_instance)
            self.modules[module_name] = {'idx': idx,
                                         'instances': module_instances,
                                         'type': module_instance.module_type,
                                         'configuration': module_info['configuration'] if 'configuration' in module_info else None,
                                         'receivers': module_info['receivers'] if 'receivers' in module_info else None}
            """
            except:
                self.modules[module_name] = [{'instance': module_instance,
                                              'configuration': module_info[
                                                  'configuration'] if 'configuration' in module_info else None,
                                              'receivers': module_info[
                                                  'receivers'] if 'receivers' in module_info else None}]
            """

    def initEventStream(self):
        """ Connect modules via queues.
        
        The configuartion allows to connect the modules via the <receivers> parameter.
        This method creates the queues and connects the modules via this queues.
        To prevent loops a sanity check is performed before all modules are connected.
        """
        # All modules are initialized, connect producer and consumers via a queue.
        queues = {}
        module_loop_buffer = []
        for module_name, module_info in self.modules.iteritems():
            for instance in module_info['instances']:
                if "receivers" not in module_info or module_info['receivers'] is None:
                    continue
                for receiver_data in module_info["receivers"]:
                    receiver_filter_config = {}
                    if isinstance(receiver_data, str):
                        receiver_name = receiver_data
                    else:
                        receiver_name, receiver_filter_config = receiver_data.iteritems().next()
                    self.logger.debug("%s will send its output to %s." % (module_name, receiver_name))
                    if receiver_name not in self.modules:
                        self.logger.warning(
                            "%sCould not add %s as receiver for %s. Module not found.%s" % (Utils.AnsiColors.WARNING, receiver_name, module_name, Utils.AnsiColors.ENDC))
                        continue
                    for receiver_instance in self.modules[receiver_name]['instances']:
                        if receiver_name not in queues:
                            queues[receiver_name] = self.produceQueue()
                        try:
                            if not receiver_instance.getInputQueue():
                                receiver_instance.setInputQueue(queues[receiver_name])
                            filter = receiver_filter_config['filter'] if receiver_filter_config and 'filter' in receiver_filter_config else False
                            instance.addOutputQueue(queues[receiver_name], filter)
                        except AttributeError:
                            self.logger.error(
                                "%s%s can not be set as receiver. It seems to be incompatible." % (Utils.AnsiColors.WARNING, receiver_name, Utils.AnsiColors.ENDC))
                            # Build a node structure used for the loop test.
                        try:
                            node = (node for node in module_loop_buffer if node.module == instance).next()
                        except:
                            node = Node(instance)
                            module_loop_buffer.append(node)
                        try:
                            receiver_node = (node for node in module_loop_buffer if \
                                             node.module == receiver_instance).next()
                        except:
                            receiver_node = Node(receiver_instance)
                            module_loop_buffer.append(receiver_node)
                        node.addChild(receiver_node)
        # Check if the configuration produces a loop.
        # This code can definitely be made more efficient...  
        for node in module_loop_buffer:
            for loop in hasLoop(node, stack=[]):
                self.logger.error(
                    "%sChaining of modules produced a loop. Check configuration. Module: %s.%s" % (Utils.AnsiColors.FAIL, loop.module.__class__.__name__, Utils.AnsiColors.ENDC))
                self.shutDown()

    def run(self):
        self.runModules()
        try:
            while self.is_alive:
                time.sleep(.1)
        except KeyboardInterrupt:
            self.shutDown()

    def shutDown(self):
        # Shutdown all input modules.
        for module_name, module_info in self.modules.iteritems():
            for instance in module_info['instances']:
                if instance.module_type == "input":
                    self.logger.info("%sShutting down input module: %s.%s" % (Utils.AnsiColors.LIGHTBLUE, module_name, Utils.AnsiColors.ENDC))
                    instance.shutDown()
        # Wait for all events in queue to be processed but limit number of shutdown tries to avoid endless loop.
        shutdown_tries = 0
        while (StatisticCollector.StatisticCollector().getCounter('events_in_queues') > 0 or StatisticCollector.StatisticCollector().getCounter('events_in_process') > 0) and shutdown_tries <= 20:
            #pprint.pprint(StatisticCollector.StatisticCollector().counter_stats_per_module)
            self.logger.info("%sWaiting for pending events. Events waiting in queues: %s. Events in process: %s.%s" % (Utils.AnsiColors.LIGHTBLUE, BaseQueue.BaseQueue.messages_in_queues, StatisticCollector.StatisticCollector().getCounter('events_in_process'), Utils.AnsiColors.ENDC))
            shutdown_tries += 1
            time.sleep(.3)
        self.is_alive = False
        sys.exit()

def usage():
    print 'Usage: ' + sys.argv[0] + ' -c <path/to/config.conf>'

if "__main__" == __name__:
    config_pathname = os.path.abspath(sys.argv[0])
    config_pathname = config_pathname[:config_pathname.rfind("/")] + "/../conf"
    logging.config.fileConfig('%s/logger.conf' % config_pathname)
    path_to_config_file = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "conf="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--conf"):
            path_to_config_file = arg
    if not path_to_config_file:
        usage()
        sys.exit(2)
    gp = GambolPutty(path_to_config_file)
    gp.initModulesFromConfig()
    gp.initEventStream()
    gp.run()