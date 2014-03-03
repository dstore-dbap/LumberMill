# -*- coding: utf-8 -*-
import logging
import logging.handlers
import os
import BaseThreadedModule
import BaseMultiProcessModule
import Decorators
import Utils
import time
import sys


@Decorators.ModuleDocstringParser
class FileSink(BaseMultiProcessModule.BaseMultiProcessModule):
    """
    Store events in a file.

    path: Path to logfiles. String my contain any of pythons strtime directives.
    name_pattern: Filename pattern. String my conatain pythons strtime directives and event fields.
    format: Which event fields to use in the logline, e.g. '%(@timestamp)s - %(url)s - %(country_code)s'
    store_interval_in_secs: sending data to es in x seconds intervals.
    batch_size: sending data to es if event count is above, even if store_interval_in_secs is not reached.
    backlog_size: maximum count of events waiting for transmission. Events above count will be dropped.

    Configuration example:

    - FileSink:
        path:                                 # <type: string; is: required>
        name_pattern:                         # <type: string; is: required>
        format:                               # <type: string; is: required>
        store_interval_in_secs:               # <default: 10; type: integer; is: optional>
        batch_size:                           # <default: 500; type: integer; is: optional>
        backlog_size:                         # <default: 5000; type: integer; is: optional>
    """

    module_type = "output"
    """Set module type"""
    can_run_parallel = False

    def configure(self, configuration):
         # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.events_container = []
        self.batch_size = self.getConfigurationValue('batch_size')
        self.backlog_size = self.getConfigurationValue('backlog_size')
        self.fileloggers = {}
        self.path = self.getConfigurationValue('path')
        self.name_pattern = self.getConfigurationValue('path')
        self.is_storing = False
        self.timed_store_func = self.getTimedStoreFunc()

    def getTimedStoreFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('store_interval_in_secs'))
        def timedStoreEvents():
            if self.is_storing:
                return
            self.storeEvents(self.events_container)
        return timedStoreEvents

    @Decorators.setInterval(60)
    def clearStaleLoggers(self):
        now = time.time()
        for key in self.fileloggers.keys():
            logger_last_used = self.fileloggers[key][1]
            #print "%s - %s = %s" % (now, logger_last_used, (now - logger_last_used))
            if now - logger_last_used < 300:
                continue
            self.logger.info('Dropping logger')
            for handler in self.fileloggers[key][0].handlers:
                handler.stream.close()
                handler.stream = None
            del self.fileloggers[key]

    def getLogger(self, key):
        try:
            logger, last_used = self.fileloggers[key]
            self.fileloggers[key][1] = time.time()
        except KeyError:
            path = time.strftime(self.path)
            if not os.path.exists(path):
                os.mkdir(path)
            handler = logging.handlers.WatchedFileHandler('%s/%s' % (path, key))
            logger = logging.getLogger(key)
            logger.addHandler(handler)
            logger.propagate = False
            self.fileloggers[key] = [logger, time.time()]
        return logger

    def run(self):
        self.startTimedFunction(self.clearStaleLoggers)
        self.startTimedFunction(self.timed_store_func)
         # Call parent run method
        BaseMultiProcessModule.BaseMultiProcessModule.run(self)

    def handleEvent(self, event):
        # Wait till a running store is finished to avoid strange race conditions.
        while self.is_storing:
            time.sleep(.001)
        if len(self.events_container) >= self.backlog_size:
            self.logger.warning("%sMaximum number of events (%s) in backlog reached. Dropping event.%s" % (Utils.AnsiColors.WARNING, self.backlog_size, Utils.AnsiColors.ENDC))
            yield event
            return
        self.events_container.append(event)
        if len(self.events_container) >= self.batch_size:
            self.storeEvents(self.events_container)
        yield event

    def storeEvents(self, events):
        if len(events) == 0:
            return
        self.is_storing = True
        for event in events:
            try:
                key = time.strftime(self.getConfigurationValue('name_pattern'))
                key = key % event
                logger = self.getLogger(key)
                logger.info(self.getConfigurationValue('format', event))
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error('%sCould no log event %s. Excpeption: %s, Error: %s.%s' % (Utils.AnsiColors.FAIL, event, etype, evalue, Utils.AnsiColors.ENDC))
        self.events_container = []
        self.is_storing = False

    def shutDown(self, silent=False):
        if hasattr(self, 'fileloggers'):
            for key in self.fileloggers.keys():
                for handler in self.fileloggers[key][0].handlers:
                    try:
                        handler.stream.close()
                    except:
                        pass
                del self.fileloggers[key]
        BaseMultiProcessModule.BaseMultiProcessModule.shutDown(self, silent=False)
