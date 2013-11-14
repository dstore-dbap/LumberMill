import time
import sys
import StatisticCollector
import Utils
import BaseThreadedModule
import threading
import traceback
import Decorators

@Decorators.ModuleDocstringParser
class MultiProcessStatistics(BaseThreadedModule.BaseThreadedModule):
    """
    Collect and log some statistic data.

    Configuration example:

    - module: Statistics
      configuration:
        print_interval: 10               # <default: 10; type: integer; is: optional>
        regex_statistics: True             # <default: True; type: boolean; is: optional>
        receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
        waiting_event_statistics: True     # <default: True; type: boolean; is: optional>
        processing_event_statistics: True  # <default: False; type: boolean; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    lock = threading.Lock()

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        StatisticCollector.StatisticCollector().setCounter('ts_last_stats', time.time())

    def printTimedIntervalStatistics(self):
        self.logger.info("############# Statistics #############")
        if self.getConfigurationValue('receive_rate_statistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('waiting_event_statistics'):
            self.eventsInQueuesStatistics()
        if self.getConfigurationValue('processing_event_statistics'):
            self.eventsInProcess()
        if self.getConfigurationValue('regex_statistics'):
            self.regexStatistics()

    def regexStatistics(self, stats):
        self.logger.info(">> Regex Statistics")
        for event_type, count in sorted(StatisticCollector.StatisticCollector().getAllCounters().iteritems()):
            if not event_type.startswith('event_type_'):
                continue
            print("EventType: %s%s%s - Hits: %s%s%s" % (Utils.AnsiColors.YELLOW, event_type.replace('event_type_', ''), Utils.AnsiColors.ENDC, Utils.AnsiColors.YELLOW, count, Utils.AnsiColors.ENDC))
            StatisticCollector.StatisticCollector().resetCounter(event_type)

    def receiveRateStatistics(self):
        self.logger.info(">> Receive rate stats")
        rps = StatisticCollector.StatisticCollector().getCounter('rps')
        if not rps:
            rps = 0
        StatisticCollector.StatisticCollector().resetCounter('rps')
        self.logger.info("Received events in %ss: %s%s (%s/eps)%s" % (self.getConfigurationValue('print_interval'), Utils.AnsiColors.YELLOW, rps, (rps/self.getConfigurationValue('print_interval')), Utils.AnsiColors.ENDC))

    def eventsInQueuesStatistics(self):
        self.logger.info(">> Queue stats")
        self.logger.info("Events in queues: %s%s%s" % (StatisticCollector.MultiProcessStatisticCollector().getCounter('events_in_queues'), Utils.AnsiColors.YELLOW, Utils.AnsiColors.ENDC))

    def eventsInProcess(self):
        self.logger.info(">> Processing stats")
        self.logger.info("Events in process: %s%s%s" % (Utils.AnsiColors.YELLOW, StatisticCollector.MultiProcessStatisticCollector().getCounter('events_in_process'), Utils.AnsiColors.ENDC))

    def run(self):
        if not self.input_queue:
            # Only issue warning for those modules that are expected to have an input queue.
            # TODO: A better solution should be implemented...
            if self.module_type not in ['stand_alone']:
                self.logger.warning("%sShutting down module %s since no input queue set.%s" % (Utils.AnsiColors.WARNING, self.__class__.__name__, Utils.AnsiColors.ENDC))
            return
        while self.is_alive:
            data = False
            try:
                data = self.getEventFromInputQueue()
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("%sCould not read data from input queue.%s" % (Utils.AnsiColors.FAIL, Utils.AnsiColors.ENDC) )
                traceback.print_exception(exc_type, exc_value, exc_tb)
                continue
            for data in self.handleData(data):
                self.addEventToOutputQueues(data)

    def handleData(self, event):
        StatisticCollector.StatisticCollector().incrementCounter('rps')
        if self.getConfigurationValue('regex_statistics'):
            try:
                StatisticCollector.StatisticCollector().incrementCounter('event_type_%s' % event['event_type'])
            except:
                pass
        now = time.time()
        if now - StatisticCollector.StatisticCollector().getCounter('ts_last_stats') >= self.getConfigurationValue('print_interval'):
            StatisticCollector.StatisticCollector().setCounter('ts_last_stats', now)
            self.printTimedIntervalStatistics()
        yield