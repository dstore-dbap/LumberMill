#!/usr/bin/python
# -*- coding: UTF-8 -*-
import multiprocessing
import sys
import os
import signal
import time
import getopt
import logging.config
import yaml
import tornado.ioloop
import importlib
from collections import OrderedDict
import lumbermill.Utils as Utils
from lumbermill.ConfigurationValidator import ConfigurationValidator

# Conditional imports for python2/3
try:
    import Queue
except ImportError:
    import queue as Queue

module_dirs = ['input',
               'parser',
               'modifier',
               'misc',
               'output',
               'webserver',
               'cluster']

# Expand the include path to our libs and modules.
# TODO: Check for problems with similar named modules in different module directories.
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

class LumberMill():
    """
    A stream parser with configurable modules and message paths.

    LumberMill helps to parse text based streams by providing a framework of modules.
    These modules can be combined via a simple configuration in any way you like. Have
    a look at the example config lumbermill.conf.example in the conf folder.

    This is the main class that reads the configuration, includes the needed modules
    and connects them as configured.
    """

    def __init__(self, path_to_config_file):
        self.path_to_config_file = path_to_config_file
        self.alive = False
        self.child_processes = []
        self.main_process_pid = os.getpid()
        self.modules = OrderedDict()
        self.global_configuration = {'workers': multiprocessing.cpu_count() - 1,
                                     'queue_size': 20,
                                     'queue_buffer_size': 50,
                                     'logging': {'level': 'info',
                                                 'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                                 'filename': None,
                                                 'filemode': 'w'}}
        self.logger = logging.getLogger(self.__class__.__name__)
        success = self.setConfiguration(self.readConfiguration(self.path_to_config_file), merge=False)
        if not success:
            self.shutDown()

    def produceQueue(self, queue_type='simple', queue_max_size=20, queue_buffer_size=1):
        """Returns a queue with queue_max_size"""
        queue = None
        if queue_type == 'simple':
            queue =  Utils.BufferedQueue(queue=Queue.Queue(queue_max_size), buffersize=queue_buffer_size)
        if queue_type == 'multiprocess':
            # At the moment I ran into a problem with zmq.
            # This problem causes the performance to be comparable with the normal python multiprocessing.Queue.
            # To make things worse, the load balancing between multiple workers is better when using multiprocessing.Queue.
            # Update 28.04.2015: With pypy-2.5 and normal python, the load balancing problem seems to be gone. ZMQ is
            # still a bit faster (ca. ~15%).
            # TODO: Analyze this problem more thoroughly.
            if False and Utils.zmq_avaiable and Utils.msgpack_avaiable:
                  queue = Utils.ZeroMqMpQueue(queue_max_size)
            else:
                queue = multiprocessing.Queue(queue_max_size)
            queue = Utils.BufferedQueue(queue=queue, buffersize=queue_buffer_size)
        if not queue:
            self.logger.error("Could not produce requested queue %s." % (queue_type))
            self.shutDown()
        return queue

    def readConfiguration(self, path_to_config_file):
        """Loads and parses the configuration"""
        try:
            with open(path_to_config_file, "r") as configuration_file:
                self.raw_conf_file = configuration_file.read()
            configuration = yaml.load(self.raw_conf_file)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not read config file %s. Exception: %s, Error: %s." % (path_to_config_file, etype, evalue))
            usage()
            self.shutDown()
        return configuration

    def getConfigurationFilePath(self):
        return self.path_to_config_file

    def getConfiguration(self):
        return self.configuration

    def getRawConfiguration(self):
        return self.raw_conf_file

    def getWorkerCount(self):
        return self.global_configuration['workers']

    def setConfiguration(self, configuration, merge=True):
        configuration_errors = ConfigurationValidator().validateConfiguration(configuration)
        for configuration_error in configuration_errors:
            self.logger.error("Could not set configuration due to configuration errors.")
            self.logger.error(configuration_error)
            return False
        if merge:
            # If merge is true keep currently configured modules and only merge new ones.
            for module_info in configuration:
                if module_info not in self.configuration:
                    self.configuration.append(module_info)
        else:
            self.configuration = configuration
        return True

    def configureGlobal(self):
        """Merge custom global configuration values to default settings."""
        for idx, configuration in enumerate(self.configuration):
            if 'Global' in configuration:
                self.global_configuration = Utils.mergeNestedDicts(self.global_configuration, configuration['Global'])
                self.configuration.pop(idx)

    def configureLogging(self):
        # Logger configuration.
        if self.global_configuration['logging']['level'].lower() not in Utils.loglevel_string_to_loglevel_int:
            print("Loglevel unknown.")
            self.shutDown()
        log_level = Utils.loglevel_string_to_loglevel_int[self.global_configuration['logging']['level'].lower()]
        logging.basicConfig(level=log_level,
                            format=self.global_configuration['logging']['format'],
                            filename=self.global_configuration['logging']['filename'],
                            filemode=self.global_configuration['logging']['filemode'])
        if not self.global_configuration['logging']['filename']:
            logging.StreamHandler.emit = Utils.coloredConsoleLogging(logging.StreamHandler.emit)

    def initModule(self, module_name):
        """ Initalize a module."""
        self.logger.debug("Initializing module %s." % (module_name))
        instance = None
        try:
            module = importlib.import_module(module_name, 'LumberMill')
            #module = __import__(module_name, globals(), locals(), class_name, -1)
            module_class = getattr(module, module_name)
            instance = module_class(self)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, etype, evalue))
            self.shutDown()
        return instance

    def initModulesFromConfig(self):
        """ Initalize all modules from the current config."""
        # Init modules as defined in config
        for idx, module_info in enumerate(self.configuration):
            module_config = {}
            module_id = None
            if isinstance(module_info, dict):
                module_class_name = module_info.keys()[0]
                module_config = module_info[module_class_name]
                # Set module id. If the id field was used in configuration use it else use class name of module.
                try:
                    module_id = module_class_name if 'id' not in module_config else module_config['id']
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("Error in configuration file for module %s. Exception: %s, Error: %s. Please check configuration." % (module_class_name, etype, evalue))
                    self.shutDown()
            else:
                module_id = module_class_name = module_info
            counter = 1
            # Modules ids have to be unique. Add a counter like "_1" to id if it is already used.
            while module_id in self.modules:
                tmp_mod_name = module_id.split("_", 1)[0]
                module_id = "%s_%s" % (tmp_mod_name, counter)
                counter += 1
            # Ignore some reserved module names. At the moment this is just the Global keyword.
            if module_id in ['Global']:
                continue
            module_instances = []
            module_instance = self.initModule(module_class_name)
            module_instances.append(module_instance)
            self.modules[module_id] = {'idx': idx,
                                       'instances': module_instances,
                                       'type': module_instance.module_type,
                                       'configuration': module_config}

    def setDefaultReceivers(self):
        """
        Add default receivers if none are provided by configuration.

        To make configuration less complicated, a module does not need to provide a receivers setting.
        if receivers is not set, events are send to the next module in the configuration by default.
        This method takes care of setting the default receivers settings.
        """
        # Iterate over all configured modules ordered as they appear in the current configuration.
        for module_name, module_info in self.modules.items():
            # If receivers is configured we can skip to next module.
            if 'receivers' in module_info['configuration']:
                continue
            # Some module types do not have any receivers.
            if module_info['type'] in ['stand_alone', 'output']:
                module_info['configuration']['receivers'] = []
                continue
            # Break on last module since it can have no following receivers.
            if module_info['idx'] == len(self.modules) - 1:
                break
            # Set receiver to next module in config if no receivers were set.
            # Get next module in configuration.
            try:
                receiver_module_name = [nxt_mod_name for nxt_mod_name, nxt_mod_info in self.modules.items() if nxt_mod_info['idx'] == module_info['idx'] + 1][0]
            except:
                # Something is wrong with the configuration. Tell user.
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Error in configuration for module %s. Exception: %s, Error: %s. Please check configuration." % (module_name, etype, evalue))
                self.shutDown()
            # Some modules are not allowed to act as receivers. Exit if configuration is faulty.
            if self.modules[receiver_module_name]['type'] in ['stand_alone', 'input']:
                self.logger.error("Error in configuration. %s not allowed to act as receiver for events from %s. %s modules are not allowed as receivers. Please check configuration." % (receiver_module_name, module_name, self.modules[receiver_module_name]['type']))
                self.shutDown()
            module_info['configuration']['receivers'] = [receiver_module_name]

    def configureModules(self):
        """Call configuration method of module."""
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for module_instance in module_info['instances']:
                module_instance.configure(module_info['configuration'])

    def initEventStream(self):
        """
        Connect all modules.

        The configuration allows to connect the modules via the <receivers> parameter.
        As different types of modules exists (Base, Threaded, MultiProcess), connecting one modules output
        with its receivers input can be either direct or via a queue.
        TODO: To prevent loops a sanity check should be performed after all modules have been connected.
        """
        queues = {}
        # Iterate over all configured modules.
        for module_name, module_info in self.modules.items():
            sender_instance = module_info['instances'][0]
            for receiver_data in sender_instance.getConfigurationValue('receivers'):
                if not receiver_data:
                    break
                if isinstance(receiver_data, dict):
                    receiver_name, _ = iter(receiver_data.items()).next()
                else:
                    receiver_name = receiver_data
                if receiver_name not in self.modules:
                    self.logger.error("Could not add %s as receiver for %s. Module not found." % (receiver_name, module_name))
                    self.shutDown()
                # If we run multiprocessed and the module is not capable of running parallel, this module will only be
                # started in the main process. Connect the module via a queue to all receivers that can run forked.
                for receiver_instance in self.modules[receiver_name]['instances']:
                    if (self.global_configuration['workers'] > 1 and sender_instance.can_run_forked != receiver_instance.can_run_forked):
                        try:
                            queue = queues[receiver_name]
                        except KeyError:
                            queue = self.produceQueue('multiprocess', self.global_configuration['queue_size'], self.global_configuration['queue_buffer_size'])
                            queues[receiver_name] = queue
                        receiver_instance.setInputQueue(queue)
                # Add the receiver to senders. If a corresponding queue exist, use this else use the normal mod instance.
                for instance in module_info['instances']:
                    if receiver_name in queues:
                        self.logger.debug("%s will send its output to %s via a queue." % (module_name, receiver_name))
                        instance.addReceiver(receiver_name, queues[receiver_name])
                    else:
                        self.logger.debug("%s will send its output directly to %s." % (module_name, receiver_name))
                        instance.addReceiver(receiver_name, receiver_instance)

    def getModuleInfoById(self, module_id, silent=True):
        """
        Get a module by its id.

        Some modules need access to other modules. This method will return the module referenced by its id.
        """
        try:
            return self.modules[module_id]
        except KeyError:
            if not silent:
                self.logger.error("Get module by id %s failed. No such module." % (module_id))
            return None

    def initModulesAfterFork(self):
        """
        All modules are completely configured, call modules initAfterFork method.
        initAfterFork is used to (re)init modules after a process fork.
        BufferedQueue i.e. uses a thread to flush its buffer in given intervals.
        The thread will not survive a fork of the main process. So we need to start this
        after the fork was executed.
        """
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for instance in module_info['instances']:
                if instance.can_run_forked:
                    instance.initAfterFork()
                #else:
                #    print("Not calling initAfterFork on %s." % module_name)

    def runModules(self):
        """
        Start the configured modules if they poll queues.
        """
        # All modules are completely configured, call modules run method if it exists.
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            if self.is_master():
                start_message = "%s - %s" % (module_name, module_info['instances'][0].getStartMessage())
                self.logger.info(start_message)
            for instance in module_info['instances']:
                # Some modules, mostly input modules, use unique io devices, that can not be polled from multiple
                # threads/processes. These modules will only be started once from the master process and the output
                # will be send via queue to the other processes.
                if not self.is_master() and not instance.can_run_forked:
                    continue
                # The default 'start' method of threading.Thread/mp will call the 'run' method of the module.
                # The module itself can then decide if it wants to be run as thread. If not, it has to return False to let Gambolputty know.
                if getattr(instance, "start", None): # and (instance.getInputQueue() or instance.module_type in ['stand_alone', 'input'])
                    started = instance.start()
                    if started:
                        self.logger.debug("Starting module %s as thread via %s.start()." % (module_name, module_name))
                    continue

    def getAllQueues(self):
        """ Get all configured queues to check for pending events. """
        module_queues = {}
        for module_name, module_info in self.modules.items():
            instance = module_info['instances'][0]
            if not hasattr(instance, 'getInputQueue') or not instance.getInputQueue():
                continue
            module_queues[module_name] = instance.getInputQueue()
        return module_queues

    def is_master(self):
        return os.getpid() == self.main_process_pid

    def configTest(self):
        self.logger.info("Running configuration test for %s." % self.path_to_config_file)
        self.configureGlobal()
        self.configureLogging()
        self.initModulesFromConfig()
        self.setDefaultReceivers()
        self.configureModules()
        self.initEventStream()
        self.logger.info("Done...")
        return

    def start(self):
        self.configureGlobal()
        self.configureLogging()
        self.initModulesFromConfig()
        self.setDefaultReceivers()
        self.configureModules()
        self.initEventStream()
        self.runWorkers()

    def runWorkers(self):
        for i in range(1, self.global_configuration['workers']):
            worker = multiprocessing.Process(target=self.run)
            worker.start()
            self.child_processes.append(worker)
        self.run()

    def run(self):
        # Catch Keyboard interrupt here. Catching the signal seems
        # to be more reliable then using try/except when running
        # multiple processes under pypy.
        # Register SIGINT to call shutDown for all processes.
        signal.signal(signal.SIGINT, self.shutDown)
        if self.is_master():
            # Register SIGALARM only for master process. This will take care to kill all subprocesses.
            signal.signal(signal.SIGALRM, self.restart)
        self.alive = True
        self.initModulesAfterFork()
        self.runModules()
        if self.is_master():
            self.logger.info("LumberMill started with %s processes(%s)." % (len(self.child_processes) + 1, os.getpid()))
        tornado.ioloop.IOLoop.instance().start()

    def restart(self, signum=False, frame=False):
        for worker in list(self.child_processes):
            os.kill(worker.pid, signal.SIGINT)
            worker.join()
            self.child_processes.remove(worker)
        self.logger.info("Restarting LumberMill.")
        self.shutDown()
        time.sleep(5)
        Utils.restartMainProcess()

    def shutDown(self, signum=False, frame=False):
        # If a module started a subprocess, the whole lumbermill parent process gets forked.
        # As a result, the forked lumbermill process will also catch SIGINT||SIGALARM.
        if self.is_master():
            self.logger.info("Shutting down LumberMill.")
        if not self.alive:
            sys.exit(0)
        self.alive = False
        self.shutDownModules()
        Utils.TimedFunctionManager.stopTimedFunctions()
        tornado.ioloop.IOLoop.instance().stop()
        if self.is_master():
            self.logger.info("Shutdown complete.")

    def shutDownModules(self):
        # Shutdown all input modules.
        for module_name, module_info in self.modules.items():
            for instance in module_info['instances']:
                if instance.module_type == "input":
                    instance.shutDown()
        # Get all configured queues to check for pending events.
        module_queues = self.getAllQueues()
        if len(module_queues) > 0:
            wait_loops = 0
            while wait_loops < 5:
                wait_loops += 1
                events_in_queues = 0
                for module_name, queue in module_queues.items():
                    events_in_queues += queue.qsize()
                if events_in_queues > 0:
                    # Give remaining queued events some time to finish.
                    if self.is_master():
                        self.logger.info("%s event(s) still in flight. Waiting %s secs. Press ctrl+c again to exit directly." % (events_in_queues, (.5 * wait_loops)))
                    time.sleep(.5 * wait_loops)
                    continue
                break
        # Shutdown all other modules.
        for module_name, module_info in self.modules.items():
            for instance in module_info['instances']:
                if instance.module_type != "input":
                    instance.shutDown()

def usage():
    print('Usage: ' + sys.argv[0] + ' -c <path/to/config.conf> --configtest')

def main():
    path_to_config_file = ""
    run_configtest = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "configtest", "conf="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--conf"):
            path_to_config_file = arg
        elif opt in ("--configtest"):
            run_configtest = True
    gp = LumberMill(path_to_config_file)
    if run_configtest:
        gp.configTest()
    else:
        gp.start()

if __name__ == '__main__':
    main()



