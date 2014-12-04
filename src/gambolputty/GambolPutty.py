#!/usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import Utils
import multiprocessing
import sys
import os
import signal
import time
import getopt
import logging.config
import yaml
import tornado.ioloop
from collections import defaultdict
import BaseMultiProcessModule
import ConfigurationValidator

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

class GambolPutty():
    """
    A stream parser with configurable modules and message paths.

    GambolPutty helps to parse text based streams by providing a framework of modules.
    These modules can be combined via a simple configuration in any way you like. Have
    a look at the example config gambolputty.conf.example in the conf folder.

    This is the main class that reads the configuration, includes the needed modules
    and connects them as configured.
    """

    def __init__(self, path_to_config_file):
        self.alive = False
        self.child_processes = []
        self.main_process_pid = os.getpid()
        self.modules = {}
        self.message_callbacks = defaultdict(lambda: [])
        self.logger = logging.getLogger(self.__class__.__name__)
        if path_to_config_file:
            success = self.setConfiguration(self.readConfiguration(path_to_config_file), merge=False)
            if not success:
                self.shutDown()

    def produceQueue(self, queue_type='simple', queue_max_size=20, queue_buffer_size=1):
        """Returns a queue with queue_max_size"""
        queue = None
        if queue_type == 'simple':
            queue =  Queue.Queue(queue_max_size)
        if queue_type == 'multiprocess':
            # At the moment I ran into a problem with zmq.
            # This problem causes the performance to be comparable with the normal python multiprocessing.Queue.
            # To make things worse, the load balancing between multiple workers is better when using multiprocessing.Queue.
            # TODO: Analyze this problem more thoroughly.
            #if Utils.zmq_avaiable and Utils.msgpack_avaiable:
            #    queue = Utils.ZeroMqMpQueue(queue_max_size)
            #else:
            #    queue = multiprocessing.Queue(queue_max_size)
            queue = multiprocessing.Queue(queue_max_size)
        if not queue:
            self.logger.error("Could not produce requested queue %s." % (queue_type))
            self.shutDown()
        return queue

    def readConfiguration(self, path_to_config_file):
        """Loads and parses the configuration"""
        try:
            conf_file = open(path_to_config_file)
            configuration = yaml.load(conf_file)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not read config file %s. Exception: %s, Error: %s." % (path_to_config_file, etype, evalue))
            self.shutDown()
        return configuration

    def getConfiguration(self):
        return self.configuration

    def setConfiguration(self, configuration, merge=True):
        configuration_errors = ConfigurationValidator.ConfigurationValidator().validateConfiguration(configuration)
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
        """Set some global configuration values."""
        # CPU count - 1 as we want to leave at least one cpu for other tasks.
        self.workers = multiprocessing.cpu_count() - 1
        self.queue_size = 20
        self.queue_buffer_size = 50
        for idx, configuration in enumerate(self.configuration):
            if 'Global' in configuration:
                configuration = configuration['Global']
                if 'workers' in configuration:
                    self.workers = configuration['workers']
                if 'queue_size' in configuration:
                    self.queue_size = configuration['queue_size']
                if 'queue_buffer_size' in configuration:
                    self.queue_buffer_size = configuration['queue_buffer_size']
                self.configuration.pop(idx)
                break

    def initModule(self, module_name):
        """ Initalize a module."""
        self.logger.debug("Initializing module %s." % (module_name))
        instance = None
        try:
            module = __import__(module_name)
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
                # Set module name. Use id if it was set in configuration.
                try:
                    module_id = module_class_name if 'id' not in module_config else module_config['id']
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("Error in configuration file for module %s. Exception: %s, Error: %s. Please check configuration." % (module_class_name, etype, evalue))
                    self.shutDown()
            else:
                module_id = module_class_name = module_info
            counter = 1
            while module_id in self.modules:
                tmp_mod_name = module_id.split("_",1)[0]
                module_id = "%s_%s" % (tmp_mod_name, counter)
                counter += 1
            module_instances = []
            module_instance = self.initModule(module_class_name)
            module_instances.append(module_instance)
            if isinstance(module_instance, BaseMultiProcessModule.BaseMultiProcessModule):
                pool_size = module_config['pool_size'] if 'pool_size' in module_config else self.workers
                for _ in range(pool_size-1):
                    module_instance = self.initModule(module_class_name)
                    module_instances.append(module_instance)
            self.modules[module_id] = {'idx': idx,
                                       'instances': module_instances,
                                       'type': module_instance.module_type,
                                       'configuration': module_config}
            start_message = "Using module %s." % module_id
            self.logger.info(start_message)
            # Set receiver to next module in config if no receivers were set.
            if 'receivers' not in module_config:
                try:
                    next_module_info = self.configuration[idx+1]
                    if isinstance(next_module_info, dict):
                        receiver_class_name = next_module_info.keys()[0]
                        receiver_id = receiver_class_name if (not next_module_info[receiver_class_name] or 'id' not in next_module_info[receiver_class_name]) else next_module_info[receiver_class_name]['id']
                    else:
                        receiver_id = receiver_class_name = next_module_info
                    counter = 1
                    while receiver_id in self.modules:
                        tmp_mod_name = receiver_id.split("_",1)[0]
                        receiver_id = "%s_%s" % (tmp_mod_name, counter)
                        counter += 1
                    module_config['receivers'] = [receiver_id]
                except IndexError:
                    module_config['receivers'] = [None]
                except:
                    # Something is wrong with the configuration. Tell user.
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("Error in configuration for module %s. Exception: %s, Error: %s. Please check configuration." % (module_config, etype, evalue))
                    self.shutDown()

    """
    def __initModuleParsers(self):
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for module_instance in module_info['instances']:
                # Inline parsers are only supported for input and output modules.
                if module_instance.module_type not in ['input', 'output']:
                    continue
                if 'parsers' not in module_info['configuration']:
                    continue
                for parser_data in module_info['configuration']['parsers']:
                    if isinstance(parser_data, dict):
                        parser_name, parser_config = iter(parser_data.items()).next()
                    else:
                        parser_name = parser_data
                        parser_config = {}
                    parser = self.initModule(parser_name)
                    parser.configure(parser_config)
                    parser.checkConfiguration()
                    module_instance.addParser(parser)
    """

    def configureModules(self):
        """Call configuration method of module."""
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for module_instance in module_info['instances']:
                module_instance.configure(module_info['configuration'])

    def initEventStream(self):
        """
        Connect all modules

        The configuration allows to connect the modules via the <receivers> parameter.
        As different types of modules exists (Base, Threaded, MultiProcess), connecting one modules output
        with its receivers input can be either direct or via a queue.
        TODO: To prevent loops a sanity check should be performed after all modules have been connected.
        """
        queues = {}
        # Iterate over all configured modules.
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']): #self.modules.items():
            sender_instance = module_info['instances'][0]
            # StandAlone and output modules can have no receivers.
            if sender_instance.module_type in ['stand_alone', 'output']:
                continue
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
                for receiver_instance in self.modules[receiver_name]['instances']:
                    # If we run multiprocessed and the module is not capable of running parallel, this module will only be
                    # started in the main process. Connect the module via a queue to all receivers that can run forked.
                    if (self.workers > 1 and (not sender_instance.can_run_forked and receiver_instance.can_run_forked))\
                            or\
                        (isinstance(receiver_instance, BaseMultiProcessModule.BaseMultiProcessModule)):
                        try:
                            queue = queues[receiver_name]
                        except KeyError:
                            queue = self.produceQueue('multiprocess', self.queue_size, self.queue_buffer_size)
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
                instance.initAfterFork()

    def runModules(self):
        """
        Start the configured modules if they poll queues.
        """
        # All modules are completely configured, call modules run method if it exists.
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for instance in module_info['instances']:
                # Some modules, mostly input modules, use unique io devices, that can not be polled from multiple
                # threads/processes. These modules will only be started once from the master process and the output
                # will be send via queue to the other processes.
                if not self.is_master() and not instance.can_run_forked:
                    continue
                # All multiprocess modules will only be started from the main process.
                if not self.is_master() and isinstance(instance, BaseMultiProcessModule.BaseMultiProcessModule):
                    continue
                # The default 'start' method of threading.Thread/mp will call the 'run' method of the module.
                # The module itself can then decide if it wants to be run as thread. If not, it has to return False to let Gambolputty know.
                if getattr(instance, "start", None): # and (instance.getInputQueue() or instance.module_type in ['stand_alone', 'input'])
                    started = instance.start()
                    if started:
                        self.logger.debug("Starting module %s as thread via %s.start()." % (module_name, module_name))
                    continue
                # TODO: get rid of this call as it is only there for backwards compatibility.
                if getattr(instance, "run", None):
                    self.logger.debug("Starting module %s via %s.run()" % (module_name, module_name))
                    instance.run()
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

    def runWorkers(self):
        for i in range(1, self.workers):
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
            self.logger.info("GambolPutty started with %s processes(%s)." % (len(self.child_processes) + 1, os.getpid()))
        tornado.ioloop.IOLoop.instance().start()

    def restart(self, signum=False, frame=False):
        for worker in list(self.child_processes):
            os.kill(worker.pid, signal.SIGINT)
            worker.join()
            self.child_processes.remove(worker)
        self.logger.info("Restarting GambolPutty.")
        self.shutDown()
        time.sleep(1)
        Utils.restartMainProcess()

    def shutDown(self, signum=False, frame=False):
        # If a module started a subprocess, the whole gambolputty parent process gets forked.
        # As a result, the forked gambolputty process will also catch SIGINT||SIGALARM.
        if self.is_master():
            self.logger.info("Shutting down GambolPutty.")
        if not self.alive:
            sys.exit(0)
        self.alive = False
        self.shutDownModules()
        Utils.TimedFunctionManager.stopTimedFunctions()
        tornado.ioloop.IOLoop.instance().stop()
        if self.is_master():
            self.logger.info("Shutdown complete.")
        # Using multiprocessing.Manager (e.g. in Stats module) and os.fork together will cause the following error
        # when calling sys.exit():
        #
        # Error in sys.exitfunc:
        # Traceback (most recent call last):
        #  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/atexit.py", line 24, in _run_exitfuncs
        #    func(*targs, **kargs)
        #  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/multiprocessing/util.py", line 319, in _exit_function
        #    p.join()
        #  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/multiprocessing/process.py", line 143, in join
        #    assert self._parent_pid == os.getpid(), 'can only join a child process'
        # AssertionError: can only join a child process
        #
        # To make sure all subprocess share the same manager, it needs to be instantiated BEFORE the fork call.
        # The problem is that the multiprocessing.Manager starts its own process to handle the shared data.
        # When shutting down after the fork, the process.join seems to have lost the access to this process.
        # Aside of this error, everything works as expected.
        # So instead of calling sys.exit we send a SIGQUIT signal, which works just fine.
        #os.kill(os.getpid(), signal.SIGQUIT)

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

