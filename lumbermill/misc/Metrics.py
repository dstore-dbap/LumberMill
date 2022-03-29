# -*- coding: utf-8 -*-
import numpy
import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.StatisticCollector import StatisticCollector, MultiProcessStatisticCollector
from lumbermill.utils.DynamicValues import mapDynamicValue
from lumbermill.utils.misc import TimedFunctionManager


@ModuleDocstringParser
class Metrics(BaseThreadedModule):
    """
    Collect metrics data from events.

    As a side note: This module inits MultiProcessStatisticCollector. As it uses multiprocessing.Manager().dict()
    this will start another process. So if you use SimpleStats, you will see workers + 1 processes in the process
    list.

    This module keeps track of the number of times a field occured in an event during interval.
    So, if you want to count the http_status codes encountered during the last 10s, you would use this configuration:
    - Mertrics:
        interval: 10
        aggregations:
            - key: http_status_%{vhost}
              value: http_status

    After interval seconds, an event will be emitted with the following fields (counters are just examples ;):
    {'data': '',
     'field_name': 'http_status_this.parrot.dead',
     'field_counts': {'200': 5, '301': 10, '400': 5},
     'lumbermill': {'event_id': 'cef34d298fbe8ce4b662251e17b2acfb',
                     'event_type': 'metrics',
                     'received_from': False,
                     'source_module': 'Metrics'}
     'interval': 10,
     'total_count': 20}

    Same with buckets:
        - Mertrics:
        interval: 10
        aggregations:
            - key: http_status_%{vhost}
              value: http_status
              buckets:
                - key: 100
                  upper: 199
                - key: 200
                  upper: 299
                - key: 300
                  upper: 399
                - key: 400
                  upper: 499
                - key: 500
                  upper: 599
        percentiles:
            - key: request_time_%{vhost}
              value: request_time
              percentiles: [50, 75, 95, 99]


    {'data': '',
     'field_name': 'http_status_this.parrot.dead',
     'field_counts': {'200': 5, '300': 10, '400': 5},
     'lumbermill': {'event_id': 'cef34d298fbe8ce4b662251e17b2acfb',
                     'event_type': 'metrics',
                     'received_from': False,
                     'source_module': 'Metrics'}
     'interval': 10,
     'total_count': 20}

    Configuration template:

    - Metrics:
       interval:                        # <default: 10; type: integer; is: optional>
       aggregations:                    # <default: []; type: list; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.interval = self.getConfigurationValue('interval')
        self.aggregations = self.getConfigurationValue('aggregations')
        self.aggregations_contain_dynamic_value = self.configuration_data['aggregations']['contains_dynamic_value']
        self.stats_namespace = "Metrics"
        self.stats_collector = StatisticCollector()
        self.mp_stats_collector = MultiProcessStatisticCollector()
        self.stats_collector.initCounter(self.stats_namespace)
        self.mp_stats_collector.initCounter(self.stats_namespace)
        for aggregation in self.aggregations:
            if "buckets" not in aggregation:
                continue
            aggregation["bucket_keys"] = []
            aggregation["bins"] = []
            for bucket in aggregation["buckets"]:
                aggregation["bucket_keys"].append(bucket["key"])
                aggregation["bins"].append(bucket["upper"])

    def getRunTimedFunctionsFunc(self):
        @setInterval(self.interval)
        def evaluateStats():
            self.accumulateMetrics()
            if self.lumbermill.is_master():
                self.sendMetrics()
        return evaluateStats

    def accumulateMetrics(self):
        for event_type, count in self.stats_collector.getAllCounters(namespace=self.stats_namespace).items():
            if count == 0:
                continue
            self.stats_collector.resetCounter(event_type, namespace=self.stats_namespace)
            self.mp_stats_collector.incrementCounter(event_type, count, namespace=self.stats_namespace)

    def sendMetrics(self):
        last_field_name = None
        field_counts = {}
        total_count = 0
        for field_name_value, field_count in sorted(self.mp_stats_collector.getAllCounters(namespace=self.stats_namespace).items()):
            if not isinstance(field_name_value, tuple):
                continue
            field_name, field_value = field_name_value
            self.mp_stats_collector.resetCounter(field_name_value, namespace=self.stats_namespace)
            if not last_field_name:
                last_field_name = field_name
            if field_name != last_field_name:
                self.sendEvent(DictUtils.getDefaultEventDict({"total_count": total_count,  "field_name": last_field_name, "field_counts": field_counts, "interval": self.interval}, caller_class_name="Metrics", event_type="metrics"))
                last_field_name = field_name
                field_counts = {}
                total_count = 0
            field_counts.update({field_value: field_count})
            total_count += field_count
        # Send remaining.
        if last_field_name:
            self.sendEvent(DictUtils.getDefaultEventDict({"total_count": total_count, "field_name": field_name, "field_counts": field_counts, "interval": self.interval}, caller_class_name="Metrics", event_type="metrics"))

    def initAfterFork(self):
        TimedFunctionManager.startTimedFunction(self.getRunTimedFunctionsFunc())
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        for aggregation in self.aggregations:
            if self.aggregations_contain_dynamic_value:
                key = mapDynamicValue(aggregation['key'], event)
            else:
                key = aggregation['key']
            if "bins" in aggregation:
                try:
                    value = aggregation["bucket_keys"][numpy.digitize(event[aggregation['value']], aggregation['bins'])]
                except KeyError:
                    continue
            else:
                value = event[aggregation['value']]
            try:
                self.stats_collector.incrementCounter((key, value), namespace=self.stats_namespace)
            except KeyError:
                continue
        yield event

    def shutDown(self):
        self.accumulateMetrics()
        if self.lumbermill.is_master():
            self.sendMetrics()
        BaseThreadedModule.shutDown(self)