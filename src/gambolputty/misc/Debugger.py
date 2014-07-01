# -*- coding: utf-8 -*-
import BaseMultiProcessModule
import Utils
import Decorators
import time
import collections
import operator

try:
    from __pypy__.builders import UnicodeBuilder
except ImportError:
    UnicodeBuilder = None

@Decorators.ModuleDocstringParser
class Debugger(BaseMultiProcessModule.BaseMultiProcessModule):

    module_type = "stand_alone"
    """Set module type"""

    can_run_parallel = False

    def configure(self, configuration):
        # Call parent configure method
        BaseMultiProcessModule.BaseMultiProcessModule.configure(self, configuration)
        self.interval = 10
        self.times = collections.defaultdict(int)
        self.counts = collections.defaultdict(int)
        for module_name, module_info in sorted(self.gp.modules.items(), key=lambda x: x[1]['idx']):
            for module_instance in module_info['instances']:
                #print "Decorating %s.receiveEvent" % module_name
                module_instance.receiveEvent = self.wrap(module_instance, module_instance.receiveEvent, self.addReceiveTimeStamp)
                #print "Decorating %s.sendEvent" % module_name
                module_instance.sendEvent = self.wrap(module_instance, module_instance.sendEvent, self.calculateTimeSpendInModule)
        Utils.TimedFunctionManager.startTimedFunction(self.getRunTimedFunctionsFunc())

    def getRunTimedFunctionsFunc(self):
        @Decorators.setInterval(self.interval)
        def runTimedFunctionsFunc():
            self.printIntervalStatistics()
        return runTimedFunctionsFunc

    def printIntervalStatistics(self):
        self.logger.info("############# Debug #############")
        #for mod_name, times in self.times.items():
        for module_name, times in sorted(self.times.items(), key=operator.itemgetter(1), reverse=True):
            self.logger.info("%s: %s (mean of %s entries)"  % (module_name, times/self.counts[module_name], self.counts[module_name]))
        self.times = collections.defaultdict(int)
        self.counts = collections.defaultdict(int)

    def wrap(self, wrapped_instance, wrapped_func, payload):
        def wrapper(event):
            event = payload(wrapped_instance, event)
            return wrapped_func(event)
        return wrapper

    def addReceiveTimeStamp(self, wrapped_instance, event):
        event['gambolputty']['debug_entered_module'] = time.time()
        return event

    def calculateTimeSpendInModule(self, wrapped_instance, event):
        if 'debug_entered_module' in event['gambolputty']:
            self.times[wrapped_instance.__class__.__name__] += time.time() - event['gambolputty']['debug_entered_module']
            self.counts[wrapped_instance.__class__.__name__] += 1
            event['gambolputty'].pop('debug_entered_module')
        return event
