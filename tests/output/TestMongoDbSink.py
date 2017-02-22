import datetime
import mock
import pymongo
import sys
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.output import MongoDbSink


class TestMongoDbSink(ModuleBaseTestCase):

    def setUp(self):
        super(TestMongoDbSink, self).setUp(MongoDbSink.MongoDbSink(mock.Mock()))
        self.mongodb_server = 'localhost:27017'
        self.mongodb = self.connect()

    def connect(self):
        try:
            mongodb_client = pymongo.MongoClient(self.mongodb_server, serverSelectionTimeoutMS=3)
            self.logger.debug(str(mongodb_client.server_info()))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Connection to %s failed. Exception: %s, Error: %s." % (self.mongodb_server, etype, evalue))
        if not mongodb_client:
            self.logger.error("Connection to %s failed. Shutting down." % self.mongodb_server)
            self.tearDown()
        else:
            self.logger.debug("Connection to %s successful." % self.mongodb_server)
        return mongodb_client

    def testDefaultDatabaseAndDefaultCollection(self):
        self.test_object.configure({'host': self.mongodb_server,
                                    'optinonal_connection_params': {'serverSelectionTimeoutMS': 1}})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        timestring = datetime.datetime.utcnow().strftime('%Y.%m.%d')
        collection_name = 'lumbermill-%s' % timestring
        database_name = self.test_object.getConfigurationValue('database')
        event = DictUtils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered."})
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        result = self.mongodb[database_name][collection_name].find_one({'_id': event['lumbermill']['event_id']})
        self.assertEqual(type(result), dict)
        self.assertEqual(result['McTeagle'], "But it was with more simple, homespun verses that McTeagle's unique style first flowered.")
        self.mongodb.drop_database(database_name)

    def testCustomDatabaseAndCustomCollection(self):
        self.test_object.configure({'host': self.mongodb_server,
                                    'database': 'my_test_database',
                                    'collection': 'lumbermill-$(target_collection)',
                                    'optinonal_connection_params': {'serverSelectionTimeoutMS': 1}})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        collection_name = 'lumbermill-mcteagles'
        database_name = self.test_object.getConfigurationValue('database')
        event = DictUtils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered.",
                                               'target_collection': 'mcteagles'})
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        result = self.mongodb[database_name][collection_name].find_one({'_id': event['lumbermill']['event_id']})
        self.assertEqual(type(result), dict)
        self.assertEqual(result['McTeagle'], "But it was with more simple, homespun verses that McTeagle's unique style first flowered.")
        self.mongodb.drop_database(database_name)

    def testCustomDocId(self):
        self.test_object.configure({'host': self.mongodb_server,
                                    'doc_id': '$(event_doc_id)',
                                    'optinonal_connection_params': {'serverSelectionTimeoutMS': 1}})
        self.checkConfiguration()
        self.test_object.initAfterFork()
        timestring = datetime.datetime.utcnow().strftime('%Y.%m.%d')
        collection_name = 'lumbermill-%s' % timestring
        database_name = self.test_object.getConfigurationValue('database')
        event = DictUtils.getDefaultEventDict({'McTeagle': "But it was with more simple, homespun verses that McTeagle's unique style first flowered.",
                                               'event_doc_id': 'Ewan'})
        self.test_object.receiveEvent(event)
        self.test_object.shutDown()
        result = self.mongodb[database_name][collection_name].find_one({'_id': event['event_doc_id']})
        self.assertEqual(type(result), dict)
        self.assertEqual(result['McTeagle'], "But it was with more simple, homespun verses that McTeagle's unique style first flowered.")
        self.mongodb.drop_database(database_name)
