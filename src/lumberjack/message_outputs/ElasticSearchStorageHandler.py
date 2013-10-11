import sys
import httplib
import socket
import time
import datetime
import threading
import traceback
import Queue
import simplejson as json
import BaseModule
from hashlib import md5

class ElasticSearchStorageHandler(BaseModule.BaseModule):

    def setup(self):
        # Call parent setup method
        super(ElasticSearchStorageHandler, self).setup()
        # Set defaults
        self.events_container = []
        self.store_data_interval = 25
        self.store_data_idle = 1

    def configure(self, configuration):
        # Call parent configure method
        super(ElasticSearchStorageHandler, self).configure(configuration)
        if 'store_data_interval' in configuration:
            self.store_data_interval = configuration['store_data_interval']
        if 'store_data_idle' in configuration:
            self.store_data_idle = configuration['store_data_idle']

    """
    StorageHandler to store SyslogMessages into an elastic search index.
    This is done via a http post request.
    """
    def run(self):
        socket.setdefaulttimeout(25)
        self.restService = httplib.HTTP(self.config["host"])
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        if not any (keys in self.config for keys in ['index_prefix', 'index_name']):
            self.logger.warning("Will not start module %s since no index name is set." % (self.__class__.__name__))
            return
        if "index_prefix" in self.config:
            self.logger.info("Started ElasticSearchStorageHandler. ES-Server: %s, Index-Prefix: %s" % (self.config["host"], self.config["index_prefix"]))
        else:
            self.logger.info("Started ElasticSearchStorageHandler. ES-Server: %s, Index-Name: %s" % (self.config["host"], self.config["index_name"]))
        while self.is_alive:
            try:
                data = self.input_queue.get(timeout=self.store_data_idle)
                self.decrementQueueCounter()
                self.handleData(data)
                self.input_queue.task_done()
            except Queue.Empty:
                if len(self.events_container) > 0:
                    self.storeData()
                    self.events_container = []
                pass
            except Exception, e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.logger.error("Could not read data from input queue." )
                traceback.print_exception(exc_type, exc_value, exc_tb)
                time.sleep(.5)
            if self.output_queues and data:
                self.addToOutputQueues(data)

    def handleData(self, data):
        """Store data in elasticsearch index
        After some testing it turned out that using httplib is less cpu intensive than pyes.
        There this approach.
        """
        # Append event to internal data container
        self.events_container.append(data)
        if len(self.events_container) < self.config['store_data_interval']:
            return
        self.storeData()
        self.events_container = []

    def storeData(self):
        if "index_prefix" in self.config:
            index_name = "%s%s" % (self.config["index_prefix"], datetime.date.today().strftime('%Y.%m.%d'))
        else:
            index_name = self.config["index_name"]
        bulk_update_url = index_name+"/_bulk"
        json_data = self.dataToElasticSearchJson(index_name, self.events_container)
        try:
            self.logger.debug("(ThreadID: %s): Sending json data to server: %s. URL: %s" % (threading.current_thread(), self.config["host"], bulk_update_url));
            self.restService.putrequest("POST", bulk_update_url)
            self.restService.putheader("User-Agent", "Python post")
            self.restService.putheader("Content-type", "application/json;") #charset=\"UTF-8\"
            self.restService.putheader("Content-length", "%d" % len(json_data))
            self.restService.endheaders()
            self.restService.send(json_data)
        except Exception, e:
            try:
                self.logger.error("Server cummunication error: %s" % e[1])
                self.logger.error("%s/%s" % (self.config["host"],index_name))
            except:
                self.logger.error("Server cummunication error: %s" % e)
            finally:
                self.restService = None
                self.restService = httplib.HTTP(self.config["host"])
                time.sleep(.1)
            return
        # Get the response
        try:
            http_statuscode, statusmessage, header = self.restService.getreply()
            response_string = self.restService.getfile().read()
            self.logger.debug("Server said: HttpStatus: %s. Response: %s" % (http_statuscode,response_string));
        except Exception, e:
            try:
                self.logger.error("Server cummunication error: %s" % e[1])
            except:
                self.logger.error("Server cummunication error: %s" % e)
            return
        # Check status code
        if(http_statuscode != 200):
            self.logger.error("Server returncode: %s. Error: %s" % (http_statuscode,response_string))
            self.logger.error("JSON Data: %s" % json_data)
            return
        self.logger.debug("Successfully send data: %s" % json_data)

    def dataToElasticSearchJson(self, index_name, data):
        """
        Format data for elasticsearch bulk update
        """
        json_data = ""
        for datarow in data:
            es_index = '{"index": {"_index": "%s", "_type": "%s", "_id": "%s"}}\n' % (index_name, datarow['message_type'], md5(datarow['data']).hexdigest())
            # Cast fields to datatype as defined in config.
            if 'field_types' in self.config:
                for field_name, data_type in self.config['field_types'].items():
                    try:
                        {'Integer': lambda field_name: datarow.__setitem__(field_name, int(datarow[field_name])),
                         'String': lambda field_name: datarow.__setitem__(field_name, str(datarow[field_name])),
                         'Float': lambda field_name: datarow.__setitem__(field_name, float(datarow[field_name])),
                         'Boolean': lambda field_name: datarow.__setitem__(field_name, bool(datarow[field_name]))}[data_type](field_name)
                    except Exception, e:
                        pass
            try:
                json_data += "%s%s\n" % (es_index,json.dumps(datarow))
            except UnicodeDecodeError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Could not  json encode %s. Exception: %s, Error: %s." % (datarow, etype, evalue))
        return json_data