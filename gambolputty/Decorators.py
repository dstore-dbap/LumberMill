# -*- coding: utf-8 -*-
import codecs
import sys
import functools
import threading
import re
import ast
import multiprocessing
import collections


def Singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance

def setInterval(interval, max_run_count=0, call_on_init=False):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()
            def loop(): # executed in another thread
                run_count = 0
                if call_on_init:
                    function(*args, **kwargs)
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)
                    if max_run_count > 0:
                        run_count += 1
                        if run_count == max_run_count:
                            break
            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator

def setProcessInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = multiprocessing.Event()
            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)
            t = multiprocessing.Process(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator


def ModuleDocstringParser(cls):
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.configuration_metadata = {}
        config_option_regex = "\s*(?P<name>.*?):.*?#\s*<(?P<props>.*?)>"
        regex = re.compile(config_option_regex, re.MULTILINE)
        docstring = ""
        # Get docstring from parents. Only single inheritance supported.
        for parent_class in cls.__bases__:
            if parent_class.__doc__:
                docstring += parent_class.__doc__
        if cls.__doc__:
            docstring += cls.__doc__
        for matches in regex.finditer(docstring):
            config_option_info = matches.groupdict()
            for prop_info in config_option_info['props'].split(";"):
                try:
                    prop_name, prop_value = [m.strip() for m in prop_info.split(":", 1)]
                    # Replace escaped backslashes.
                    if "//" in prop_value:
                        prop_value = codecs.escape_decode(prop_value)
                except ValueError:
                    instance.logger.debug("Could not parse config setting %s." % config_option_info)
                    continue
                if prop_name in ["default", "values"]:
                    try:
                        prop_value = ast.literal_eval(prop_value)
                    except:
                        etype, evalue, etb = sys.exc_info()
                        instance.logger.error("Could not parse %s from docstring. Exception: %s, Error: %s." % (prop_value, etype, evalue))
                        continue
                    # Set default values in module configuration. Will be overwritten by custom values
                    if prop_name == "default":
                        instance.configuration_data[config_option_info['name'].strip()] = prop_value
                    # Support for multiple datatypes using the pattern: "type: string||list;"
                if prop_name == "type":
                    prop_value = prop_value.split("||")
                    prop_value.append('Unicode')
                try:
                    instance.configuration_metadata[config_option_info['name'].strip()].update({prop_name: prop_value})
                except:
                    instance.configuration_metadata[config_option_info['name'].strip()] = {prop_name: prop_value}
        # Set self_hostname
        return instance

    return wrapper

def memoize(obj):
    cache = obj.cache = {}
    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoizer

class BoundedOrderedDict(collections.OrderedDict):
    def __init__(self, *args, **kwds):
        self.maxlen = kwds.pop("maxlen", None)
        collections.OrderedDict.__init__(self, *args, **kwds)
        self._checklen()

    def __setitem__(self, key, value):
        collections.OrderedDict.__setitem__(self, key, value)
        self._checklen()

    def _checklen(self):
        if self.maxlen is not None:
            while len(self) > self.maxlen:
                self.popitem(last=False)

def memoize(func=None, maxlen=None):
    """ Bounded memoize decorator.
        Found @http://stackoverflow.com/questions/9389307/how-do-i-create-a-bounded-memoization-decorator-in-python
    """
    if func:
        cache = BoundedOrderedDict(maxlen=maxlen)
        @functools.wraps(func)
        def memo_target(*args):
            lookup_value = args
            if lookup_value not in cache:
                cache[lookup_value] = func(*args)
            return cache[lookup_value]
        return memo_target
    else:
        def memoize_factory(func):
            return memoize(func, maxlen=maxlen)
        return memoize_factory