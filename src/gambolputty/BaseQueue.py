# -*- coding: utf-8 -*-
import Queue
import StatisticCollector

class BaseQueue(Queue.Queue):

    def __init__(self, maxsize=0):
        Queue.Queue.__init__(self, maxsize)

    def put(self, item, block=True, timeout=None, filter=False):
        Queue.Queue.put(self, item, block, timeout)

    def get(self, block=True, timeout=None):
        item = Queue.Queue.get(self, block, timeout)
        #self.task_done()
        return item
