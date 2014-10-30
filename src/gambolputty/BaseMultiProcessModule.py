# -*- coding: utf-8 -*-
import os
import multiprocessing
import msgpack
import signal
import Utils
import BaseModule

class BaseMultiProcessModule(BaseModule.BaseModule, multiprocessing.Process): #
    """
    Base class for all gambolputty modules that will run as separate processes.
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
            packed_data = self.input_queue.get(block, timeout)
            events = msgpack.unpackb(packed_data)
            # After msgpack.uppackb we just have a normal dict. Cast this to KeyDotNotationDict.
            for event in events:
                yield Utils.KeyDotNotationDict(event)
        except (KeyboardInterrupt, SystemExit, ValueError, OSError):
            # Keyboard interrupt is catched in GambolPuttys main run method.
            # This will take care to shutdown all running modules.
            pass

    def run(self):
        if not self.receivers:
            # Only issue warning for those modules that are expected to have receivers.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone', 'output']:
                self.logger.error("%sShutting down module %s since no receivers are set.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, Utils.AnsiColors.ENDC))
                return
        if not self.input_queue:
            # Only issue warning for those modules that are expected to have an input queue.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone', 'input']:
                self.logger.error("%sShutting down module %s since no input queue set.%s" % (Utils.AnsiColors.FAIL, self.__class__.__name__, Utils.AnsiColors.ENDC))
                return
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
