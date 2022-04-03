# -*- coding: utf-8 -*-
import numpy
import lumbermill.utils.DictUtils as DictUtils

from collections import defaultdict
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
            - name: http_status_%{vhost}
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
                - name: http_status_%{vhost}
                  field: http_status
                  buckets:
                    - name: 100
                      upper: 199
                    - name: 200
                      upper: 299
                    - name: 300
                      upper: 399
                    - name: 400
                      upper: 499
                    - name: 500
                      upper: 599
            percentiles:
                - name: request_time_%{vhost}
                  field: request_time
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
       percentiles:                     # <default: []; type: list; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.interval = self.getConfigurationValue('interval')
        self.aggregations = self.getConfigurationValue('aggregations')
        self.aggregations_contain_dynamic_value = self.configuration_data['aggregations']['contains_dynamic_value']
        self.aggregations_counter = defaultdict(int)
        self.percentiles = self.getConfigurationValue('percentiles')
        self.percentiles_contain_dynamic_value = self.configuration_data['percentiles']['contains_dynamic_value']
        self.percentile_values = defaultdict(list)
        self.stats_namespace = "Metrics"
        self.mp_stats_collector = MultiProcessStatisticCollector()
        self.mp_stats_collector.initCounter(self.stats_namespace)
        self.mp_stats_collector.initValues(self.stats_namespace)
        for aggregation in self.aggregations:
            if "buckets" not in aggregation:
                continue
            aggregation["bucket_names"] = []
            aggregation["bins"] = []
            for bucket in aggregation["buckets"]:
                aggregation["bucket_names"].append(bucket["name"])
                aggregation["bins"].append(bucket["upper"])
        self.name_to_percentiles = dict()
        for percentile in self.percentiles:
            self.name_to_percentiles[percentile["name"]] = percentile["percentiles"]

    def getRunTimedFunctionsFunc(self):
        @setInterval(self.interval)
        def evaluateStats():
            self.accumulateMetrics()
            if self.lumbermill.is_master():
                self.sendMetrics()
        return evaluateStats

    def accumulateMetrics(self):
        for idx, count in self.aggregations_counter.items():
            self.mp_stats_collector.incrementCounter(idx, count, namespace=self.stats_namespace)
            self.aggregations_counter[idx] = 0
        for idx, values in self.percentile_values.items():
            if not values:
                continue
            self.mp_stats_collector.appendValues(idx, values, namespace=self.stats_namespace)
            self.percentile_values[idx] = []

    def sendMetrics(self):
        last_field_name = None
        field_counts = {}
        total_count = 0
        for name_value in sorted(self.mp_stats_collector.getAllCounters(namespace=self.stats_namespace).keys()):
            field_count = self.mp_stats_collector.getCounter(name_value, namespace=self.stats_namespace)
            self.mp_stats_collector.resetCounter(name_value, namespace=self.stats_namespace)
            field_name, field_value = name_value
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
        for name_unmapped_name in self.mp_stats_collector.getAllValues(namespace=self.stats_namespace).keys():
            values = self.mp_stats_collector.getValues(name_unmapped_name, namespace=self.stats_namespace)
            self.mp_stats_collector.resetValues(name_unmapped_name, namespace=self.stats_namespace)
            name, unmapped_name = name_unmapped_name
            percentiles = self.name_to_percentiles[unmapped_name]
            try:
                percentiles = self.name_to_percentiles[unmapped_name]
            except KeyError:
                continue
            try:
                percentiles = numpy.percentile(values, percentiles).tolist()
            except IndexError:
                continue
            min = numpy.min(values)
            max = numpy.max(values)
            mean = numpy.mean(values)
            std_deviation = numpy.std(values)
            self.sendEvent(DictUtils.getDefaultEventDict({"field_name": name, "min": min, "max": max, "mean": mean, "std": std_deviation, "percentiles": percentiles, "interval": self.interval}, caller_class_name="Metrics", event_type="metrics"))


    def initAfterFork(self):
        TimedFunctionManager.startTimedFunction(self.getRunTimedFunctionsFunc())
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        for aggregation in self.aggregations:
            if self.aggregations_contain_dynamic_value:
                name = mapDynamicValue(aggregation['name'], event)
            else:
                name = aggregation['name']
            if "bins" in aggregation:
                try:
                    value = aggregation["bucket_names"][numpy.digitize(event[aggregation['field']], aggregation['bins'])]
                except KeyError:
                    continue
            else:
                try:
                    value = event[aggregation['field']]
                except KeyError:
                    continue
            self.aggregations_counter[(name, value)] += 1
        for percentile in self.percentiles:
            if self.percentiles_contain_dynamic_value:
                name = mapDynamicValue(percentile['name'], event)
            else:
                name = percentile['name']
            try:
                value = event[percentile['field']]
            except KeyError:
                continue
            self.percentile_values[(name, percentile['name'])].append(value)
        yield event

    def shutDown(self):
        self.accumulateMetrics()
        if self.lumbermill.is_master():
            self.sendMetrics()
        BaseThreadedModule.shutDown(self)