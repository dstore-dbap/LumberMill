import time
import mock

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.misc import Cache


class TestCache(ModuleBaseTestCase):

    key = 'Gambol'

    def setUp(self):
        super(TestCache, self).setUp(Cache.Cache(mock.Mock()))
        try:
            self.test_object.kv_store.delete(self.key)
        except AttributeError:
            pass

    def testSimpleValue(self):
        self.test_object.configure({})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value)
        self.assertEquals(value, self.test_object.get(self.key))

    def testPickledValue(self):
        self.test_object.configure({})
        self.checkConfiguration()
        value = {'Putty': {'Composer': True}}
        self.test_object.set(self.key, value)
        self.assertEquals(value, self.test_object.get(self.key))

    def testDeleteValue(self):
        self.test_object.configure({})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value)
        self.assertEquals(value, self.test_object.get(self.key))
        self.test_object.delete(self.key)
        self.assertRaises(KeyError, self.test_object.get, self.key)

    def testRedisBackendSimpleValue(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost'})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value)
        self.assertEquals(value, self.test_object.get(self.key))

    def testRedisBackendPickledValue(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost'})
        self.checkConfiguration()
        value = {'Putty': {'Composer': True}}
        self.test_object.set(self.key, value)
        self.assertEquals(value, self.test_object.get(self.key))

    def testRedisBackendTtlValue(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost'})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value, ttl=1)
        self.assertEquals(value, self.test_object.get(self.key))
        time.sleep(1)
        self.assertRaises(KeyError, self.test_object.get, self.key)

    def testRedisClusterBackendSimpleValue(self):
        try:
            import rediscluster
        except ImportError:
            self.skipTest("Could not test redis cluster client. Module rediscluster not installed.")
            return
        self.test_object.configure({'backend': 'RedisStore',
                                    'cluster': {'localhost': {'localhost'}}})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value)
        self.assertEquals(value, self.test_object.get(self.key))

    def testBufferWithBatchSize(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost',
                                    'batch_size': 10,
                                    'store_interval_in_secs': 60})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value)
        # Getting directly from backend should fail, since batch size is not yet reached.
        self.assertRaises(KeyError, self.test_object.kv_store.get, self.key)
        # Getting directly from kv store should succeed.
        self.assertEquals(value, self.test_object.get(self.key))
        # Trigger batch size.
        for _ in xrange(0, 15):
            self.test_object.set(self.key, value)
        # Getting from backend should now succeed.
        value_in_backend = None
        try:
            value_in_backend = self.test_object.kv_store.get(self.key)
        except:
            pass
        self.assertIsNotNone(value_in_backend)
        self.assertEquals(value, self.test_object.get(self.key))

    def testBufferWithInterval(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost',
                                    'batch_size': 50,
                                    'store_interval_in_secs': 1})
        self.checkConfiguration()
        value = 'Putty'
        self.test_object.set(self.key, value)
        # Getting from backend should fail, since interval is not yet reached.
        self.assertRaises(KeyError, self.test_object.kv_store.get, self.key)
        # Wait for interval.
        time.sleep(1)
        # Getting from backend should now succeed.
        value_in_backend = None
        try:
            value_in_backend = self.test_object.kv_store.get(self.key)
        except:
           pass
        self.assertIsNotNone(value_in_backend)
        self.assertEquals(value, self.test_object.get(self.key))

    def tearDown(self):
        ModuleBaseTestCase.tearDown(self)
        try:
            self.test_object.kv_store.delete(self.key)
        except AttributeError:
            pass