#!/usr/bin/python
# -*- coding: UTF-8 -*-
module_dirs = {'message_inputs': {},
               'message_classifiers': {},
               'message_parsers': {},
               'field_modifiers': {},
               'message_outputs': {},
               'misc': {}}

import sys
import os
import time
import getopt
import logging.config
import Queue
import threading
import yaml
import lumberjack.BaseModule as BaseModule

# Expand the include path to our libs and modules.
# TODO: Check for problems with similar named modules in 
# different module directories.
pathname = os.path.abspath(__file__)
pathname = pathname[:pathname.rfind("/")]
sys.path.append(pathname + "/lumberjack")
[sys.path.append(pathname + "/lumberjack/" + mod_dir) for mod_dir in module_dirs]


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


class LumberJack:
    """A stream parser with configurable modules and message paths.
    
    LumberJack helps to parse text based streams by providing a framework of modules.
    These modules can be combined via a simple configuration in any way you like. Have
    a look at the example config lumberjack.conf.example in the conf folder.
    
    This is the main class that reads the configuration, includes the needed modules
    and connects them via queues as configured.
    """

    def __init__(self, path_to_config_file):
        self.alive = True
        self.modules = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.readConfiguration(path_to_config_file)

    def _produceQueue(self, queue_max_size=100):
        """Returns a queue with queue_max_size"""
        return Queue.Queue(queue_max_size)


    def _initModule(self, module_name):
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
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, etype, evalue))
            sys.exit(255)
        return instance

    def _runModules(self):
        """Start the configured modules
        
        Start each module in its own thread
        """
        # All modules are completely configured, call modules run method if it exists.
        for module_name, instances in self.modules.iteritems():
            for instance in instances:
                name = instance['alias'] if 'alias' in instance else module_name
                self.logger.debug("Calling start/run method of %s." % name)
                try:
                    if (isinstance(instance["instance"], threading.Thread)):
                        instance["instance"].start()
                    else:
                        instance["instance"].run()
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.warning(
                        "Error calling run/start method of %s. Exception: %s, Error: %s." % (name, etype, evalue))

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
            self.logger.error(
                "Could not read config file %s. Exception: %s, Error: %s." % (path_to_config_file, etype, evalue))
            sys.exit(255)

    def initModulesFromConfig(self):
        """ Initalize all modules from the current config.
        
            The pool size defines how many threads for this module will be started.
        """
        # Init modules as defined in config
        for module_info in self.configuration:
            pool_size = module_info['pool-size'] if "pool-size" in module_info else 1
            for _ in range(pool_size):
                module_instance = self._initModule(module_info['module'])
                # Set module name. Use alias if it was set in configuration.
                module_name = module_info['module'] if 'alias' not in module_info else module_info['alias']
                # Call setup of module if method is implemented and pass reference to Lumberjack instance
                try:
                    module_instance.setup()
                except AttributeError:
                    pass
                # Call configuration of module
                if 'configuration' in module_info:
                    try:
                        configuration_sucessful = module_instance.configure(module_info['configuration'])
                        if configuration_sucessful == False:
                            self.logger.error("Could not configure module %s. Please check log for error messages.") % module_info['module']
                            self.shutDown()
                            break
                    except:
                        etype, evalue, etb = sys.exc_info()
                        self.logger.error("Could not configure module %s. Exception: %s, Error: %s." % (module_info['module'], etype, evalue))
                        self.shutDown()
                        break
                try:
                    self.modules[module_name].append({'instance': module_instance,
                                                      'configuration': module_info[
                                                          'configuration'] if 'configuration' in module_info else None,
                                                      'receivers': module_info[
                                                          'receivers'] if 'receivers' in module_info else None})
                except:
                    self.modules[module_name] = [{'instance': module_instance,
                                                  'configuration': module_info[
                                                      'configuration'] if 'configuration' in module_info else None,
                                                  'receivers': module_info[
                                                      'receivers'] if 'receivers' in module_info else None}]

    def initEventStream(self):
        """ Connect modules via queues.
        
        The configuartion allows to connect the modules via the <receivers> parameter.
        This method creates the queues and connects the modules via this queues.
        To prevent loops a sanity check is performed before all modules are connected.
        """
        # All modules are initialized, connect producer and consumers via a queue.
        queues = {}
        module_loop_buffer = []
        for module_name, instances in self.modules.iteritems():
            for instance in instances:
                if "receivers" not in instance or instance['receivers'] is None:
                    continue
                for receiver_data in instance["receivers"]:
                    filter_by_marker = False
                    filter_by_field = False
                    if isinstance(receiver_data, str):
                        receiver_name = receiver_data
                    else:
                        receiver_name, config = receiver_data.iteritems().next()
                        if 'filter-by-marker' in config:
                            filter_by_marker = config['filter-by-marker']
                        if 'filter-by-field' in config:
                            filter_by_field = config['filter-by-field']
                    self.logger.debug("%s will send its output to %s." % (module_name, receiver_name))
                    if receiver_name not in self.modules:
                        self.logger.warning(
                            "Could not add %s as receiver for %s. Module not found." % (receiver_name, module_name))
                        continue
                    for receiver_instance in self.modules[receiver_name]:
                        if receiver_name not in queues:
                            queues[receiver_name] = self._produceQueue()
                        try:
                            if not receiver_instance["instance"].getInputQueue():
                                receiver_instance["instance"].setInputQueue(queues[receiver_name])
                            instance["instance"].addOutputQueue(queues[receiver_name], filter_by_marker, filter_by_field)
                        except AttributeError:
                            self.logger.error(
                                "%s can not be set as receiver. It seems to be incompatible." % receiver_name)
                            # Build a node structure used for the loop test.
                        try:
                            node = (node for node in module_loop_buffer if node.module == instance["instance"]).next()
                        except:
                            node = Node(instance["instance"])
                            module_loop_buffer.append(node)
                        try:
                            receiver_node = (node for node in module_loop_buffer if \
                                             node.module == receiver_instance["instance"]).next()
                        except:
                            receiver_node = Node(receiver_instance["instance"])
                            module_loop_buffer.append(receiver_node)
                        node.addChild(receiver_node)
        # Check if the configuration produces a loop.
        # This code can definitely be made more efficient...  
        for node in module_loop_buffer:
            for loop in hasLoop(node, stack=[]):
                self.logger.error(
                    "Chaining of modules produced a loop. Check configuration. Module: %s." % loop.module.__class__.__name__)
                sys.exit(255)

    def run(self):
        self._runModules()
        try:
            while self.alive:
                time.sleep(.1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            # TODO: Get all event input modules and shut those down first. Then wait till all events in all queues (BaseModule.BaseModule.messages_in_queues) have been proccessed.
            sys.exit()

    def shutDown(self):
        self.alive = False


def usage():
    print 'Usage: ' + sys.argv[0] + ' -c <path/to/config.conf>'

if "__main__" == __name__:
    config_pathname = os.path.abspath(sys.argv[0])
    config_pathname = config_pathname[:config_pathname.rfind("/")] + "/conf"
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
    lj = LumberJack(path_to_config_file)
    lj.initModulesFromConfig()
    lj.initEventStream()
    lj.run()        