# -*- coding: utf-8 -*-
import os
import multiprocessing
import signal
import BaseModule


class BaseMultiProcessModule(BaseModule.BaseModule, multiprocessing.Process): #
    """
    Base class for all lumbermill modules that will run as separate processes.
    If you happen to override one of the methods defined here, be sure to know what you
    are doing ;) You have been warned...

    id: Id of the module. If multiple instances of the same modules are used, id can be used to reference the correct receiver.
    filter: Filter expression to apply to incoming events. If filter succeeds, module will handle the event, else
            the event will be passed to next module unchanged.
    pool_size: How many processes should be spawned.
    queue_size: How many events may be waiting in queue.
    queue_buffer_size: How many events will be buffered before sending them to queue.

    Configuration template:

    - module: SomeModuleName
       id:                               # <default: ""; type: string; is: optional>
       filter:                           # <default: None; type: None||string; is: optional>
       add_fields:                       # <default: {}; type: dict; is: optional>
       delete_fields:                    # <default: []; type: list; is: optional>
       event_type:                       # <default: None; type: None||string; is: optional>
       log_level:                        # <default: 'info'; type: string; values: ['info', 'warn', 'error', 'critical', 'fatal', 'debug']; is: optional>
       pool_size:                        # <default: 2; type: integer; is: optional>
       queue_size:                       # <default: 50; type: integer; is: optional>
       queue_buffer_size:                # <default: 250; type: integer; is: optional>
       receivers:
        - ModuleName
        - ModuleAlias
    """

    def __init__(self, gp):
        BaseModule.BaseModule.__init__(self, gp)
        multiprocessing.Process.__init__(self)
        self.input_queue = False
        self.alive = False
        self.worker = None

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
        if not self.receivers:
            # Only issue warning for those modules that are expected to have receivers.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone', 'output']:
                self.logger.error("Shutting down module %s since no receivers are set." % (self.__class__.__name__))
                return False
        if not self.input_queue:
            # Only issue warning for those modules that are expected to have an input queue.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone', 'input']:
                self.logger.error("Shutting down module %s since no input queue set." % (self.__class__.__name__))
                return False
        self.alive = True
        self.process_id = os.getpid()
        while self.alive:
            for event in self.pollQueue():
                if not event:
                    continue
                self.receiveEvent(event)

    def shutDown(self):
        # Call parent shutDown method
        BaseModule.BaseModule.shutDown(self)
        try:
            self.input_queue.close()
        except:
            pass
        # Kill self via signal. Otherwise a simple reload will not terminate the worker processes.
        # Why that is escapes me...
        self.alive = False
        if self.pid:
            os.kill(self.pid, signal.SIGQUIT)
