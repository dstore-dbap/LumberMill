# -*- coding: utf-8 -*-
import ast
import datetime
import copy
import random
import re
import time
import os
import sys
import subprocess
import logging
import signal
import socket
import types
import platform
import pylru
from string import Formatter
from Decorators import setInterval

# Conditional imports for python2/3
try:
    import __builtin__ as builtins
except ImportError:
    import builtins

try:
    import zmq
    zmq_avaiable = True
except ImportError:
    zmq_avaiable = False

try:
    import msgpack
    msgpack_avaiable = True
except ImportError:
    msgpack_avaiable = False

try:
    import __pypy__
    is_pypy = True
except ImportError:
    is_pypy = False

# In python3 the types constants have been eliminated.
if sys.hexversion > 0x03000000:
    typenames_to_type = {'None': type(None),
                         'Boolean': bool,
                         'Bool': bool,
                         'Integer': int,
                         'Int': int,
                         'Float': float,
                         'Str': str,
                         'String': str,
                         'Unicode': str,
                         'Tuple': tuple,
                         'List': list,
                         'Dictionary': dict,
                         'Dict': dict}
else:
    typenames_to_type = {'None': types.NoneType,
                         'Boolean': types.BooleanType,
                         'Bool': types.BooleanType,
                         'Integer': types.IntType,
                         'Int': types.IntType,
                         'Float': types.FloatType,
                         'Str': types.StringType,
                         'String': types.StringType,
                         'Unicode': types.UnicodeType,
                         'Tuple': types.TupleType,
                         'List': types.ListType,
                         'Dictionary': types.DictType,
                         'Dict': types.DictType}

loglevel_string_to_loglevel_int = {'info': logging.INFO,
                                   'warn': logging.WARN,
                                   'error': logging.ERROR,
                                   'critical': logging.CRITICAL,
                                   'fatal': logging.FATAL,
                                   'debug': logging.DEBUG}

MY_HOSTNAME = socket.gethostname()
MY_SYSTEM_NAME = platform.system()
GP_DYNAMIC_VAL_REGEX = re.compile('[\$|%]\((.*?)\)')
GP_DYNAMIC_VAL_REGEX_WITH_TYPES = re.compile('[\$|%]\((.*?)\)(-?\d*[-\.\*]?\d*[sdf]?)')
PYTHON_DYNAMIC_VAL_REGEX = re.compile('%\((.*?)\)')
DYNAMIC_VALUE_REPLACE_PATTERN = r"%(\1)"

