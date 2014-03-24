# -*- coding: utf-8 -*-
import os
import pprint
import gc
import time
import zmq
import BaseModule
import BaseThreadedModule
import Utils
import Decorators


@Decorators.ModuleDocstringParser
class EventBuffer(BaseThreadedModule.BaseThreadedModule):
    """
    Send an event into a tarpit before passing it on.

    Useful only for testing purposes of threading problems and concurrent access to event data.

    Configuration example:

    - EventBuffer:
        interface:         # <default: '127.0.0.1'; type: string; is: optional>
        port:              # <default: 5678; type: integer; is: optional>
        receivers:
          - NextModule
    """

    module_type = "misc"
    """Set module type"""
    can_run_parallel = False

    def configure(self, configuration):
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.pid_on_init = os.getpid()
        self.buffer = {}
        self.connection_info = "%s:%s" % (self.getConfigurationValue("interface"), self.getConfigurationValue("port"))
        self.zmq_context = zmq.Context()
        self.server = self.zmq_context.socket(zmq.PULL)
        self.server.bind('tcp://%s' % self.connection_info)
        def notifyOnGarbageCollect(self):
            if not self["gambolputty.socket"]:
                return
            client = None
            try:
                zmq_context = zmq.Context()
                client = zmq_context.socket(zmq.PUSH)
                client.linger = 10
                client.connect("tcp://%s" % self['gambolputty']['socket'])
                client.send('%s' % self['gambolputty']['event_id'])
            except:
                pass
            # Hmm, uncommenting this code causes hangs when shutting down gp.
            #finally:
            #    if client:
            #        client.close()
            #        zmq_context.term()

        Utils.KeyDotNotationDict.__del__ = notifyOnGarbageCollect
        self.flush_interval = 5
        self.timedFuncHandle = self.startTimedFunction(self.getTimedGarbageCollectFunc())

    def getTimedGarbageCollectFunc(self):
        @Decorators.setInterval(self.flush_interval)
        def timedGarbageCollect():
            # Stop timed function if we are running in a forked process.
            if self.isForkedProcess():
                self.timedFuncHandle.set()
                return
            if len(self.buffer) == 0:
                return
            self.handleDeletedEvents()
        return timedGarbageCollect

    def isForkedProcess(self):
        return self.pid_on_init != os.getpid()

    def handleEvent(self, event):
        self.buffer[event['gambolputty']['event_id']] = {'refcount': 1, 'data': event.copy()}
        event['gambolputty']['socket'] = self.connection_info
        yield event

    def handleDeletedEvents(self, force_gc=False):
        if force_gc:
            gc.collect()
            time.sleep(1)
        counter = 0
        while True:
            try:
                deleted_event_id = self.server.recv(flags=zmq.NOBLOCK)
            except:
                break
            try:
                event_info = self.buffer.pop(deleted_event_id)
            except KeyError:
                print deleted_event_id
                continue
            del event_info['data']['gambolputty']['socket']
            event_info = None
            counter += 1
        #self.logger.info("%sDeleted %s handled events.%s" % (Utils.AnsiColors.LIGHTBLUE, counter, Utils.AnsiColors.ENDC))
        #self.logger.info("%sRemaining: %s.%s" % (Utils.AnsiColors.LIGHTBLUE, len(self.buffer), Utils.AnsiColors.ENDC))


    def shutDown(self, silent=False):
        if len(self.buffer) > 0:
            self.handleDeletedEvents(force_gc=True)
            if not silent:
                self.logger.info("%sRemaining unhandled events: %s. Any unhandled events will be queued on next startup.%s" % (Utils.AnsiColors.LIGHTBLUE, len(self.buffer), Utils.AnsiColors.ENDC))
        try:
            self.server.close()
            self.zmq_context.term()
        except:
            pass
        BaseThreadedModule.BaseThreadedModule.shutDown(self, silent)