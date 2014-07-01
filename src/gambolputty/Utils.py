# -*- coding: utf-8 -*-
import ast
import datetime
import copy
import random
import time
import os
import sys
import subprocess
import logging
import signal
import Decorators
import socket

# Conditional imports for python2/3
try:
    import __builtin__ as builtins
except ImportError:
    import builtins

try:
    import zmq
    import msgpack
    zmq_avaiable = True
except ImportError:
    zmq_avaiable = False

try:
    import __pypy__
    is_pypy = True
except ImportError:
    is_pypy = False

# Borrowed from Ned Batchelder
if sys.hexversion > 0x03000000:
    def exec_function(source, filename, global_map):
        exec(compile(source, filename, "exec"), global_map)
else:
    eval(compile("""\
def exec_function(source, filename, global_map):
    exec compile(source, filename, "exec") in global_map
""",
    "<exec_function>", "exec"))

my_hostname = socket.gethostname()

def reload():
    """
    Reload the whole GambolPutty process. This code is a direct copy from tornado-3.1.1-py2.7.egg/tornado/autoreload.py.
    """
    if hasattr(signal, "setitimer"):
        # Clear the alarm signal set by
        # ioloop.set_blocking_log_threshold so it doesn't fire
        # after the exec.
        signal.setitimer(signal.ITIMER_REAL, 0, 0)
    # sys.path fixes: see comments at top of file.  If sys.path[0] is an empty
    # string, we were (probably) invoked with -m and the effective path
    # is about to change on re-exec.  Add the current directory to $PYTHONPATH
    # to ensure that the new process sees the same path we did.
    path_prefix = '.' + os.pathsep
    if (sys.path[0] == '' and
            not os.environ.get("PYTHONPATH", "").startswith(path_prefix)):
        os.environ["PYTHONPATH"] = (path_prefix +
                                    os.environ.get("PYTHONPATH", ""))
    if sys.platform == 'win32':
        # os.execv is broken on Windows and can't properly parse command line
        # arguments and executable name if they contain whitespaces. subprocess
        # fixes that behavior.
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    else:
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except OSError:
            # Mac OS X versions prior to 10.6 do not support execv in
            # a process that contains multiple threads.  Instead of
            # re-executing in the current process, start a new one
            # and cause the current process to exit.  This isn't
            # ideal since the new process is detached from the parent
            # terminal and thus cannot easily be killed with ctrl-C,
            # but it's better than not being able to autoreload at
            # all.
            # Unfortunately the errno returned in this case does not
            # appear to be consistent, so we can't easily check for
            # this error specifically.
            os.spawnv(os.P_NOWAIT, sys.executable,
                      [sys.executable] + sys.argv)
            sys.exit(0)

def getDefaultEventDict(dict={}, caller_class_name='', received_from=False, event_type="Unknown"):
    default_dict = { "data": "",
                     "gambolputty": {
                        'event_type': event_type,
                        'event_id': "%032x%s" % (random.getrandbits(128), os.getpid()),
                        'source_module': caller_class_name,
                        'received_from': received_from,
                        'received_by': my_hostname
                     }
                }
    default_dict.update(dict)
    default_dict = KeyDotNotationDict(default_dict)
    return default_dict

def compileStringToConditionalObject(condition_as_string, mapping):
    """
    Parse a condition passed in as string.

    Example:

    lambda event:

    condition_as_string = "matched = VirtualHostName == 'www.gambolutty.com'", mapping = "event['%s']"

    condition_as_string = "lambda event: VirtualHostName == 'www.gambolutty.com'", mapping = "event['%s']"

     will be parsed and compiled to:
     matched = event['VirtualHostName'] == "www.gambolutty.com"
     matched = event.get('VirtualHostName', False) == "www.gambolutty.com"
    """
    try:
        # Build a complete expression from filter.
        transformer = AstTransformer(mapping)
        conditional_ast = ast.parse(condition_as_string)
        conditional_ast = transformer.visit(conditional_ast)
        conditional = compile(conditional_ast, '<string>', 'exec')
        return conditional
    except :
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not compile conditional %s. Exception: %s, Error: %s.%s" % (AnsiColors.WARNING, condition_as_string, etype, evalue, AnsiColors.ENDC))
        return False

