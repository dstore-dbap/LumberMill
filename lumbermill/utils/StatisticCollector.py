# -*- coding: utf-8 -*-
import sys
import socket
import multiprocessing
from collections import defaultdict

from lumbermill.utils.Decorators import Singleton


@Singleton
class StatisticCollector:

    def __init__(self):
        self.max_int = sys.maxsize
        self.counter_stats = defaultdict(dict)
        #self.counter_stats_per_module = defaultdict(lambda: defaultdict(int))
        """ Stores the statistic data """

    def initCounter(self, namespace="default"):
        self.counter_stats[namespace] = defaultdict(int)

    def incrementCounter(self, key, increment_value=1, namespace="default"):
        self.counter_stats[namespace][key] += increment_value
        #print "Incr %s: %s" % (name, self.counter_stats[name])

    def decrementCounter(self, key, decrement_value=1, namespace="default"):
        self.counter_stats[namespace][key] -= decrement_value
        #print "Decr %s: %s" % (name, self.counter_stats[name])

    def resetCounter(self, key, namespace="default"):
        self.counter_stats[namespace][key] = 0

    def setCounter(self, key, value, namespace="default"):
        self.counter_stats[namespace][key] = value

    def getCounter(self, key, namespace="default"):
        return self.counter_stats[namespace][key]

    def getAllCounters(self, namespace="default"):
        return self.counter_stats[namespace]

@Singleton
class MultiProcessStatisticCollector:

    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.sync_manager = multiprocessing.Manager()
        self.counter_stats = self.sync_manager.dict()
        """ Stores the statistic data """

    def initCounter(self, namespace="default"):
        self.counter_stats[namespace] = self.sync_manager.dict()

    def incrementCounter(self, key, increment_value=1, namespace="default"):
        with self.lock:
            try:
                self.counter_stats[namespace][key] += increment_value
            except KeyError:
                self.counter_stats[namespace][key] = increment_value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except EOFError:
                # EOFError may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except socket.error as e:
                # socket.error: [Errno 2] No such file or directory may be thrown when exiting via CTRL+C. Ignore it
                etype, evalue, etb = sys.exc_info()
                if "No such file or directory" in str(evalue):
                    return 0
                else:
                    raise e

    def decrementCounter(self, key, decrement_value=1, namespace="default"):
        with self.lock:
            try:
                self.counter_stats[namespace][key] -= decrement_value
            except KeyError:
                self.counter_stats[namespace][key] = 0
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except EOFError:
                # EOFError may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except socket.error as e:
                # socket.error: [Errno 2] No such file or directory may be thrown when exiting via CTRL+C. Ignore it
                etype, evalue, etb = sys.exc_info()
                if "No such file or directory" in str(evalue):
                    return 0
                else:
                    raise e

    def resetCounter(self, key, namespace="default"):
        with self.lock:
            try:
                self.counter_stats[namespace][key] = 0
            except KeyError:
                pass
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except EOFError:
                # EOFError may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except socket.error as e:
                # socket.error: [Errno 2] No such file or directory may be thrown when exiting via CTRL+C. Ignore it
                etype, evalue, etb = sys.exc_info()
                if "No such file or directory" in str(evalue):
                    return 0
                else:
                    raise e

    def setCounter(self, key, value, namespace="default"):
        with self.lock:
            try:
                self.counter_stats[namespace][key] = value
            except KeyError:
                self.counter_stats[namespace][key] = value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except EOFError:
                # EOFError may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except socket.error as e:
                # socket.error: [Errno 2] No such file or directory may be thrown when exiting via CTRL+C. Ignore it
                etype, evalue, etb = sys.exc_info()
                if "No such file or directory" in str(evalue):
                    return 0
                else:
                    raise e

    def getCounter(self, key, namespace="default"):
        with self.lock:
            try:
                return self.counter_stats[namespace][key]
            except KeyError:
                return 0
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting via CTRL+C. Ignore it.
                return 0
            except EOFError:
                # EOFError may be thrown when exiting via CTRL+C. Ignore it.
                pass
            except socket.error as e:
                # socket.error: [Errno 2] No such file or directory may be thrown when exiting via CTRL+C. Ignore it
                etype, evalue, etb = sys.exc_info()
                if "No such file or directory" in str(evalue):
                    return 0
                else:
                    raise e

    def getAllCounters(self, namespace="default"):
        try:
            return self.counter_stats[namespace]
        except KeyError:
            return {}

    def shutDown(self):
        self.sync_manager.shutdown()
