# -*- coding: utf-8 -*-
import time
import sys
import gambolputty.Decorators as Decorators
import gambolputty.StatisticCollector as StatisticCollector
import gambolputty.Utils as Utils
import BaseThreadedModule
import BaseQueue
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class Statistics(BaseThreadedModule.BaseThreadedModule):
    """
    Collect and log some statistic data.

    Configuration example:

    - module: Statistics
      configuration:
        print_interval: 1000               # <default: 1000; type: integer; is: optional>
        regex_statistics: True             # <default: True; type: boolean; is: optional>
        receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
        waiting_event_statistics: True     # <default: True; type: boolean; is: optional>
    """

    def configure(self, configuration):
         # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.print_regex_statistics_at_message_count = self.getConfigurationValue('print_interval')

    def regexStatistics(self):
        if not StatisticCollector.StatisticCollector().getCounter('received_messages') % self.print_regex_statistics_at_message_count == 0:
            return
        # log statistic data
        self.logger.info("########## Regex Statistics ##########")
        for event_type, count in sorted(StatisticCollector.StatisticCollector().getAllCounters().iteritems()):
            if event_type in ['rps', 'received_messages']:
                continue
            self.logger.info("EventType: %s%s%s - Hits: %s%s%s" % (Utils.AnsiColors.YELLOW, event_type, Utils.AnsiColors.ENDC, Utils.AnsiColors.YELLOW, count, Utils.AnsiColors.ENDC))
            StatisticCollector.StatisticCollector().resetCounter(event_type)
        self.logger.info("Total events: %s%s%s." % (Utils.AnsiColors.YELLOW, StatisticCollector.StatisticCollector().getCounter('received_messages'), Utils.AnsiColors.ENDC))
        StatisticCollector.StatisticCollector().resetCounter('received_messages')
        
    @Decorators.setInterval(5.0)
    def receiveRateStatistics(self):
        rps = StatisticCollector.StatisticCollector().getCounter('rps')
        if not rps:
            rps = 0
        StatisticCollector.StatisticCollector().resetCounter('rps')
        self.logger.info("Received events in 5s: %s%s (%s/eps)%s" % (Utils.AnsiColors.YELLOW, rps, (rps/5), Utils.AnsiColors.ENDC))

    @Decorators.setInterval(5.0)
    def waitingEventStatistics(self):
        self.logger.info("Events waiting to be served: %s%s%s" % (Utils.AnsiColors.YELLOW, BaseQueue.BaseQueue.messages_in_queues, Utils.AnsiColors.ENDC))
        
    def run(self):
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        if self.getConfigurationValue('receive_rate_statistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('waiting_event_statistics'):
            self.waitingEventStatistics()
        while True:
            try:
                item = self.getEventFromInputQueue()
                self.handleData(item)
                if self.getConfigurationValue('regex_statistics'):
                    self.regexStatistics()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not read data from input queue. Excpeption: %s, Error: %s." % (etype, evalue))
                time.sleep(1)
    
    def handleData(self, data):
        StatisticCollector.StatisticCollector().incrementCounter('received_messages')
        StatisticCollector.StatisticCollector().incrementCounter('rps')
        try:
            StatisticCollector.StatisticCollector().incrementCounter(data['event_type'])
        except: 
            pass