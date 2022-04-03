# -*- coding: utf-8 -*-
import sys
import socket
import multiprocessing
from collections import defaultdict

from lumbermill.utils.Decorators import Singleton


@Singleton
class StatisticCollector:

    def __init__(self):
        self.counters = defaultdict(dict)
        """ Stores the statistic data """

    def initCounter(self, namespace="default"):
        self.counters[namespace] = defaultdict(int)

    def incrementCounter(self, key, increment_value=1, namespace="default"):
        self.counters[namespace][key] += increment_value

    def decrementCounter(self, key, decrement_value=1, namespace="default"):
        self.counters[namespace][key] -= decrement_value

    def resetCounter(self, key, namespace="default"):
        self.counters[namespace][key] = 0

    def setCounter(self, key, value, namespace="default"):
        self.counters[namespace][key] = value

    def getCounter(self, key, namespace="default"):
        return self.counters[namespace][key]

    def getAllCounters(self, namespace="default"):
        return self.counters[namespace]

@Singleton
class MultiProcessStatisticCollector:

    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.sync_manager = multiprocessing.Manager()
        self.counters = self.sync_manager.dict()
        self.values = self.sync_manager.dict()

    def initCounter(self, namespace="default"):
        self.counters[namespace] = self.sync_manager.dict()

    def incrementCounter(self, key, increment_value=1, namespace="default"):
        with self.lock:
            try:
                self.counters[namespace][key] += increment_value
            except KeyError:
                self.counters[namespace][key] = increment_value
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
                self.counters[namespace][key] -= decrement_value
            except KeyError:
                self.counters[namespace][key] = 0
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
                self.counters[namespace][key] = 0
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
                self.counters[namespace][key] = value
            except KeyError:
                self.counters[namespace][key] = value
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
                return self.counters[namespace][key]
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
            return self.counters[namespace]
        except KeyError:
            return {}

    def initValues(self, namespace="default"):
        self.values[namespace] = self.sync_manager.dict()

    def appendValues(self, key, values, namespace="default"):
        with self.lock:
            if key not in self.values[namespace].keys():
                self.values[namespace][key] = values
            else:
                self.values[namespace][key].append(values)

    def resetValues(self, key, namespace="default"):
        with self.lock:
            self.values[namespace][key] = self.sync_manager.list()

    def getValues(self, key, namespace="default"):
        try:
            return self.values[namespace][key]
        except KeyError:
            return []

    def getAllValues(self, namespace="default"):
        try:
            return self.values[namespace]
        except KeyError:
            return {}

    def shutDown(self):
        self.sync_manager.shutdown()
