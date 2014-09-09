# -*- coding: utf-8 -*-
import Utils
import StatisticCollector as StatisticCollector
import BaseThreadedModule
import Decorators

@Decorators.ModuleDocstringParser
class Statistics(BaseThreadedModule.BaseThreadedModule):
    """
    Collect and log statistic data.

    This module keeps track of the number of times a field occured in an event during interval.
    So, if you want to count the http_status codes encountered during the last 10s, you would use this configuration:
    - Statistics:
        interval: 10
        fields: [http_status]

    After interval seconds, an event will be emitted with the following fields (counters are just examples ;):
    {'data': '',
     'event_type': 'statistic',
     'field_name': 'http_status',
     'field_counts': {'200': 5, '301': 10, '400': 5},
     'gambolputty': {'event_id': 'cef34d298fbe8ce4b662251e17b2acfb',
                     'event_type': 'statistic',
                     'received_from': False,
                     'source_module': 'Statistics'}
     'interval': 10,
     'total_count': 20}

    Configuration example:

    - Statistics:
        interval:                      # <default: 10; type: integer; is: optional>
        fields:                        # <default: ['gambolputty.event_type']; type: list; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        self.interval = self.getConfigurationValue('interval')
        self.fields = self.getConfigurationValue('fields')
        self.stats_collector = StatisticCollector.StatisticCollector()
        self.module_queues = {}

    def getRunTimedFunctionsFunc(self):
        @Decorators.setInterval(self.interval)
        def runTimedFunctionsFunc():
            self.printIntervalStatistics()
        return runTimedFunctionsFunc

    def printIntervalStatistics(self):
        last_field_name = None
        field_counts = {}
        total_count = 0
        for field_name_value, field_count in sorted(self.stats_collector.getAllCounters().items()):
            if not isinstance(field_name_value, tuple):
                continue
            field_name, field_value = field_name_value
            if field_name not in self.fields:
                continue
            self.stats_collector.resetCounter(field_name_value)
            if not last_field_name:
                last_field_name = field_name
            if field_name != last_field_name:
                self.sendEvent(Utils.getDefaultEventDict({"total_count": total_count, "count_per_sec": (field_counts/self.interval), "field_name": last_field_name, "field_counts": field_counts, "interval": self.interval }, caller_class_name="Statistics", event_type="statistic"))
                last_field_name = field_name
                field_counts = {}
                total_count = 0
                #if self.emit_as_event:
                #    self.logger.info("Received events in %ss: %s%s (%s/eps)%s" % (self.getConfigurationValue('interval'), Utils.AnsiColors.YELLOW, field_count, (field_count/self.getConfigurationValue('interval')), Utils.AnsiColors.ENDC))
            field_counts.update({field_value: field_count})
            total_count += field_count
        # Send remaining.
        if last_field_name:
            self.sendEvent(Utils.getDefaultEventDict({"total_count": total_count, "count_per_sec": (field_counts/self.interval), "field_name": field_name, "field_counts": field_counts, "interval": self.interval }, caller_class_name="Statistics", event_type="statistic"))

    def prepareRun(self):
        timed_func = self.getRunTimedFunctionsFunc()
        Utils.TimedFunctionManager.startTimedFunction(timed_func)
        BaseThreadedModule.BaseThreadedModule.prepareRun()

    def handleEvent(self, event):
        for field in self.fields:
            if field not in event:
                continue
            self.stats_collector.incrementCounter((field, event[field]))
        yield event