def coloredConsoleLogging(fn):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if(levelno>=50):
            color = Utils.AnsiColors.FAIL
        elif(levelno>=40):
            color = Utils.AnsiColors.FAIL
        elif(levelno>=30):
            color = Utils.AnsiColors.WARNING
        elif(levelno>=20):
            color = Utils.AnsiColors.LIGHTBLUE
        elif(levelno>=10):
            color = Utils.AnsiColors.OKGREEN
        else:
            color = Utils.AnsiColors.LIGHTBLUE
        args[1].msg = color + args[1].msg +  Utils.AnsiColors.ENDC # normal
        return fn(*args)
    return new

def usage():
    print('Usage: ' + sys.argv[0] + ' -c <path/to/config.conf> --configtest')

if "__main__" == __name__:
    config_pathname = os.path.abspath(sys.argv[0])
    config_pathname = config_pathname[:config_pathname.rfind("/")] + "/../conf"
    # Logger configuration.
    logging.config.fileConfig('%s/logger.conf' % config_pathname)
    logging.StreamHandler.emit = coloredConsoleLogging(logging.StreamHandler.emit)
    logger = logging.getLogger("GambolPutty")
    path_to_config_file = ""
    run_configtest = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "configtest","conf="])
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
    if not path_to_config_file:
        logger.error("Please provide a path to a configuration.")
        usage()
        sys.exit(2)
    if not os.path.isfile(path_to_config_file):
        logger.error("Configfile %s could not be found." % (path_to_config_file))
        usage()
        sys.exit(2)
    gp = GambolPutty(path_to_config_file)
    gp.configureGlobal()
    gp.initModulesFromConfig()
    gp.configureModules()
    gp.initEventStream()
    if run_configtest:
        logger.info("Configurationtest for %s finished.%s" % (path_to_config_file))
        sys.exit(0)
    gp.runWorkers()



