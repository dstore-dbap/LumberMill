#!/usr/bin/python
# -*- coding: UTF-8 -*-
from __future__ import print_function
import Utils
import BaseThreadedModule
import BaseMultiProcessModule
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

class GambolPutty():
    """A stream parser with configurable modules and message paths.

    GambolPutty helps to parse text based streams by providing a framework of modules.
    These modules can be combined via a simple configuration in any way you like. Have
    a look at the example config gambolputty.conf.example in the conf folder.

    This is the main class that reads the configuration, includes the needed modules
    and connects them via queues as configured.
    """

    def __init__(self, path_to_config_file):
        self.alive = False
        self.child_processes = []
        self.main_process_pid = os.getpid()
        self.modules = {}
        self.message_callbacks = defaultdict(lambda: [])
        self.logger = logging.getLogger(self.__class__.__name__)
        if path_to_config_file:
            self.readConfiguration(path_to_config_file)

    def produceQueue(self, queue_type='simple', queue_max_size=20, queue_buffer_size=1):
        """Returns a queue with queue_max_size"""
        queue = None
        if queue_type == 'simple':
            queue =  Queue.Queue(queue_max_size)
        if queue_type == 'multiprocess':
            if Utils.zmq_avaiable and Utils.msgpack_avaiable:
                queue = Utils.ZeroMqMpQueue(queue_max_size)
            else:
                queue = multiprocessing.Queue(queue_max_size)
        if not queue:
            self.logger.error("%sCould not produce requested queue %s.%s" % (Utils.AnsiColors.WARNING, queue_type, Utils.AnsiColors.ENDC))
            self.shutDown()
        return queue

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
            self.logger.error("%sCould not read config file %s. Exception: %s, Error: %s.%s" % (
            Utils.AnsiColors.WARNING, path_to_config_file, etype, evalue, Utils.AnsiColors.ENDC))
            self.shutDown()

    def getConfiguration(self):
        return self.configuration

    def setConfiguration(self, configuration, merge=True):
        if type(configuration) is not list:
            return
        if merge:
            # If merge is true keep currently configured modules and only merge new ones.
            for module_info in configuration:
                if module_info not in self.configuration:
                    self.configuration.append(module_info)
        else:
            self.configuration = configuration

    def configureGlobal(self):
        # SET SOME DEFAULTS HERE
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
        """ Initalize a module.

        :param module_name: module to initialize
        :type module_name: string
        """
        self.logger.debug("Initializing module %s." % (module_name))
        instance = None
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class(self)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not init module %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, module_name, etype, evalue, Utils.AnsiColors.ENDC))
            self.shutDown()
        return instance

    def initModulesFromConfig(self):
        """ Initalize all modules from the current config.
        """
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
                    self.logger.error("%sError in configuration file for module %s. Exception: %s, Error: %s. Please check configuration.%s" % (Utils.AnsiColors.FAIL, module_class_name, etype, evalue, Utils.AnsiColors.ENDC))
                    self.shutDown()
            else:
                module_id = module_class_name = module_info
            counter = 1
            while module_id in self.modules:
                tmp_mod_name = module_id.split("_",1)[0]
                module_id = "%s_%s" % (tmp_mod_name, counter)
                counter += 1
            module_instances = []
            for _ in range(self.workers):
                module_instance = self.initModule(module_class_name)
                module_instances.append(module_instance)
                if not isinstance(module_instance, BaseMultiProcessModule.BaseMultiProcessModule):
                    break
            self.modules[module_id] = {  'idx': idx,
                                         'instances': module_instances,
                                         'type': module_instance.module_type,
                                         'configuration': module_config}
            start_message = "%sUsing module %s%s." % (Utils.AnsiColors.LIGHTBLUE, module_id, Utils.AnsiColors.ENDC)
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
                    self.logger.error("%sError in configuration for module %s. Exception: %s, Error: %s. Please check configuration.%s" % ( Utils.AnsiColors.FAIL, module_config, etype, evalue, Utils.AnsiColors.ENDC))
                    self.shutDown()

    def configureModules(self):
        # Call configuration of module
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for module_instance in module_info['instances']:
                module_instance.configure(module_info['configuration'])

    def initEventStream(self):
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
                self.logger.debug("%s will send its output to %s." % (module_name, receiver_name))
                if receiver_name not in self.modules:
                    self.logger.error( "%sCould not add %s as receiver for %s. Module not found.%s" % ( Utils.AnsiColors.FAIL, receiver_name, module_name, Utils.AnsiColors.ENDC))
                    self.shutDown()
                for receiver_instance in self.modules[receiver_name]['instances']:
                    # a) If we run multiprocessed and the module is not capable of running parallel, this module will only be
                    # started in the main process. Connect the module via a queue to all child processes.
                    # b) All output modules will run in their own process because most of the outputs are quite slow compared
                    # to input and modifier mods.
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
                        instance.addReceiver(receiver_name, queues[receiver_name])
                    else:
                        instance.addReceiver(receiver_name, receiver_instance)

    def _initEventStream(self):
        """ Connect modules.

        The configuration allows to connect the modules via the <receivers> parameter.
        This method creates the queues and connects the modules via this queues.
        To prevent loops a sanity check is performed before all modules are connected.
        """
        # All modules are initialized, connect producer and consumers via a queue.
        queues = {}
        module_loop_buffer = []
        for module_name, module_info in self.modules.items():
            sender_instance = module_info['instance']
            for receiver_data in sender_instance.getConfigurationValue('receivers'):
                if not receiver_data:
                    break
                if isinstance(receiver_data, dict):
                    receiver_name, _ = iter(receiver_data.items()).next()
                else:
                    receiver_name = receiver_data
                self.logger.debug("%s will send its output to %s." % (module_name, receiver_name))
                if receiver_name not in self.modules:
                    self.logger.warning( "%sCould not add %s as receiver for %s. Module not found.%s" % ( Utils.AnsiColors.WARNING, receiver_name, module_name, Utils.AnsiColors.ENDC))
                    continue
                receiver_instance = self.modules[receiver_name]['instance']
                # If the sender or receiver is a thread or a process, produce the needed queue.
                if isinstance(receiver_instance, BaseThreadedModule.BaseThreadedModule) or isinstance(receiver_instance, BaseMultiProcessModule.BaseMultiProcessModule) \
                    or \
                    isinstance(sender_instance, BaseThreadedModule.BaseThreadedModule) or isinstance(receiver_instance, BaseMultiProcessModule.BaseMultiProcessModule):
                    try:
                        queue = queues[receiver_name]
                    except KeyError:
                        if isinstance(sender_instance, BaseMultiProcessModule.BaseMultiProcessModule) or isinstance(receiver_instance, BaseMultiProcessModule.BaseMultiProcessModule):
                            queue = self.produceQueue('multiprocess', self.queue_size, self.queue_buffer_size)
                        else:
                            queue = self.produceQueue('simple', self.queue_size, self.queue_buffer_size)
                        queues[receiver_name] = queue
                    if not receiver_instance.getInputQueue():
                        receiver_instance.setInputQueue(queue)

                # Build a node structure used for the loop test.
                try:
                    node = (node for node in module_loop_buffer if node.module == sender_instance).next()
                except:
                    node = Node(sender_instance)
                    module_loop_buffer.append(node)
                try:
                    receiver_node = (node for node in module_loop_buffer if node.module == receiver_instance).next()
                except:
                    receiver_node = Node(receiver_instance)
                    module_loop_buffer.append(receiver_node)
                node.addChild(receiver_node)

                sender_instance = module_info['instance']
                # Add the receiver to senders. If the send/receiver is a thread or multiprocess, they share the same queue.
                if isinstance(receiver_instance, BaseThreadedModule.BaseThreadedModule) or isinstance(receiver_instance, BaseMultiProcessModule.BaseMultiProcessModule) \
                    or \
                    isinstance(sender_instance, BaseThreadedModule.BaseThreadedModule) or isinstance(receiver_instance, BaseMultiProcessModule.BaseMultiProcessModule):
                    sender_instance.addReceiver(receiver_name, queues[receiver_name])
                else:
                    sender_instance.addReceiver(receiver_name, receiver_instance)

        # Check if the configuration produces a loop.
        # This code can definitely be made more efficient...
        for node in module_loop_buffer:
            for loop in hasLoop(node, stack=[]):
                self.logger.error(
                    "%sChaining of modules produced a loop. Check configuration. Module: %s.%s" % ( Utils.AnsiColors.FAIL, loop.module.__class__.__name__, Utils.AnsiColors.ENDC))
                self.shutDown()

    def getModuleInfoById(self, module_id, silent=True):
        try:
            return self.modules[module_id]
        except KeyError:
            if not silent:
                self.logger.error("%sGet module by id %s failed. No such module.%s" % (Utils.AnsiColors.FAIL, module_id, Utils.AnsiColors.ENDC))
            return None

    def prepareModules(self):
        # All modules are completely configured, call modules prepareRun method.
        # prepareRun is used to (re)init modules after a process fork.
        # BufferedQueue i.e. uses a thread to flush its buffer in given intervals.
        # The thread will not survive a fork of the main process. So we need to start this
        # after the fork was executed.
        for module_name, module_info in sorted(self.modules.items(), key=lambda x: x[1]['idx']):
            for instance in module_info['instances']:
                instance.prepareRun()

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
                if not instance.can_run_forked and not self.is_master():
                    continue
                # All multiprocess modules will only be started from the main process.
                if isinstance(instance, BaseMultiProcessModule.BaseMultiProcessModule) and not self.is_master():
                    continue
                # The default 'start' method of threading.Thread/mp will call the 'run' method of the module.
                if getattr(instance, "start", None): # and (instance.getInputQueue() or instance.module_type in ['stand_alone', 'input'])
                    instance.start()
                    continue
                #if getattr(instance, "run", None):
                #    instance.run()
                #    continue

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

    def runChildren(self):
        for i in range(1,self.workers):
            worker = multiprocessing.Process(target=self.run)
            worker.start()
            self.child_processes.append(worker)
        self.run()

    def run(self):
        #print("Started Gambolputty(%s,%s)" % (self.is_master(), os.getpid()))
        # Catch Keyboard interrupt here. Catching the signal seems
        # to be more reliable then using try/except when running
        # multiple processes under pypy.
        signal.signal(signal.SIGINT, self.shutDown)
        signal.signal(signal.SIGALRM, self.restart)
        self.alive = True
        self.prepareModules()
        self.runModules()
        if self.is_master():
            self.logger.info("%sGambolPutty started with %s processes(%s).%s" % (Utils.AnsiColors.LIGHTBLUE, len(self.child_processes)+1, os.getpid(),Utils.AnsiColors.ENDC))
        tornado.ioloop.IOLoop.instance().start()

    def restart(self, signum=False, frame=False):
        # If a module started a subprocess, the whole gambolputty parent process gets forked.
        # As a result, the forked gambolputty process will also catch SIGINT||SIGALARM.
        # Still we know the pid of the original main process.
        if self.is_master():
            self.logger.info("%sRestarting GambolPutty.%s" % (Utils.AnsiColors.LIGHTBLUE, Utils.AnsiColors.ENDC))
        self.shutDownModules()
        self.configure()
        self.initModulesFromConfig()
        self.configureModules()
        self.initEventStream()
        #self.runModules()

    def shutDown(self, signum=False, frame=False):
        # If a module started a subprocess, the whole gambolputty parent process gets forked.
        # As a result, the forked gambolputty process will also catch SIGINT||SIGALARM.
        # Still we know the pid of the original main process and ignore SIGINT||SIGALARM in forked processes.
        # Directly exit on a second SIGINT||SIGALARM.
        if not self.alive:
            sys.exit(0)
        self.alive = False
        if self.is_master():
            for worker in list(self.child_processes):
                if not worker.pid:
                    continue
                os.kill(worker.pid, signal.SIGINT)
                self.child_processes.remove(worker)
            self.logger.info("%sShutting down GambolPutty.%s" % (Utils.AnsiColors.LIGHTBLUE, Utils.AnsiColors.ENDC))
        self.shutDownModules()
        Utils.TimedFunctionManager.stopTimedFunctions()
        if self.is_master():
            self.logger.info("%sShutdown complete.%s" % (Utils.AnsiColors.LIGHTBLUE, Utils.AnsiColors.ENDC))
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
                        self.logger.info("%s%s event(s) still in flight. Waiting %s secs. Press ctrl+c again to exit directly.%s" % (Utils.AnsiColors.LIGHTBLUE, events_in_queues, (.5 * wait_loops),Utils.AnsiColors.ENDC))
                    time.sleep(.5 * wait_loops)
                    continue
                break
        # Shutdown all other modules.
        for module_name, module_info in self.modules.items():
            for instance in module_info['instances']:
                if instance.module_type != "input":
                    instance.shutDown()
        tornado.ioloop.IOLoop.instance().stop()

def usage():
    print('Usage: ' + sys.argv[0] + ' -c <path/to/config.conf> --configtest')

if "__main__" == __name__:
    config_pathname = os.path.abspath(sys.argv[0])
    config_pathname = config_pathname[:config_pathname.rfind("/")] + "/../conf"
    logging.config.fileConfig('%s/logger.conf' % config_pathname)
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
        logger.error("%sPlease provide a path to a configuration.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC))
        usage()
        sys.exit(2)
    if not os.path.isfile(path_to_config_file):
        logger.error("%sConfigfile %s could not be found.%s" % (Utils.AnsiColors.FAIL, path_to_config_file, Utils.AnsiColors.ENDC))
        usage()
        sys.exit(2)
    gp = GambolPutty(path_to_config_file)
    gp.configureGlobal()
    gp.initModulesFromConfig()
    gp.configureModules()
    gp.initEventStream()
    if run_configtest:
        logger.info("%sConfigurationtest for %s finished.%s" % (Utils.AnsiColors.LIGHTBLUE, path_to_config_file, Utils.AnsiColors.ENDC))
        sys.exit(0)
    gp.runChildren()



