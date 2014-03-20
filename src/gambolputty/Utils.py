# -*- coding: utf-8 -*-
import ast
import pprint
import random
import time
import os
import sys
import subprocess
import logging
import __builtin__
import signal
import Decorators

try:
    import __pypy__
    is_pypy = True
except ImportError:
    is_pypy = False

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
    default_dict = KeyDotNotationDict({ "event_type": event_type,
                     "data": "",
                     "gambolputty": {
                        'event_type': event_type,
                        'event_id': "%032x" % random.getrandbits(128),
                        "source_module": caller_class_name,
                        "received_from": received_from,
                     }
                    })
    default_dict.update(dict)
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
        ignore_nodes = dir(__builtin__)
        ignore_nodes.extend(["matched", "dependency", "event"])
        if node.id in ignore_nodes:
            return node
        #pprint.pprint(self.mapping % node.id)
        #pprint.pprint(ast.dump(ast.parse(self.mapping % node.id)))
        new_node = ast.parse(self.mapping % node.id).body[0].value
        return new_node

class Buffer:
    def __init__(self, size, callback=None, interval=1, maxsize=5000):
        self.flush_size = size
        self.buffer = []
        self.maxsize = maxsize
        self.append = self.put
        self.flush_interval = interval
        self.flush_callback = callback
        self.flush_timed_func = self.getTimedFlushMethod()
        if self.flush_interval:
            self.flush_timed_func()
        self.is_storing = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def getTimedFlushMethod(self):
        @Decorators.setInterval(self.flush_interval)
        def timedFlush():
            self.flush()
        return timedFlush

    def put(self, item):
        # Wait till a running store is finished to avoid strange race conditions when using this buffer with
        # multiprocessing.
        while self.is_storing:
            time.sleep(.0001)
        if len(self.buffer) < self.maxsize:
            self.buffer.append(item)
        else:
            self.logger.warning("%sMaximum number of items (%s) in buffer reached. Dropping item.%s" % (AnsiColors.WARNING, self.maxsize, AnsiColors.ENDC))
        if len(self.buffer) >= self.flush_size:
            self.flush()

    def flush(self):
        if len(self.buffer) == 0:
            return
        if self.is_storing:
            time.sleep(.0001)
        self.is_storing = True
        try:
            self.flush_callback(self.buffer)
            self.buffer = []
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("%sCould not flush buffer to %s. Exception: %s, Error: %s.%s" % (AnsiColors.FAIL, self.flush_callback, etype, evalue, AnsiColors.ENDC))
        self.is_storing = False

    def bufsize(self):
        return len(self.buffer)

class BufferedQueue():
    def __init__(self, queue, buffersize=100):
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = Buffer(buffersize, self.sendBuffer, 1)

    def put(self, payload):
        self.buffer.append(payload)

    def sendBuffer(self, buffered_data):
        self.queue.put(buffered_data)

    def get(self, block=True, timeout=None):
        return self.queue.get(block, timeout)

    def qsize(self):
        return self.buffer.bufsize + self.queue.qsize()

    def __getattr__(self, name):
        return getattr(self.queue, name)

class __BufferedQueue():
    def __init__(self, queue, buffersize=100):
        self.queue = queue
        self.buffersize = buffersize
        self.buffer = []
        self.is_sending = False
        self.flushBuffer()

    @Decorators.setInterval(1)
    def flushBuffer(self):
        if self.is_sending or len(self.buffer) == 0:
            return
        self.sendBuffer()

    def put(self, payload):
        # Wait till a running store is finished to avoid strange race conditions.
        while self.is_sending:
            time.sleep(.001)
        self.buffer.append(payload)
        if len(self.buffer) == self.buffersize:
            self.sendBuffer()

    def sendBuffer(self):
        self.is_sending = True
        self.queue.put(self.buffer)
        self.buffer = []
        self.is_sending = False

    def get(self, block=True, timeout=None):
        return self.queue.get(block, timeout)

    def qsize(self):
        return len(self.buffer) + self.queue.qsize()

    def __getattr__(self, name):
        return getattr(self.queue, name)

class KeyDotNotationDict(dict):
    def __init__(self, *args):
        dict.__init__(self, *args)

    def __getitem__(self, key, dict_or_list=None):
        dict_or_list = dict_or_list if dict_or_list else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(dict_or_list, list):
                key = int(key)
            return dict_or_list.__getitem__(key)
        current_key, remaining_keys = key.split('.', 1)
        dict_or_list = dict_or_list.__getitem__(current_key)
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

class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LIGHTBLUE = '\033[34m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
