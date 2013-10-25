# -*- coding: utf-8 -*-
import sys
import threading
import re
import ast
from functools import wraps

def singleton(cls):
    """Decorator to create a singleton."""
    instance = cls()
    instance.__call__ = lambda: instance
    return instance

def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)
            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator

def GambolPuttyModule(cls):
    @wraps(cls)
    def wrapper(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.configuration_metadata = {}
        config_option_regex = "\s*(?P<name>.*?):.*?#\s*<(?P<props>.*?)>"
        regex = re.compile(config_option_regex,re.MULTILINE)
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
                prop_name, prop_value = [ m.strip() for m in prop_info.split(":", 1)]
                if prop_name == "default":
                    try:
                        prop_value = ast.literal_eval(prop_value)
                    except:
                        etype, evalue, etb = sys.exc_info()
                        instance.logger.error("Could not parse default value %s from docstring. Excpeption: %s, Error: %s." % (prop_value,etype, evalue))
                        print "Could not parse default value %s from docstring. Excpeption: %s, Error: %s." % (prop_value,etype, evalue)
                try:
                    instance.configuration_metadata[config_option_info['name'].strip()].update({prop_name: prop_value})
                except:
                    instance.configuration_metadata[config_option_info['name'].strip()] = {prop_name: prop_value}
        return instance
    return wrapper