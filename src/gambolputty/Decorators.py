# -*- coding: utf-8 -*-
import sys
import time
import threading
import re
import ast
import multiprocessing
from functools import wraps


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
    @wraps(cls)
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
                except ValueError:
                    instance.logger.debug("Could not parse config setting %s." % config_option_info)
                    continue
                if prop_name in ["default", "values"]:
                    try:
                        prop_value = ast.literal_eval(prop_value)
                    except:
                        etype, evalue, etb = sys.exc_info()
                        instance.logger.error(
                            "Could not parse %s from docstring. Excpeption: %s, Error: %s." % (prop_value, etype, evalue))
                        print "Could not parse %s from docstring. Excpeption: %s, Error: %s." % (prop_value, etype, evalue)
                    # Support for multiple datatypes using the pattern: "type: string||list;"
                if prop_name == "type":
                    prop_value = prop_value.split("||")
                    prop_value.append('Unicode')
                try:
                    instance.configuration_metadata[config_option_info['name'].strip()].update({prop_name: prop_value})
                except:
                    instance.configuration_metadata[config_option_info['name'].strip()] = {prop_name: prop_value}
        return instance

    return wrapper