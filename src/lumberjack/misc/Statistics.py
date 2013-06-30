import time
import lumberjack.Decorators as Decorators
import lumberjack.StatisticCollector as StatisticCollector
import BaseModule

class Statistics(BaseModule.BaseModule):
    
    print_regex_statistics_at_message_count = 500
       
    def configure(self, configuration):
        self.config = configuration
        if configuration['print_regex_statistics_at_message_count']:
            self.print_regex_statistics_at_message_count = configuration['print_regex_statistics_at_message_count']

    def regexStatistics(self):
        if not StatisticCollector.StatisticCollector().getCounter('received_messages') % self.print_regex_statistics_at_message_count == 0:
            return
        total_messages_count = total_failures_count = 0
        # log statistic data 
        self.logger.info("########## Regex Statistics ##########")
        for message_type, count in sorted(StatisticCollector.StatisticCollector().getAllCounters().iteritems()):
            if message_type in ['rps', 'received_messages']:
                continue
            self.logger.info("MessageType: %s - Hits: %s" % (message_type, count))
            StatisticCollector.StatisticCollector().resetCounter(message_type)
        self.logger.info("Total messages: %s." % (StatisticCollector.StatisticCollector().getCounter('received_messages')))
        StatisticCollector.StatisticCollector().resetCounter('received_messages')
        
    @Decorators.setInterval(5.0)
    def receiveRateStatistics(self):
        rps = StatisticCollector.StatisticCollector().getCounter('rps')
        if not rps:
            rps = 0
        StatisticCollector.StatisticCollector().resetCounter('rps')
        self.logger.info("Received messages in 5s: %s (%s/rps)" % (rps, (rps/5)))
        
    def run(self):
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        if self.config['receiveRateStatistics']:
            self.receiveRateStatistics()
        while True:
            try:
                self.handleData(self.input_queue.get())
                if self.config['regexStatistics']:
                    self.regexStatistics()
                self.input_queue.task_done()
            except Exception, e:
                self.logger.error("Could not read data from input queue. Excpeption: %s, Error: %s." % (Exception, e))
                time.sleep(1)
    
    def handleData(self, data):
        StatisticCollector.StatisticCollector().incrementCounter('received_messages')
        StatisticCollector.StatisticCollector().incrementCounter('rps')
        try:
            StatisticCollector.StatisticCollector().incrementCounter(data['message_type'])
        except: 
            pass