# -*- coding: utf-8 -*-
import time
import sys
import StatisticCollector
import Utils
import BaseThreadedModule
import BaseQueue
import Decorators

@Decorators.ModuleDocstringParser
class Statistics(BaseThreadedModule.BaseThreadedModule):
    """
    Collect and log some statistic data.

    Configuration example:

    - module: Statistics
      configuration:
        print_interval: 10               # <default: 10; type: integer; is: optional>
        regex_statistics: True             # <default: True; type: boolean; is: optional>
        receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
        waiting_event_statistics: True     # <default: True; type: boolean; is: optional>
        processing_event_statistics: True  # <default: True; type: boolean; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.printTimedIntervalStatistics()

    @Decorators.setInterval(10.0)
    def printTimedIntervalStatistics(self):
        self.logger.info("############# Statistics #############")
        if self.getConfigurationValue('regex_statistics'):
            self.regexStatistics()
        if self.getConfigurationValue('receive_rate_statistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('waiting_event_statistics'):
            self.eventsInQueuesStatistics()
        if self.getConfigurationValue('processing_event_statistics'):
            self.eventsInProcess()

    def regexStatistics(self):
        self.logger.info(">> Regex Statistics")
        for event_type, count in sorted(StatisticCollector.StatisticCollector().getAllCounters().iteritems()):
            if not event_type.startswith('event_type_'):
                continue
            event_type = event_type.replace('event_type_', '')
            self.logger.info("EventType: %s%s%s - Hits: %s%s%s" % (Utils.AnsiColors.YELLOW, event_type, Utils.AnsiColors.ENDC, Utils.AnsiColors.YELLOW, count, Utils.AnsiColors.ENDC))
            StatisticCollector.StatisticCollector().resetCounter(event_type)
        StatisticCollector.StatisticCollector().resetCounter('received_messages')

    def receiveRateStatistics(self):
        self.logger.info(">> Receive rate stats")
        rps = StatisticCollector.StatisticCollector().getCounter('rps')
        if not rps:
            rps = 0
        StatisticCollector.StatisticCollector().resetCounter('rps')
        self.logger.info("Received events in %ss: %s%s (%s/eps)%s" % (self.getConfigurationValue('print_interval'), Utils.AnsiColors.YELLOW, rps, (rps/self.getConfigurationValue('print_interval')), Utils.AnsiColors.ENDC))

    def eventsInQueuesStatistics(self):
        self.logger.info(">> Queue stats")
        self.logger.info("Events in queues: %s%s%s" % (BaseQueue.BaseQueue.messages_in_queues, Utils.AnsiColors.YELLOW, Utils.AnsiColors.ENDC))

    def eventsInProcess(self):
        self.logger.info(">> Processing stats")
        for module_name, counters in StatisticCollector.StatisticCollector().counter_stats_per_module.iteritems():
            self.logger.info("Events in process: %s%s - %s%s" % (Utils.AnsiColors.YELLOW, module_name, counters['events_in_process'], Utils.AnsiColors.ENDC))

    def handleData(self, data):
        StatisticCollector.StatisticCollector().incrementCounter('received_messages')
        StatisticCollector.StatisticCollector().incrementCounter('rps')
        try:
            StatisticCollector.StatisticCollector().incrementCounter('event_type_%s' % data['event_type'])
        except: 
            pass
        yield