def restartMainProcess():
    """
    Reload the whole LumberMill process. This code is a direct copy from tornado-3.1.1-py2.7.egg/tornado/autoreload.py.
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
    if (sys.path[0] == '' and not os.environ.get("PYTHONPATH", "").startswith(path_prefix)):
        os.environ["PYTHONPATH"] = (path_prefix + os.environ.get("PYTHONPATH", ""))
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
                     "lumbermill": {
                         'pid': os.getpid(),
                         'event_type': event_type,
                         'event_id': "%032x%s" % (random.getrandbits(128), os.getpid()),
                         'source_module': caller_class_name,
                         'received_from': received_from,
                         'received_by': MY_HOSTNAME
                     }
                }
    default_dict.update(dict)
    default_dict = KeyDotNotationDict(default_dict)
    return default_dict

def replaceVarsAndCompileString(code_as_string, replacement):
    """
    Parse a string to python code.

    This function will parse the code and replaces all variable names with the replacment.

    Example:

    code_as_string = "matched = VirtualHostName == 'www.gambolutty.com'", replacement = "event['%s']"

     will be parsed and compiled to:
     matched = event['VirtualHostName'] == "www.gambolutty.com"
    """
    try:
        code_ast = ast.parse(code_as_string)
    except:
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not parse code %s. Exception: %s, Error: %s." % (code_as_string, etype, evalue))
        return False
    transformer = ReplaceVars(replacement)
    transformer.visit(code_ast)
    try:
        code = compile(code_ast, '<ast>', 'exec')
    except:
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not compile code %s. Exception: %s, Error: %s." % (code_as_string, etype, evalue))
        return False
    return code


class ReplaceVars(ast.NodeTransformer):
    def __init__(self, replacement):
        ast.NodeTransformer.__init__(self)
        self.replacement = replacement

    def visit_Name(self, node):
        # ignore builtins and some other vars
        ignore_nodes = dir(builtins)
        ignore_nodes.extend(["matched", "dependency", "event"])
        if node.id in ignore_nodes:
            return node
        #pprint.pprint(self.mapping % node.id)
        #pprint.pprint(ast.dump(ast.parse(self.mapping % node.id)))
        new_node = ast.parse(self.replacement % node.id).body[0].value
        return new_node

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
        self.timed_func_handle = TimedFunctionManager.startTimedFunction(self.flush_timed_func)
        self.is_flushing = False

    def stopInterval(self):
        TimedFunctionManager.stopTimedFunctions(self.timed_func_handle)
        self.timed_func_handle = False

    def startInterval(self):
        if self.timed_func_handle:
            self.stopInterval()
        self.timed_func_handle = TimedFunctionManager.startTimedFunction(self.flush_timed_func)

    def getTimedFlushMethod(self):
        @setInterval(self.flush_interval)
        def timedFlush():
            self.flush()
        return timedFlush

    def append(self, item):
        self.put(item)

    def put(self, item):
        # Wait till a running store is finished to avoid strange race conditions when using this buffer with multiprocessing.
        while self.is_flushing:
            time.sleep(.00001)
        while len(self.buffer) > self.maxsize:
            self.logger.warning("Maximum number of items (%s) in buffer reached. Waiting for flush." % self.maxsize)
            time.sleep(1)
        self.buffer.append(item)
        if self.flush_size and len(self.buffer) == self.flush_size:
            self.flush()

    def flush(self):
        if self.bufsize() == 0 or self.is_flushing:
            return
        self.is_flushing = True
        self.stopInterval()
        success = self.flush_callback(self.buffer)
        if success:
            self.buffer = []
        self.startInterval()
        self.is_flushing = False

    def bufsize(self):
        return len(self.buffer)

class BufferedQueue:
    def __init__(self, queue, buffersize=500):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = Buffer(buffersize, self.sendBuffer, 5)

    def startInterval(self):
        self.buffer.startInterval()

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
            self.logger.error("Could not append data to queue. Exception: %s, Error: %s." % (etype, evalue))

    def get(self, block=True, timeout=None):
        try:
            buffered_data = self.queue.get(block, timeout)
            buffered_data = msgpack.unpackb(buffered_data)
            # After msgpack.uppackb we just have a normal dict. Cast this to KeyDotNotationDict.
            for data in buffered_data:
                yield KeyDotNotationDict(data)
        except (KeyboardInterrupt, SystemExit, ValueError, OSError):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass

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

    #def __del__(self, key):
    #    pass

    def __missing__(self, key):
        raise KeyError(key)

    def copy(self):
        new_dict = KeyDotNotationDict(copy.deepcopy(super(KeyDotNotationDict, self)))
        if "event_id" in new_dict.get("lumbermill", {}):
            new_dict['lumbermill']['event_id'] = "%032x%s" % (random.getrandbits(128), os.getpid())
        return new_dict

    def get(self, key, *args):
        try:
            return self.__getitem__(key)
        except (KeyError, IndexError) as e:
            # Try to return a default value for not existing dict keys.
            try:
                return args[0]
            except KeyError:
                raise e

    def __get(self, key, default, dict_or_list=None):
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

    def pop(self, key, default=None, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            if not isinstance(dict_or_list, list):
                return dict_or_list.pop(key, default)
            else:
                try:
                    return dict_or_list[int(key)]
                except KeyError:
                    return default
        current_key, remaining_keys = key.split('.', 1)
        try:
            dict_or_list = dict_or_list.__getitem__(current_key)
            return self.pop(remaining_keys, default, dict_or_list)
        except KeyError:
            return default

class DotDictFormatter(Formatter):
    try:  # deal with Py 2 & 3 difference
        NUMERICS = (int, long)
    except NameError:
        NUMERICS = int

    def get_field(self, field_name, args, kwargs):
        first, rest = field_name._formatter_field_name_split()
        obj = self.get_value(first, args, kwargs)
        # loop through the rest of the field_name, doing
        #  getattr or getitem as needed
        for is_attr, i in rest:
            obj = obj[i]
        return obj, first

def parseDynamicValuesInString(value):
    """
    Parse a string and replace the configuration notation for dynamic values with pythons notation.
    E.g:
    filter: $(lumbermill.source_module) == 'TcpServer'
    parsed:
    filter: %(lumbermill.source_module)s == 'TcpServer'
    """
    matches = GP_DYNAMIC_VAL_REGEX_WITH_TYPES.search(value)
    if not matches:
        return value
    # Get custom format if set.
    # Defaults to string.
    if matches.group(2):
        replace_pattern = DYNAMIC_VALUE_REPLACE_PATTERN + matches.group(2)
    else:
        replace_pattern = DYNAMIC_VALUE_REPLACE_PATTERN + "s"
    return GP_DYNAMIC_VAL_REGEX_WITH_TYPES.sub(replace_pattern, value)

def parseDynamicValuesInList(value_list, contains_dynamic_value):
    # Copy list since we might change it during iteration.
    value_list_copy = list(value_list)
    for idx, value in enumerate(value_list_copy):
        if isinstance(value, list):
            parseDynamicValuesInList(value_list[idx], contains_dynamic_value)
        elif isinstance(value, dict):
            parseDynamicValuesInDict(value_list[idx], contains_dynamic_value)
        elif isinstance(value, basestring):
            new_value = parseDynamicValuesInString(value)
            if new_value == value:
                continue
            contains_dynamic_value.append(True)
            value_list[idx] = new_value

def parseDynamicValuesInDict(value_dict, contains_dynamic_value):
    # Copy dict since we might change it during iteration.
    value_dict_copy = value_dict.copy()
    for key, value in value_dict_copy.items():
        new_key = key
        if(isinstance(key, basestring)):
            new_key = parseDynamicValuesInString(key)
        if isinstance(value, list):
            parseDynamicValuesInList(value_dict[key], contains_dynamic_value)
        elif isinstance(value, dict):
            parseDynamicValuesInDict(value_dict[key], contains_dynamic_value)
        elif isinstance(value, basestring):
            new_value = parseDynamicValuesInString(value)
            if key == new_key and value == new_value:
                continue
            if new_key != key:
                del value_dict[key]
            contains_dynamic_value.append(True)
            value_dict[new_key] = new_value

def parseDynamicValue(value):
    contains_dynamic_value = []
    if isinstance(value, list):
        parseDynamicValuesInList(value, contains_dynamic_value)
    elif isinstance(value, dict):
        parseDynamicValuesInDict(value, contains_dynamic_value)
    elif isinstance(value, basestring):
        new_value = parseDynamicValuesInString(value)
        if value != new_value:
            value = new_value
            contains_dynamic_value.append(True)
    return {'value': value, 'contains_dynamic_value': bool(contains_dynamic_value)}

def mapDynamicValueInString(value, mapping_dict, use_strftime=False):
    try:
        if use_strftime:
            if sys.platform .startswith('linux'):
                value = datetime.datetime.utcnow().strftime(value) % mapping_dict
            # On linux strftime will not remove non-supported format characters.
            # On other platforms this might be different.
            # So we need to take care that other dynamic value notations, which also use the percent sign syntax,
            # are renamed prior to using strftime and renamed to original after strftime was applied.
            # This adds a considerable overhead in parsing.
            # @see: http://bugs.python.org/issue9811
            else:
                value = PYTHON_DYNAMIC_VAL_REGEX.sub(r"$(\1)", value)
                value = datetime.datetime.utcnow().strftime(value)
                value = GP_DYNAMIC_VAL_REGEX.sub(r"%(\1)", value)
        return value % mapping_dict # dot_dict_formatter.format(value, **mapping_dict)
    except KeyError:
        return value
    except (ValueError, TypeError):
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("mapDynamicValueInString").error("Mapping failed for %s. Mapping data: %s. Exception: %s, Error: %s." % (value, mapping_dict, etype, evalue))
        return False

def mapDynamicValueInList(value_list, mapping_dict, use_strftime=False):
    for idx, value in enumerate(value_list):
        if isinstance(value, list):
            mapDynamicValueInList(value, mapping_dict, use_strftime)
        elif isinstance(value, dict):
            mapDynamicValueInDict(value, mapping_dict, use_strftime)
        elif isinstance(value, basestring):
            new_value = mapDynamicValueInString(value, mapping_dict, use_strftime)
            if new_value == value:
                continue
            value_list[idx] = new_value

def mapDynamicValueInDict(value_dict, mapping_dict, use_strftime=False):
    for key, value in value_dict.items():
        new_key = key
        if(isinstance(key, basestring)):
            new_key = mapDynamicValueInString(key, mapping_dict, use_strftime)
        if isinstance(value, list):
            mapDynamicValueInList(value, mapping_dict, use_strftime)
        elif isinstance(value, dict):
            mapDynamicValueInDict(value, mapping_dict, use_strftime)
        elif isinstance(value, basestring):
            new_value = mapDynamicValueInString(value, mapping_dict, use_strftime)
            if key == new_key and value == new_value:
                continue
            value_dict[new_key] = new_value

def mapDynamicValue(value, mapping_dict={}, use_strftime=False):
    if isinstance(value, basestring):
        return mapDynamicValueInString(value, mapping_dict, use_strftime)
    if isinstance(value, list):
        mapDynamicValueInList(value, mapping_dict, use_strftime)
    elif isinstance(value, dict):
        mapDynamicValueInDict(value, mapping_dict, use_strftime)
    return value

class TimedFunctionManager:
    """
    The decorator setInterval provides a simple way to repeatedly execute a function in intervals.
    This is done by starting a thread that calls the decorated method every interval seconds.
    To make sure, all threads get stopped when exiting or reloading LumberMill, the decorated functions
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
            TimedFunctionManager.timed_function_handlers.remove(handler)
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

