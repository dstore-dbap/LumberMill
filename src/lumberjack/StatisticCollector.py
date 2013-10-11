import threading
import lumberjack.Decorators as Decorators

@Decorators.singleton
class StatisticCollector:
    """ Stores the statistic data """
    statistic_data = {}

    def __init__(self):
        self.lock = threading.Lock()
    
    def incrementCounter(self, name, increment_value=1):
        self.lock.acquire()
        try:
            self.statistic_data[name] += increment_value
        except:
            self.statistic_data[name] = increment_value
        finally:
            self.lock.release()
        return self.statistic_data[name]
            
    def resetCounter(self,name):
        self.lock.acquire()
        try:
            self.statistic_data[name] = None
        except: 
            pass
        finally:
            self.lock.release()

    def setCounter(self, name, value):
        self.lock.acquire()        
        self.statistic_data[name] = value
        self.lock.release()
        
    def getCounter(self, name):
        self.lock.acquire()
        try: 
            return self.statistic_data[name]
        except:
            pass        
        finally:
            self.lock.release()
  
    def getAllCounters(self):
        self.lock.acquire()
        try: 
            return self.statistic_data
        except:
            pass        
        finally:
            self.lock.release()
  
    def getDict(self, name):
        self.lock.acquire()
        if name not in self.statistic_data:
            self.statistic_data[name] = {}
        self.lock.release()
        return self.statistic_data[name]
        
    def resetDict(self, name):
        self.lock.acquire()
        self.statistic_data[name] = {}
        self.lock.release()