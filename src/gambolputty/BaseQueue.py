# -*- coding: utf-8 -*-
import logging
import threading
import Queue
import StatisticCollector

class BaseQueue(Queue.Queue):

    messages_in_queues = 0
    """ Stores number of messages in all queues. """

    lock = threading.Lock()
    """ Class wide access to locking. """

    def __init__(self, maxsize=0):
        Queue.Queue.__init__(self, maxsize)
        self.logger = logging.getLogger(self.__class__.__name__)

    def put(self, item, block=True, timeout=None, filter=False):
        StatisticCollector.StatisticCollector().incrementCounter('events_in_queues')
        Queue.Queue.put(self, item, block=True, timeout=None)

    def get(self, block=True, timeout=None):
        item = Queue.Queue.get(self, block, timeout)
        StatisticCollector.StatisticCollector().decrementCounter('events_in_queues')
        return item
