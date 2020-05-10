# -*- coding: utf-8 -*-
import os
import sys
import time
import socket
import psutil
import datetime
from collections import defaultdict

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser, setInterval
from lumbermill.utils.StatisticCollector import StatisticCollector, MultiProcessStatisticCollector
from lumbermill.utils.misc import AnsiColors, TimedFunctionManager


@ModuleDocstringParser
class SimpleStats(BaseThreadedModule):
    """
    Collect and log some simple statistic data.

    Use this module if you just need some simple statistics on how many events are passing through 
    Per default, statistics will just be send to stdout.

    As a side note: This module inits MultiProcessStatisticCollector. As it uses multiprocessing.Manager().dict()
    this will start another process. So if you use SimpleStats, you will see workers + 1 processes in the process
    list.

    For possible values for process_statistics see: https://code.google.com/archive/p/psutil/wikis/Documentation.wiki#CPU

    Configuration template:

    - SimpleStats:
       interval:                        # <default: 10; type: integer; is: optional>
       event_type_statistics:           # <default: True; type: boolean; is: optional>
       receive_rate_statistics:         # <default: True; type: boolean; is: optional>
       waiting_event_statistics:        # <default: False; type: boolean; is: optional>
       process_statistics:              # <default: ['cpu_percent','memory_percent']; type: boolean||list; is: optional>
       emit_as_event:                   # <default: False; type: boolean; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.emit_as_event = self.getConfigurationValue('emit_as_event')
        self.interval = self.getConfigurationValue('interval')
        self.event_type_statistics = self.getConfigurationValue('event_type_statistics')
        self.process_statistics = self.getConfigurationValue('process_statistics')
        self.stats_collector = StatisticCollector()
        self.mp_stats_collector = MultiProcessStatisticCollector()
        self.module_queues = {}
        self.psutil_processes = []
        self.last_values = {'events_received': 0}
        self.methods = dir(self)

    def getRunTimedFunctionsFunc(self):
        @setInterval(self.interval)
        def evaluateStats():
            self.accumulateReceiveRateStats()
            self.accumulateEventTypeStats()
            if self.lumbermill.is_master():
                self.printIntervalStatistics()
        return evaluateStats

    def accumulateEventTypeStats(self):
        for event_type, count in self.stats_collector.getAllCounters().items():
            if count == 0:
                continue
            self.mp_stats_collector.incrementCounter(event_type, count)
            self.stats_collector.resetCounter(event_type)

    def accumulateReceiveRateStats(self):
        if self.stats_collector.getCounter('events_received') == 0:
            return
        self.mp_stats_collector.incrementCounter('events_received', self.stats_collector.getCounter('events_received'))
        self.stats_collector.resetCounter('events_received')

    def printIntervalStatistics(self):
        self.logger.info("############# Statistics (PID: %s) #############" % os.getpid())
        if self.getConfigurationValue('receive_rate_statistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('event_type_statistics'):
            self.eventTypeStatistics()
        if self.getConfigurationValue('waiting_event_statistics'):
            self.eventsInQueuesStatistics()
        if self.getConfigurationValue('process_statistics'):
            self.processStatistics()

    def receiveRateStatistics(self):
        self.logger.info(">> Receive rate stats")
        events_received = self.mp_stats_collector.getCounter('events_received')
        # If LumberMill is shutting down and running with multiple processes, we might end up with an empty return value.
        if not events_received:
            return
        self.logger.info("Received events in %ss: %s%s (%s/eps)%s" % (self.getConfigurationValue('interval'), AnsiColors.YELLOW, events_received, (events_received/self.interval), AnsiColors.ENDC))
        if self.emit_as_event:
            self.sendEvent(DictUtils.getDefaultEventDict({"stats_type": "receiverate_stats", "receiverate_count": events_received, "receiverate_count_per_sec": int((events_received/self.interval)), "interval": self.interval, "timestamp": time.time()}, caller_class_name="Statistics", event_type="statistic"))
        self.mp_stats_collector.setCounter('last_events_received', events_received)
        self.mp_stats_collector.resetCounter('events_received')

    def eventTypeStatistics(self):
        self.logger.info(">> EventTypes Statistics")
        try:
            for event_type in sorted(self.mp_stats_collector.getAllCounters().keys()):
                if not event_type.startswith('event_type_'):
                    continue
                count = self.mp_stats_collector.getCounter(event_type)
                event_name = event_type.replace('event_type_', '').lower()
                self.logger.info("EventType: %s%s%s - Hits: %s%s%s" % (AnsiColors.YELLOW, event_name, AnsiColors.ENDC, AnsiColors.YELLOW, count, AnsiColors.ENDC))
                if self.emit_as_event:
                    self.sendEvent(DictUtils.getDefaultEventDict({"stats_type": "event_type_stats", "%s_count" % event_name: count, "%s_count_per_sec" % event_name:int((count/self.interval)), "interval": self.interval, "timestamp": time.time()}, caller_class_name="Statistics", event_type="statistic"))
                self.mp_stats_collector.setCounter("last_%s" % event_type, count)
                self.mp_stats_collector.resetCounter(event_type)
        except BrokenPipeError:
            # BrokenPipeError  may be thrown when exiting via CTRL+C. Ignore it.
            pass
        except socket.error as e:
            # socket.error: [Errno 2] No such file or directory may be thrown when exiting via CTRL+C. Ignore it.
            etype, evalue, etb = sys.exc_info()
            if "No such file or directory" in str(evalue):
                pass
            else:
                raise e

    def eventsInQueuesStatistics(self):
        if len(self.module_queues) == 0:
            return
        self.logger.info(">> Queue stats")
        for module_name, queue in sorted(self.module_queues.items()):
            try:
                self.logger.info("Events in %s queue: %s%s%s" % (module_name, AnsiColors.YELLOW, queue.qsize(), AnsiColors.ENDC))
            except NotImplementedError:
                self.logger.info("Getting queue size of multiprocessed queues is not implemented for this platform.")
                return
            if self.emit_as_event:
                self.sendEvent(DictUtils.getDefaultEventDict({"stats_type": "queue_stats", "count": queue.qsize(), "interval": self.interval, "timestamp": time.time()}, caller_class_name="Statistics", event_type="statistic"))

    def processStatistics(self):
        stats_event = {"stats_type": "process_stats", "timestamp": time.time()}
        stats_event["worker_count"] = len(self.lumbermill.child_processes) + 1
        stats_event["uptime"] = int(time.time() - self.psutil_processes[0].create_time())
        self.logger.info(">> Process stats")
        self.logger.info("num workers: %d" % (len(self.lumbermill.child_processes)+1))
        self.logger.info("started: %s" % datetime.datetime.fromtimestamp(self.psutil_processes[0].create_time()).strftime("%Y-%m-%d %H:%M:%S"))
        aggregated_metrics = defaultdict(int)
        for psutil_process in self.psutil_processes:
            stats_event["pid"] = psutil_process.pid
            for metric_name, metric_value in psutil_process.as_dict(self.process_statistics).items():
                # Call metric specific method if it exists.
                if "convertMetric_%s" % metric_name in self.methods:
                    metric_name, metric_value = getattr(self, "convertMetric_%s" % self.action)(metric_name, metric_value)
                try:
                    aggregated_metrics[metric_name] += metric_value
                except TypeError:
                    try:
                        metric_value = dict(metric_value.__dict__)
                    except:
                        pass
                    try:
                        stats_event[metric_name].append(metric_value)
                    except KeyError:
                        stats_event[metric_name] = [metric_value]
                    self.logger.info("%s(pid: %s): %s" % (metric_name, psutil_process.pid, metric_value))
            if self.emit_as_event:
                self.sendEvent(DictUtils.getDefaultEventDict(stats_event, caller_class_name="Statistics", event_type="statistic"))
        for agg_metric_name, agg_metric_value in aggregated_metrics.items():
            self.logger.info("%s: %s" % (agg_metric_name, agg_metric_value))
        if self.emit_as_event:
            self.sendEvent(DictUtils.getDefaultEventDict(aggregated_metrics, caller_class_name="Statistics", event_type="statistic"))

    def getLastReceiveCount(self):
        try:
            received_counter = self.mp_stats_collector.getCounter('last_events_received')
        except KeyError:
            received_counter = 0
        return received_counter

    def getLastEventTypeCounter(self):
        event_type_counter = {}
        for event_type in sorted(self.mp_stats_collector.getAllCounters().keys()):
            if not event_type.startswith('last_event_type_'):
                continue
            count = self.mp_stats_collector.getCounter(event_type)
            event_name = event_type.replace('last_event_type_', '').lower()
            event_type_counter[event_name] = count
        return event_type_counter

    def getEventsInQueuesCounter(self):
        event_queue_counter = {}
        for module_name, queue in sorted(self.module_queues.items()):
            try:
                event_queue_counter[module_name] = queue.qsize()
            except NotImplementedError:
                self.logger.debug("Getting queue size of multiprocessed queues is not implemented for this platform.")
                continue
        return event_queue_counter

    def initAfterFork(self):
        # Get all configured queues for waiting event stats.
        self.module_queues = self.lumbermill.getAllQueues()
        self.psutil_processes.append(psutil.Process(self.lumbermill.getMainProcessId()))
        for worker in self.lumbermill.child_processes:
            self.psutil_processes.append(psutil.Process(worker.pid))
        TimedFunctionManager.startTimedFunction(self.getRunTimedFunctionsFunc())
        BaseThreadedModule.initAfterFork(self)

    def handleEvent(self, event):
        self.stats_collector.incrementCounter('events_received')
        if self.event_type_statistics:
            try:
                self.stats_collector.incrementCounter('event_type_%s' % event['lumbermill']['event_type'])
            except:
                pass
        yield event

    def shutDown(self):
        self.accumulateReceiveRateStats()
        self.accumulateEventTypeStats()
        if self.lumbermill.is_master():
            self.printIntervalStatistics()
        self.mp_stats_collector.shutDown()
        BaseThreadedModule.shutDown(self)
