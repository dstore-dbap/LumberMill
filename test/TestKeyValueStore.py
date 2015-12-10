import time
import ModuleBaseTestCase
import mock

from lumbermill.misc import KeyValueStore


class TestKeyValueStore(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestKeyValueStore, self).setUp(KeyValueStore.KeyValueStore(mock.Mock()))

    def testSimpleValue(self):
        self.test_object.configure({})
        self.checkConfiguration()
        key = 'Gambol'
        value = 'Putty'
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))

    def testPickledValue(self):
        self.test_object.configure({})
        self.checkConfiguration()
        key = 'Gambol'
        value = {'Putty': {'Composer': True}}
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))

    def testDeleteValue(self):
        self.test_object.configure({})
        self.checkConfiguration()
        key = 'Gambol'
        value = 'Putty'
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))
        self.test_object.delete(key)
        self.assertRaises(KeyError, self.test_object.get, key)

    def testRedisBackendSimpleValue(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost'})
        self.checkConfiguration()
        key = 'Gambol'
        value = 'Putty'
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))

    def testRedisBackendPickledValue(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost'})
        self.checkConfiguration()
        key = 'Gambol'
        value = {'Putty': {'Composer': True}}
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))

    def testRedisBackendTtlValue(self):
        self.test_object.configure({'backend': 'RedisStore',
                                    'server': 'localhost'})
        self.checkConfiguration()
        key = 'Gambol'
        value = 'Putty'
        self.test_object.set(key, value, ttl=1)
        self.assertEquals(value, self.test_object.get(key))
        time.sleep(1)
        self.assertRaises(KeyError, self.test_object.get, key)

    def testRedisClusterBackendSimpleValue(self):
        try:
            import rediscluster
        except ImportError:
            self.skipTest("Could not test redis cluster client. Module rediscluster not installed.")
            return
        self.test_object.configure({'backend': 'RedisStore',
                                    'cluster': {'localhost': {'localhost'}}})
        self.checkConfiguration()
        key = 'Gambol'
        value = 'Putty'
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))