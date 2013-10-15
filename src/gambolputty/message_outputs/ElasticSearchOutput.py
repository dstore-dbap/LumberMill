from hashlib import md5
import sys
import socket
import Queue
import datetime
import time
import simplejson as json
import elasticsearch
import BaseModule

class ElasticSearchOutput(BaseModule.BaseModule):

    def setup(self):
        # Call parent setup method
        super(ElasticSearchOutput, self).setup()
        # Set defaults
        self.events_container = []
        self.store_data_interval = 25
        self.store_data_idle = 1
        self.es = False

    def configure(self, configuration):
        # Call parent configure method
        super(ElasticSearchOutput, self).configure(configuration)
        if 'store_data_interval' in configuration:
            self.store_data_interval = configuration['store_data_interval']
        if 'store_data_idle' in configuration:
            self.store_data_idle = configuration['store_data_idle']
        self.es = self.connect()
        if not self.es:
            self.logger.error("No index servers configured or none could be reached.")
            self.shutDown()
            return False

    def connect(self):
        es = False
        # Connect to es nodes and round-robin between them
        if 'nodes' in self.config:
            try:
                es = elasticsearch.Elasticsearch(self.config['nodes'], sniff_on_start=True)
            except:
                es = False
        return es

    """
    StorageHandler to store SyslogMessages into an elastic search index.
    This is done via a http post request.
    """
    def run(self):
        socket.setdefaulttimeout(25)
        if not self.input_queue:
            self.logger.warning("Will not start module %s since no input queue set." % (self.__class__.__name__))
            return
        if not any (keys in self.config for keys in ['index_prefix', 'index_name']):
            self.logger.warning("Will not start module %s since no index name is set." % (self.__class__.__name__))
            return
        if "index_prefix" in self.config:
            self.logger.info("Started ElasticSearchOutput. ES-Server: %s, Index-Prefix: %s" % (self.config["nodes"], self.config["index_prefix"]))
        else:
            self.logger.info("Started ElasticSearchOutput. ES-Server: %s, Index-Name: %s" % (self.config["nodes"], self.config["index_name"]))
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
        json_data = self.dataToElasticSearchJson(index_name, self.events_container)
        try:
            self.es.bulk(body=json_data)
        except Exception, e:
            try:
                self.logger.error("Server cummunication error: %s" % e[1])
                self.logger.error("%s/%s" % (self.config["nodes"],index_name))
            except:
                self.logger.error("Server cummunication error: %s" % e)
            finally:
                self.es = self.connect()
                time.sleep(.1)
            return

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