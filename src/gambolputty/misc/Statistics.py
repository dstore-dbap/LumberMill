import time
import Utils
import BaseModule
import Decorators

@Decorators.ModuleDocstringParser
class Statistics(BaseModule.BaseModule):
    """
    Collect and log some statistic data.

    Configuration example:

    - module: Statistics
      print_interval: 10                 # <default: 10; type: integer; is: optional>
      event_type_statistics: True        # <default: True; type: boolean; is: optional>
      receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
      waiting_event_statistics: True     # <default: True; type: boolean; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.stats_collector.setCounter('ts_last_stats', time.time())
        self.timed_functions = {'default': self.printIntervalStatistics}
        self.run_timed_functions_event = False
        self.run_timed_functions_func = self.getRunTimedFunctionsFunc()
        self.module_queues = {}

    def registerTimedFunction(self, key, func):
        self.stopTimedFunctions()
        self.timed_functions[key] = func
        self.startTimedFunctions()

    def unregisterTimedFunction(self, key):
        self.stopTimedFunctions()
        self.timed_functions.pop(key, None)
        self.startTimedFunctions()

    def getRunTimedFunctionsFunc(self):
        @Decorators.setInterval(self.getConfigurationValue('print_interval'))
        def runTimedFunctionsFunc(self):
            try:
                for key, func in self.timed_functions.iteritems():
                    try:
                        func()
                    except:
                        self.unregisterTimedFunction(key)
            except RuntimeError:
                # Changing the dictionary in un/registerTimedFunction may cause a
                # RuntimeError: dictionary changed size during iteration
                # even though we stop the timed functions before changing the dict.
                # We ignore this error, otherwise we would need to implement locks.
                pass
        return runTimedFunctionsFunc

    def printIntervalStatistics(self):
        self.logger.info("############# Statistics #############")
        if self.getConfigurationValue('receive_rate_statistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('waiting_event_statistics'):
            self.eventsInQueuesStatistics()
        if self.getConfigurationValue('event_type_statistics'):
            self.eventTypeStatistics()

    def eventTypeStatistics(self):
        self.logger.info(">> EventTypes Statistics")
        for event_type, count in sorted(self.stats_collector.getAllCounters().iteritems()):
            if not event_type.startswith('event_type_'):
                continue
            self.logger.info("EventType: %s%s%s - Hits: %s%s%s" % (Utils.AnsiColors.YELLOW, event_type.replace('event_type_', ''), Utils.AnsiColors.ENDC, Utils.AnsiColors.YELLOW, count, Utils.AnsiColors.ENDC))
            self.stats_collector.resetCounter(event_type)

    def receiveRateStatistics(self):
        self.logger.info(">> Receive rate stats")
        eps = self.stats_collector.getCounter('eps')
        if not eps:
            eps = 0
        self.stats_collector.resetCounter('eps')
        self.logger.info("Received events in %ss: %s%s (%s/eps)%s" % (self.getConfigurationValue('print_interval'), Utils.AnsiColors.YELLOW, eps, (eps/self.getConfigurationValue('print_interval')), Utils.AnsiColors.ENDC))

    def eventsInQueuesStatistics(self):
        if len(self.module_queues) == 0:
            return
        self.logger.info(">> Queue stats")
        for module_name, queue in self.module_queues.iteritems():
            self.logger.info("Events in %s queue: %s%s%s" % (module_name, Utils.AnsiColors.YELLOW, queue.qsize(), Utils.AnsiColors.ENDC))

    def run(self):
        # Get all configured queues for waiting event stats.
        for module_name, module_info in self.gp.modules.iteritems():
            instance = module_info['instances'][0]
            if not hasattr(instance, 'getInputQueue') or not instance.getInputQueue():
                continue
            self.module_queues[module_name] = instance.getInputQueue()
        self.startTimedFunctions()

    def startTimedFunctions(self):
        if not self.run_timed_functions_event or self.run_timed_functions_event.isSet():
            self.run_timed_functions_event = self.run_timed_functions_func(self)

    def stopTimedFunctions(self):
        if self.run_timed_functions_event:
            self.run_timed_functions_event.set()

    def destroyEvent(self, event=False, event_list=False):
        """Statistic module will not destroy any events."""
        pass

    def handleEvent(self, event):
        self.stats_collector.incrementCounter('eps')
        if self.getConfigurationValue('event_type_statistics'):
            try:
                self.stats_collector.incrementCounter('event_type_%s' % event['event_type'])
            except:
                pass
        yield event
