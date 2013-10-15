import time
import sys
import gambolputty.Decorators as Decorators
import gambolputty.StatisticCollector as StatisticCollector
import gambolputty.Utils as Utils
import BaseModule

class Statistics(BaseModule.BaseModule):

    def setup(self):
        # Call parent setup method
        super(Statistics, self).setup()
        self.print_regex_statistics_at_message_count = 500
       
    def configure(self, configuration):
         # Call parent configure method
        super(Statistics, self).configure(configuration)
        if 'print_regex_statistics_at_message_count' in configuration:
            self.print_regex_statistics_at_message_count = configuration['print_regex_statistics_at_message_count']

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
        self.logger.info("Events waiting to be served: %s%s%s" % (Utils.AnsiColors.YELLOW, BaseModule.BaseModule.messages_in_queues, Utils.AnsiColors.ENDC))
        
    def run(self):
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        if 'receiveRateStatistics' in self.config:
            self.receiveRateStatistics()
        if 'waitingEventStatistics' in self.config:
            self.waitingEventStatistics()
        while True:
            try:
                item = self.input_queue.get()
                self.handleData(item)
                if self.config['regexStatistics']:
                    self.regexStatistics()
                self.input_queue.task_done()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not read data from input queue. Excpeption: %s, Error: %s." % (etype, evalue))
                time.sleep(1)
            finally:
                self.decrementQueueCounter()
    
    def handleData(self, data):
        StatisticCollector.StatisticCollector().incrementCounter('received_messages')
        StatisticCollector.StatisticCollector().incrementCounter('rps')
        try:
            StatisticCollector.StatisticCollector().incrementCounter(data['message_type'])
        except: 
            pass