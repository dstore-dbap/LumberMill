# -*- coding: utf-8 -*-
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.misc import Throttle


class TestThrottle(ModuleBaseTestCase):

    def setUp(self):
        super(TestThrottle, self).setUp(Throttle.Throttle(MockLumberMill()))

    def testMinCount(self):
        self.test_object.configure({'key': '$(Spam)',
                                    'timeframe': 1,
                                    'min_count': 5,
                                    'max_count': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        for _ in range(1, 6):
            self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'Spam': 'Spam'}))
        event_counter = 0
        for _ in self.receiver.getEvent():
            event_counter += 1
        self.assertEqual(event_counter, 1)

    def testMinCountNotReached(self):
        self.test_object.configure({'key': '$(Spam)',
                                    'timeframe': 1,
                                    'min_count': 5,
                                    'max_count': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'Spam': 'Spam'}))
        got_event = False
        for _ in self.receiver.getEvent():
            got_event = True
        self.assertFalse(got_event)

    def testMaxCount(self):
        self.test_object.configure({'key': '$(Spam)',
                                    'timeframe': 1,
                                    'min_count': 1,
                                    'max_count': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        for _ in range(1, 20):
            self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'Spam': 'Spam'}))
        event_counter = False
        for _ in self.receiver.getEvent():
            event_counter += 1
        self.assertEqual(event_counter, 10)

    def testMaxCountNotReached(self):
        self.test_object.configure({'key': '$(Spam)',
                                    'timeframe': 1,
                                    'min_count': 1,
                                    'max_count': 10})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        for _ in range(0, 6):
            self.test_object.receiveEvent(DictUtils.getDefaultEventDict({'Spam': 'Spam'}))
        event_counter = 0
        for _ in self.receiver.getEvent():
            event_counter += 1
        self.assertEqual(event_counter, 6)