def coloredConsoleLogging(fn):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if(levelno>=50):
            color = AnsiColors.FAIL
        elif(levelno>=40):
            color = AnsiColors.FAIL
        elif(levelno>=30):
            color = AnsiColors.WARNING
        elif(levelno>=20):
            color = AnsiColors.LIGHTBLUE
        elif(levelno>=10):
            color = AnsiColors.OKGREEN
        else:
            color = AnsiColors.LIGHTBLUE
        args[1].msg = color + args[1].msg +  AnsiColors.ENDC # normal
        return fn(*args)
    return new

class ZeroMqMpQueue:
    """
    Use ZeroMQ for IPC.
    This is faster than the default multiprocessing.Queue.

    Sender and receiver will be initalized on first put/get. This is neccessary since a zmq context will not
    survive a fork.

    send_pyobj and recv_pyobj is not used since it performance is slower than using msgpack for serialization.
    (A test for a simple dict using send_pyobj et.al performed around 12000 eps, while msgpack and casting to
    KeyDotNotationDict after unpacking resulted in around 17000 eps)
    """
    def __init__(self, queue_max_size=20):
        # Get a free random port.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 0))
        sock.listen(socket.SOMAXCONN)
        ipaddr, self.port = sock.getsockname()
        sock.close()
        self.queue_max_size = queue_max_size
        self.queue_size = 0
        self.sender = None
        self.receiver = None

    def initSender(self):
        zmq_context = zmq.Context()
        self.sender = zmq_context.socket(zmq.PUSH)
        try:
            self.sender.setsockopt(zmq.SNDHWM, self.queue_max_size)
        except AttributeError:
            self.sender.setsockopt(zmq.HWM, self.queue_max_size)
        try:
            self.sender.bind("tcp://127.0.0.1:%d" % self.port)
        except zmq.error.ZMQError:
            print("Address in use. Connecting only.")
            self.sender.connect("tcp://127.0.0.1:%d" % self.port)


    def initReceiver(self):
        #print("Init receiver in %s" % os.getpid())
        zmq_context = zmq.Context()
        self.receiver = zmq_context.socket(zmq.PULL)
        try:
            self.receiver.setsockopt(zmq.RCVHWM, self.queue_max_size)
        except AttributeError:
            self.receiver.setsockopt(zmq.HWM, self.queue_max_size)
        self.receiver.connect("tcp://127.0.0.1:%d" % self.port)

    def put(self, data):
        if not self.sender:
            self.initSender()
        self.sender.send(data)

    def get(self, block=None, timeout=None):
        if not self.receiver:
            self.initReceiver()
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

class MemoryCache():

    def __init__(self, size=1000):
        self.lru_dict = pylru.lrucache(size)

    def set(self, key, value):
        self.lru_dict[key] = value

    def get(self, key):
        return self.lru_dict[key]

    def unset(self, key):
        return self.lru_dict.pop(key)

def mergeNestedDicts(a, b, path=None):
    "Merges a with b. If b provides same key as a, b takes precendence."
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                mergeNestedDicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                continue # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

dot_dict_formatter = DotDictFormatter()