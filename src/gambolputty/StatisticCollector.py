# -*- coding: utf-8 -*-
import threading
from collections import defaultdict
import Decorators
import inspect

@Decorators.Singleton
class StatisticCollector:

    def __init__(self):
        self.lock = threading.Lock()
        self.counter_stats = defaultdict(int)
        self.counter_stats_per_module = defaultdict(lambda: defaultdict(int))
        """ Stores the statistic data """

    def incrementCounter(self, name, increment_value=1):
        frame = inspect.currentframe(1)
        caller = frame.f_locals.get('self', None)
        with self.lock:
            self.counter_stats[name] += increment_value
            self.counter_stats_per_module[caller.__class__.__name__][name] += increment_value
            #print "%s increments %s to %s." % (caller.__class__.__name__, name, self.counter_stats[name])

    def decrementCounter(self, name, decrement_value=1):
        frame = inspect.currentframe(1)
        caller = frame.f_locals.get('self', None)
        with self.lock:
            self.counter_stats[name] -= decrement_value
            self.counter_stats_per_module[caller.__class__.__name__][name] -= decrement_value
            #print "%s decrements %s to %s." % (caller.__class__.__name__, name, self.counter_stats[name])

    def resetCounter(self,name):
        with self.lock:
            self.counter_stats[name] = 0

    def setCounter(self, name, value):
        with self.lock:
            self.counter_stats[name] = value

    def getCounter(self, name):
        with self.lock:
            return self.counter_stats[name]

    def getAllCounters(self):
        return self.counter_stats