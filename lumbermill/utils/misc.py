# -*- coding: utf-8 -*-
import sys
import os
import signal
import subprocess


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
    if sys.path[0] == '' and not os.environ.get("PYTHONPATH", "").startswith(path_prefix):
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