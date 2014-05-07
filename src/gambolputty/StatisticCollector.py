# -*- coding: utf-8 -*-
import threading
import multiprocessing
from collections import defaultdict
import Decorators

@Decorators.Singleton
class StatisticCollector:

    def __init__(self):
        self.lock = threading.Lock()
        self.counter_stats = defaultdict(int)
        #self.counter_stats_per_module = defaultdict(lambda: defaultdict(int))
        """ Stores the statistic data """

    def incrementCounter(self, name, increment_value=1):
        with self.lock:
            self.counter_stats[name] += increment_value
            #print "Incr %s: %s" % (name, self.counter_stats[name])

    def decrementCounter(self, name, decrement_value=1):
        with self.lock:
            self.counter_stats[name] -= decrement_value
            #print "Decr %s: %s" % (name, self.counter_stats[name])

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

@Decorators.Singleton
class MultiProcessStatisticCollector():

    def __init__(self):
        self.counter_stats = multiprocessing.Manager().dict()
        """ Stores the statistic data """

    def incrementCounter(self, name, increment_value=1):
        try:
            self.counter_stats[name] += increment_value
        except KeyError:
            self.counter_stats[name] = increment_value

    def decrementCounter(self, name, decrement_value=1):
        try:
            self.counter_stats[name] -= decrement_value
        except KeyError:
            self.counter_stats[name] = 0

    def resetCounter(self, name):
        self.counter_stats[name] = 0

    def setCounter(self, name, value):
        self.counter_stats[name] = value

    def getCounter(self, name):
        try:
            return self.counter_stats[name]
        except KeyError:
            return 0

    def getAllCounters(self):
        return self.counter_stats