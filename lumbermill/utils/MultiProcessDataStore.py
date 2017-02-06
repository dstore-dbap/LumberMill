# -*- coding: utf-8 -*-
import multiprocessing
from lumbermill.utils import Decorators


@Decorators.Singleton
class MultiProcessDataStore:

    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.sync_manager = multiprocessing.Manager()
        self.data_dict = self.sync_manager.dict()
        """ Stores the statistic data """

    def acquireLock(self):
        self.lock.acquire()

    def releaseLock(self):
        self.lock.release()

    def setValue(self, key, value):
        with self.lock:
            try:
                self.data_dict[key] = value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                pass

    def getValue(self, key, value):
        with self.lock:
            try:
                self.data_dict[key] = value
            except OSError:
                # OSError: [Errno 32] Broken pipe may be thrown when exiting lumbermill via CTRL+C. Ignore it
                pass

    def getDataDict(self):
        return self.data_dict

    def shutDown(self):
        self.sync_manager.shutdown()