class AstTransformer(ast.NodeTransformer):
    def __init__(self, mapping="%s"):
        ast.NodeTransformer.__init__(self)
        self.mapping = mapping

    def visit_Name(self, node):
        # ignore builtins and some other vars
        ignore_nodes = dir(builtins)
        ignore_nodes.extend(["matched", "dependency", "event"])
        if node.id in ignore_nodes:
            return node
        #pprint.pprint(self.mapping % node.id)
        #pprint.pprint(ast.dump(ast.parse(self.mapping % node.id)))
        new_node = ast.parse(self.mapping % node.id).body[0].value
        return new_node

def mapDynamicValue(value, mapping_dict={}, use_strftime=False):
    # At the moment, just flat lists and dictionaries are supported.
    # If need arises, recursive parsing of the lists and dictionaries will be added.
    if isinstance(value, list):
        try:
            if use_strftime:
                mapped_values = [datetime.datetime.utcnow().strftime(v) % mapping_dict for v in value]
            else:
                mapped_values = [v % mapping_dict for v in value]
            return mapped_values
        except KeyError:
            return False
        except (ValueError, TypeError):
            etype, evalue, etb = sys.exc_info()
            logging.getLogger("mapDynamicValue").error("%sMapping failed for %s. Mapping data: %s. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, v, mapping_dict, etype, evalue, AnsiColors.ENDC))
            return False
    elif isinstance(value, dict):
        try:
            if use_strftime:
                mapped_keys = [datetime.datetime.utcnow().strftime(k) % mapping_dict for k in value.iterkeys()]
                mapped_values = [datetime.datetime.utcnow().strftime(v) % mapping_dict for v in value.itervalues()]
            else:
                mapped_keys = [k % mapping_dict for k in value.iterkeys()]
                mapped_values = [v % mapping_dict for v in value.itervalues()]
            return dict(zip(mapped_keys, mapped_values))
        except KeyError:
            return False
        except (ValueError, TypeError):
            etype, evalue, etb = sys.exc_info()
            logging.getLogger("mapDynamicValue").error("%sMapping failed for %s. Mapping data: %s. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, v, mapping_dict, etype, evalue, AnsiColors.ENDC))
            return False
    elif isinstance(value, basestring):
        try:
            if use_strftime:
                return datetime.datetime.utcnow().strftime(value) % mapping_dict
            else:
                return value % mapping_dict
        except KeyError:
            return False
        except (ValueError, TypeError):
            etype, evalue, etb = sys.exc_info()
            logging.getLogger("mapDynamicValue").error("%sMapping failed for %s. Mapping data: %s. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, value, mapping_dict, etype, evalue, AnsiColors.ENDC))
            return False

class Buffer:
    def __init__(self, flush_size=None, callback=None, interval=1, maxsize=5000):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.flush_size = flush_size
        self.buffer = []
        self.maxsize = maxsize
        self.append = self.put
        self.flush_interval = interval
        self.flush_callback = callback
        self.flush_timed_func = self.getTimedFlushMethod()
        if self.flush_interval:
            self.timed_func_handle = TimedFunctionManager.startTimedFunction(self.flush_timed_func)
        self.is_storing = False

    def getTimedFlushMethod(self):
        @Decorators.setInterval(self.flush_interval)
        def timedFlush():
            self.flush()
        return timedFlush

    def append(self, item):
        self.put(item)

    def put(self, item):
        # Wait till a running store is finished to avoid strange race conditions when using this buffer with multiprocessing.
        while self.is_storing:
            time.sleep(.00001)
        while len(self.buffer) > self.maxsize:
            self.logger.warning("%sMaximum number of items (%s) in buffer reached. Waiting for flush.%s" % (AnsiColors.WARNING, self.maxsize, AnsiColors.ENDC))
            time.sleep(1)
        self.buffer.append(item)
        if self.flush_size and len(self.buffer) == self.flush_size:
            self.flush()

    def flush(self):
        if len(self.buffer) == 0 or self.is_storing:
            return
        self.is_storing = True
        if self.flush_callback(self.buffer):
            self.buffer = []
        self.is_storing = False
        """
        try:
            if self.flush_callback(self.buffer):
                self.buffer = []
        except (KeyboardInterrupt, SystemExit):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not flush buffer to %s. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, self.flush_callback, etype, evalue, AnsiColors.ENDC))
        finally:
             self.is_storing = False
        """

    def bufsize(self):
        return len(self.buffer)

class BufferedQueue():
    def __init__(self, queue, buffersize=500):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = Buffer(buffersize, self.sendBuffer, 5)

    def put(self, payload):
        self.buffer.append(payload)

    def sendBuffer(self, buffered_data):
        try:
            buffered_data = msgpack.packb(buffered_data)
            self.queue.put(buffered_data)
            return True
        except (KeyboardInterrupt, SystemExit):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not append data to queue. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, etype, evalue, AnsiColors.ENDC))

    def get(self, block=True, timeout=None):
        try:
            buffered_data = self.queue.get(block, timeout)
            #for data in buffered_data:
            #    yield data
            buffered_data = msgpack.unpackb(buffered_data)
            # After msgpack.uppackb we just have a normal dict. Cast this to KeyDotNotationDict.
            for data in buffered_data:
                yield KeyDotNotationDict(data)
        except (KeyboardInterrupt, SystemExit, ValueError, OSError):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass
        #except:
        #    exc_type, exc_value, exc_tb = sys.exc_info()
        #    self.logger.error("%sCould not read data from input queue. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, exc_type, exc_value, AnsiColors.ENDC) )


    def qsize(self):
        return self.buffer.bufsize() + self.queue.qsize()

    def __getattr__(self, name):
        return getattr(self.queue, name)

class KeyDotNotationDict(dict):
    """
    A dictionary that allows to access values via dot separated keys, e.g.:
    >>> my_dict = {"key1": {"key2": "value"}}
    >>> my_dict["key1.key2"]
    "value"
    """

    def __getitem__(self, key, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(dict_or_list, list):
                key = int(key)
            return dict_or_list.__getitem__(key)
        current_key, remaining_keys = key.split('.', 1)
        try:
            dict_or_list = dict_or_list.__getitem__(current_key)
        except TypeError:
            dict_or_list = dict_or_list.__getitem__(int(current_key))
        return self.__getitem__(remaining_keys, dict_or_list)

    def __setitem__(self, key, value, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(dict_or_list, list):
                key = int(key)
            return dict_or_list.__setitem__(key, value)
        current_key, remaining_keys = key.split('.', 1)
        dict_or_list = dict_or_list.__getitem__(current_key)
        return self.__setitem__(remaining_keys, value, dict_or_list)

    def __delitem__(self, key, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(dict_or_list, list):
                key = int(key)
            return dict_or_list.__delitem__(key)
        current_key, remaining_keys = key.split('.', 1)
        dict_or_list = dict_or_list.__getitem__(current_key)
        return self.__delitem__(remaining_keys, dict_or_list)

    def __contains__(self, key, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            return dict_or_list.__contains__(key)
        current_key, remaining_keys = key.split('.', 1)
        try:
            dict_or_list = dict_or_list.__getitem__(current_key)
            return self.__contains__(remaining_keys, dict_or_list)
        except KeyError:
            return False

    def __del__(self):
        pass

    def copy(self):
        new_dict = KeyDotNotationDict(copy.deepcopy(super(KeyDotNotationDict, self)))
        if "event_id" in new_dict.get("gambolputty", {}):
            new_dict['gambolputty']['event_id'] = "%s-%02x" % (new_dict['gambolputty']['event_id'], random.getrandbits(8))
        return new_dict

    def get(self, key, default, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            if not isinstance(dict_or_list, list):
                return dict_or_list.get(key, default)
            else:
                try:
                    return dict_or_list[int(key)]
                except KeyError:
                    return default
        current_key, remaining_keys = key.split('.', 1)
        try:
            dict_or_list = dict_or_list.__getitem__(current_key)
            return self.get(remaining_keys, default, dict_or_list)
        except KeyError:
            return default

class TimedFunctionManager:
    """
    The decorator setInterval provides a simple way to repeatedly execute a function in intervals.
    This is done by starting a thread that calls the decorated method every interval seconds.
    To make sure, all threads get stopped when exiting or reloading GambolPutty, the decorated functions
    should be started like this e.g.:
    ...
    Utils.TimedFunctionManager.startTimedFunction(self.sendAliveRequests)
    ...

    The main process will call TimedFunctionManager.stopTimedFunctions() on exit or reload.
    This makes sure all thread get terminated.
    """

    timed_function_handlers = []

    @staticmethod
    def startTimedFunction(timed_function, *args, **kwargs):
        """
        Start a timed function and keep track of all running functions.
        """
        handler = timed_function(*args, **kwargs)
        TimedFunctionManager.timed_function_handlers.append(handler)
        return handler

    @staticmethod
    def stopTimedFunctions(handler=False):
        """
        Stop all timed functions. They are started as daemon, so when a reaload occurs, they will not finish cause the
        main thread still is running. This takes care of this issue.
        """
        if not TimedFunctionManager.timed_function_handlers:
            return
        # Clear provided handler only.
        if handler and handler in TimedFunctionManager.timed_function_handlers:
            handler.set()
            TimedFunctionManager.timed_function_handlers.remove(handler)
            return
        # Clear all timed functions
        for handler in TimedFunctionManager.timed_function_handlers:
            handler.set()
        TimedFunctionManager.timed_function_handlers = []

class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LIGHTBLUE = '\033[34m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class ZeroMqMpQueue:
    """
    Use ZeroMQ for IPC.
    This is faster than the default multiprocessing.Queue.

    send_pyobj and recv_pyobj is not used since it performance is slower than using msgpack for serialization.
    (A test for a simple dict using send_pyobj et.al performed around 12000 eps, while msgpack and casting to
    KeyDotNotationDict after unpacking resulted in around 17000 eps)
    """

    def __init__(self, queue_max_size=20):
        self.queue_size = 0
        zmq_context = zmq.Context()
        self.queue_max_size = queue_max_size
        self.sender = zmq_context.socket(zmq.PUSH)
        try:
            self.sender.setsockopt(zmq.SNDHWM, queue_max_size)
        except AttributeError:
            self.sender.setsockopt(zmq.HWM, queue_max_size)
        self.selected_port = self.sender.bind_to_random_port("tcp://127.0.0.1", min_port=5200, max_port=5300, max_tries=100)
        self.receiver = None

    def put(self, data):
        self.sender.send(data)

    def get(self, block, timeout):
        if not self.receiver:
            zmq_context = zmq.Context()
            self.receiver = zmq_context.socket(zmq.PULL)
            try:
                self.receiver.setsockopt(zmq.RCVHWM, self.queue_max_size)
            except:
                self.receiver.setsockopt(zmq.HWM, self.queue_max_size)
            self.receiver.connect("tcp://127.0.0.1:%d" % self.selected_port)
        events = ""
        try:
            events = self.receiver.recv()
            return events
        except zmq.error.ZMQError as e:
            # Ignore iterrupt error caused by SIGINT
            if e.strerror == "Interrupted system call":
                return events

    def qsize(self):
        return self.queue_size


