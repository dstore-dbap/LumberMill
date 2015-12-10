# -*- coding: utf-8 -*-
import multiprocessing
from collections import defaultdict
import Decorators


@Decorators.Singleton
class StatisticCollector:

    def __init__(self):
        self.counter_stats = defaultdict(int)
        #self.counter_stats_per_module = defaultdict(lambda: defaultdict(int))
        """ Stores the statistic data """

    def incrementCounter(self, name, increment_value=1):
        self.counter_stats[name] += increment_value
        #print "Incr %s: %s" % (name, self.counter_stats[name])

    def decrementCounter(self, name, decrement_value=1):
        self.counter_stats[name] -= decrement_value
        #print "Decr %s: %s" % (name, self.counter_stats[name])

    def resetCounter(self,name):
        self.counter_stats[name] = 0

    def setCounter(self, name, value):
        self.counter_stats[name] = value

    def getCounter(self, name):
        return self.counter_stats[name]

    def getAllCounters(self):
        return self.counter_stats

@Decorators.Singleton
class MultiProcessStatisticCollector:

    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.sync_manager = multiprocessing.Manager()
        self.counter_stats = self.sync_manager.dict()
        """ Stores the statistic data """

    def incrementCounter(self, name, increment_value=1):
        with self.lock:
            try:
                self.counter_stats[name] += increment_value
            except KeyError:
                self.counter_stats[name] = increment_value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                pass

    def decrementCounter(self, name, decrement_value=1):
        with self.lock:
            try:
                self.counter_stats[name] -= decrement_value
            except KeyError:
                self.counter_stats[name] = 0
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                pass

    def resetCounter(self,name):
        with self.lock:
            try:
                self.counter_stats[name] = 0
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                pass

    def setCounter(self, name, value):
        with self.lock:
            try:
                self.counter_stats[name] = value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                pass

    def getCounter(self, name):
        with self.lock:
            try:
                return self.counter_stats[name]
            except KeyError:
                return 0
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                return 0

    def getAllCounters(self):
        return self.counter_stats

    def shutDown(self):
        self.sync_manager.shutdown()