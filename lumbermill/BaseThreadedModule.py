# -*- coding: utf-8 -*-
import threading
import BaseModule


# Conditional imports for python2/3
try:
    import Queue as queue
except ImportError:
    import queue

class BaseThreadedModule(BaseModule.BaseModule, threading.Thread):
    """
    Base class for all lumbermill modules. In most cases this is the class to inherit from when implementing a new module.
    It will only be started as thread when necessary. This depends on the configuration and how the modules are
    combined.

    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned...

    Configuration template:

    - module: SomeModuleName
       id:                               # <default: ""; type: string; is: optional>
       filter:                           # <default: None; type: None||string; is: optional>
       add_fields:                       # <default: {}; type: dict; is: optional>
       delete_fields:                    # <default: []; type: list; is: optional>
       event_type:                       # <default: None; type: None||string; is: optional>
       log_level:                        # <default: 'info'; type: string; values: ['info', 'warn', 'error', 'critical', 'fatal', 'debug']; is: optional>
       queue_size:                       # <default: 20; type: integer; is: optional>
       receivers:
        - ModuleName
        - ModuleAlias
    """

    def __init__(self, gp):
        BaseModule.BaseModule.__init__(self, gp)
        threading.Thread.__init__(self)
        self.input_queue = False
        self.alive = True
        self.daemon = True

    def setInputQueue(self, queue):
        self.input_queue = queue

    def getInputQueue(self):
        return self.input_queue

    def pollQueue(self, block=True, timeout=None):
        try:
            for event in self.input_queue.get(block, timeout):
                yield event
        except (KeyboardInterrupt, SystemExit, ValueError, OSError):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass

    def run(self):
        # Module will only be run as thread if an input_queue exists. This will depend on the actual configuration.
        # This behaviour can be overwritten by implementing a custom run method.
        if not self.input_queue:
            return False
        if not self.receivers:
            # Only issue warning for those modules that are expected to have receivers.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone', 'output']:
                self.logger.error("Shutting down module %s since no receivers are set." % (self.__class__.__name__))
                return
        while self.alive:
            for event in self.pollQueue():
                if not event:
                    continue
                self.receiveEvent(event)
