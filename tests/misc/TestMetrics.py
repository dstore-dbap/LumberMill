# -*- coding: utf-8 -*-
import pprint

import lumbermill.utils.DictUtils as DictUtils
from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.misc import Metrics

class TestMetrics(ModuleBaseTestCase):

    def setUp(self):
        super(TestMetrics, self).setUp(Metrics.Metrics(MockLumberMill()))

    def testSimpleMetric(self):
        self.test_object.configure({'interval': 1, 'aggregations': [{'key': 'http_status_$(vhost)', 'value': 'http_status'}]})
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
        self.test_object.configure({'interval': 1, 'aggregations': [{'key': 'http_status_$(vhost)',
                                                                     'value': 'http_status',
                                                                     'buckets': [{'key': 100,
                                                                                  'upper': 199},
                                                                                 {'key': 200,
                                                                                  'upper': 299},
                                                                                 {'key': 300,
                                                                                  'upper': 399},
                                                                                 {'key': 400,
                                                                                  'upper': 499},
                                                                                 {'key': 500,
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