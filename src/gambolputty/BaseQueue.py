# -*- coding: utf-8 -*-
import sys
import logging
import threading
import Queue

class BaseQueue(Queue.Queue):

    messages_in_queues = 0
    """ Stores number of messages in all queues. """

    lock = threading.Lock()
    """ Class wide access to locking. """

    @staticmethod
    def incrementQueueCounter():
        """
        Static method to keep track of how many events are en-route in queues.
        """
        BaseQueue.lock.acquire()
        BaseQueue.messages_in_queues += 1
        BaseQueue.lock.release()

    @staticmethod
    def decrementQueueCounter():
        """
        Static method to keep track of how many events are en-route in queues.
        """
        BaseQueue.lock.acquire()
        BaseQueue.messages_in_queues -= 1
        BaseQueue.lock.release()

    def __init__(self, maxsize=0):
        Queue.Queue.__init__(self, maxsize)
        self.logger = logging.getLogger(self.__class__.__name__)

    def put(self, item, block=True, timeout=None, filter=False):
        self.incrementQueueCounter()
        Queue.Queue.put(self, item, block=True, timeout=None)

    def get(self, block=True, timeout=None):
        item = Queue.Queue.get(self, block, timeout)
        self.decrementQueueCounter()
        return item
