# -*- coding: utf-8 -*-
import time
import sys
import gambolputty.Decorators as Decorators
import gambolputty.StatisticCollector as StatisticCollector
import gambolputty.Utils as Utils
import BaseModule
import BaseQueue
from Decorators import GambolPuttyModule

@GambolPuttyModule
class Statistics(BaseModule.BaseModule):
    """
    Collect and log some statistic data.

    Configuration example:

    - module: Statistics
      configuration:
        print-regex-statistics-interval: 1000               # <default: 1000; type: integer; is: optional>
        regexStatistics: True                               # <default: True; type: boolean; is: optional>
        receiveRateStatistics: True                         # <default: True; type: boolean; is: optional>
        waitingEventStatistics: True                        # <default: True; type: boolean; is: optional>
    """

    def configure(self, configuration):
         # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.print_regex_statistics_at_message_count = self.getConfigurationValue('print-regex-statistics-interval')

    def regexStatistics(self):
        if not StatisticCollector.StatisticCollector().getCounter('received_messages') % self.print_regex_statistics_at_message_count == 0:
            return
        # log statistic data
        self.logger.info("########## Regex Statistics ##########")
        for message_type, count in sorted(StatisticCollector.StatisticCollector().getAllCounters().iteritems()):
            if message_type in ['rps', 'received_messages']:
                continue
            self.logger.info("EventType: %s%s%s - Hits: %s%s%s" % (Utils.AnsiColors.YELLOW, message_type, Utils.AnsiColors.ENDC, Utils.AnsiColors.YELLOW, count, Utils.AnsiColors.ENDC))
            StatisticCollector.StatisticCollector().resetCounter(message_type)
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
        if self.getConfigurationValue('receiveRateStatistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('waitingEventStatistics'):
            self.waitingEventStatistics()
        while True:
            try:
                item = self.input_queue.get()
                self.handleData(item)
                if self.getConfigurationValue('regexStatistics'):
                    self.regexStatistics()
                self.input_queue.task_done()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not read data from input queue. Excpeption: %s, Error: %s." % (etype, evalue))
                time.sleep(1)
    
    def handleData(self, data):
        StatisticCollector.StatisticCollector().incrementCounter('received_messages')
        StatisticCollector.StatisticCollector().incrementCounter('rps')
        try:
            StatisticCollector.StatisticCollector().incrementCounter(data['message_type'])
        except: 
            pass