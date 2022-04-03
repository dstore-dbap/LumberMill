# -*- coding: utf-8 -*-
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.misc import Metrics

class TestMetrics(ModuleBaseTestCase):

    def setUp(self):
        super(TestMetrics, self).setUp(Metrics.Metrics(MockLumberMill()))

    def testSimpleMetric(self):
        self.test_object.configure({'interval': 1, 'aggregations': [{'name': 'http_status_$(vhost)', 'field': 'http_status'}]})
        self.checkConfiguration()
        events = []
        for _ in range(0, 10):
            events.append(DictUtils.getDefaultEventDict({'http_status': 200, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 5):
            events.append(DictUtils.getDefaultEventDict({'http_status': 301, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 3):
            events.append(DictUtils.getDefaultEventDict({'http_status': 302, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 3):
            events.append(DictUtils.getDefaultEventDict({'http_status': 404, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 1):
            events.append(DictUtils.getDefaultEventDict({'http_status': 200, 'vhost': 'this.parrot.alive'}))
        for _ in range(0, 2):
            events.append(DictUtils.getDefaultEventDict({'http_status': 301, 'vhost': 'this.parrot.alive'}))
        for _ in range(0, 3):
            events.append(DictUtils.getDefaultEventDict({'http_status': 404, 'vhost': 'this.parrot.alive'}))
        for event in events:
            self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        metrics_event_count = 0
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] == 'metrics':
                metrics_event_count += 1
                if event['field_name'] == "http_status_this.parrot.dead":
                    self.assertEqual({200: 10, 301: 5, 302: 3, 404: 3}, event['field_counts'])
                if event['field_name'] == "http_status_this.parrot.alive":
                    self.assertEqual({200: 1, 301: 2, 404: 3}, event['field_counts'])
        self.assertEqual(2, metrics_event_count)

    def testBucketMetric(self):
        self.test_object.configure({'interval': 1, 'aggregations': [{'name': 'http_status_$(vhost)',
                                                                     'field': 'http_status',
                                                                     'buckets': [{'name': 100,
                                                                                  'upper': 199},
                                                                                 {'name': 200,
                                                                                  'upper': 299},
                                                                                 {'name': 300,
                                                                                  'upper': 399},
                                                                                 {'name': 400,
                                                                                  'upper': 499},
                                                                                 {'name': 500,
                                                                                  'upper': 599}]}]})
        self.checkConfiguration()
        events = []
        for _ in range(0, 10):
            events.append(DictUtils.getDefaultEventDict({'http_status': 202, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 5):
            events.append(DictUtils.getDefaultEventDict({'http_status': 301, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 3):
            events.append(DictUtils.getDefaultEventDict({'http_status': 302, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 3):
            events.append(DictUtils.getDefaultEventDict({'http_status': 404, 'vhost': 'this.parrot.dead'}))
        for _ in range(0, 1):
            events.append(DictUtils.getDefaultEventDict({'http_status': 202, 'vhost': 'this.parrot.alive'}))
        for _ in range(0, 2):
            events.append(DictUtils.getDefaultEventDict({'http_status': 301, 'vhost': 'this.parrot.alive'}))
        for _ in range(0, 3):
            events.append(DictUtils.getDefaultEventDict({'http_status': 404, 'vhost': 'this.parrot.alive'}))
        for event in events:
            self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        metrics_event_count = 0
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] == 'metrics':
                metrics_event_count += 1
                if event['field_name'] == "http_status_this.parrot.dead":
                    self.assertEqual({200: 10, 300: 8, 400: 3}, event['field_counts'])
                if event['field_name'] == "http_status_this.parrot.alive":
                    self.assertEqual({200: 1, 300: 2, 400: 3}, event['field_counts'])
        self.assertEqual(2, metrics_event_count)

    def testSinglePercentiles(self):
        self.test_object.configure({'interval': 1, 'percentiles': [{'name': 'request_time_$(vhost)', 'field': 'request_time', 'percentiles': [50, 75, 95, 99]}]})
        self.checkConfiguration()
        events = []
        for _ in range(10, 100, 10):
            events.append(DictUtils.getDefaultEventDict({'request_time': _, 'vhost': 'this.parrot.dead'}))
        for event in events:
            self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] == 'metrics':
                self.assertEqual(10, event['min'])
                self.assertEqual(90, event['max'])
                self.assertEqual(50.0, event['mean'])
                self.assertEqual(25.81988897471611, event['std'])
                self.assertEqual([50.0, 70.0, 86.0, 89.2], event['percentiles'])

    def testMultiplePercentiles(self):
        self.test_object.configure({'interval': 1, 'percentiles': [{'name': 'request_time_$(vhost)', 'field': 'request_time', 'percentiles': [40, 65, 95, 99]}]})
        self.checkConfiguration()
        events = []
        for _ in range(10, 100, 10):
            events.append(DictUtils.getDefaultEventDict({'request_time': _, 'vhost': 'this.parrot.dead'}))
        for _ in range(10, 100, 5):
            events.append(DictUtils.getDefaultEventDict({'request_time': _, 'vhost': 'this.parrot.alive'}))
        for event in events:
            self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        metrics_event_count = 0
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] == 'metrics':
                metrics_event_count += 1
                if event['field_name'] == "http_status_this.parrot.dead":
                    self.assertEqual(10, event['min'])
                    self.assertEqual(90, event['max'])
                    self.assertEqual(50.0, event['mean'])
                    self.assertEqual(25.81988897471611, event['std'])
                    self.assertEqual([50.0, 70.0, 86.0, 89.2], event['percentiles'])
                if event['field_name'] == "http_status_this.parrot.alive":
                    self.assertEqual(10, event['min'])
                    self.assertEqual(95, event['max'])
                    self.assertEqual(52.5, event['mean'])
                    self.assertEqual(25.940637360455632, event['std'])
                    self.assertEqual([44.0, 65.25, 90.75, 94.14999999999999], event['percentiles'])
        self.assertEqual(2, metrics_event_count)

    def testMultipleMetricsAndPercentiles(self):
        self.test_object.configure({'interval': 1,  'aggregations': [{'name': 'http_status_$(vhost)',
                                                                      'field': 'http_status',
                                                                      'buckets': [{'name': 100,
                                                                                   'upper': 199},
                                                                                  {'name': 200,
                                                                                   'upper': 299},
                                                                                  {'name': 300,
                                                                                   'upper': 399},
                                                                                  {'name': 400,
                                                                                   'upper': 499},
                                                                                  {'name': 500,
                                                                                   'upper': 599}]}],
                                                    'percentiles': [{'name': 'request_time_$(vhost)', 'field': 'request_time', 'percentiles': [40, 65, 95, 99]}]})
        self.checkConfiguration()
        events = []
        for _ in range(10, 100, 10):
            events.append(DictUtils.getDefaultEventDict({'request_time': _, 'http_status': 201, 'vhost': 'this.parrot.dead'}))
        for _ in range(10, 100, 5):
            events.append(DictUtils.getDefaultEventDict({'request_time': _, 'http_status': 404, 'vhost': 'this.parrot.alive'}))
        for event in events:
            self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        metrics_event_count = 0
        for event in self.receiver.getEvent():
            if event['lumbermill']['event_type'] == 'metrics':
                metrics_event_count += 1
                if event['field_name'] == "http_status_this.parrot.dead":
                    if 'percentiles' in event:
                        self.assertEqual(10, event['min'])
                        self.assertEqual(90, event['max'])
                        self.assertEqual(50.0, event['mean'])
                        self.assertEqual(25.81988897471611, event['std'])
                        self.assertEqual([50.0, 70.0, 86.0, 89.2], event['percentiles'])
                    elif 'field_counts' in event:
                        self.assertEqual({200: 9}, event['field_counts'])
                if event['field_name'] == "http_status_this.parrot.alive":
                    if 'percentiles' in event:
                        self.assertEqual(10, event['min'])
                        self.assertEqual(95, event['max'])
                        self.assertEqual(52.5, event['mean'])
                        self.assertEqual(25.940637360455632, event['std'])
                        self.assertEqual([44.0, 65.25, 90.75, 94.14999999999999], event['percentiles'])
                    elif 'field_counts' in event:
                        self.assertEqual({400: 18}, event['field_counts'])
        self.assertEqual(4, metrics_event_count)