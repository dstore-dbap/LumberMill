import time
import extendSysPath
import ModuleBaseTestCase
import mock
import Utils
import KeyValueStore

class TestKeyValueStore(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestKeyValueStore, self).setUp(KeyValueStore.KeyValueStore(gp=mock.Mock()))

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
        self.skipTest("Not yet correctly implemented.")
        self.test_object.configure({'backend': 'RedisStore',
                                    'cluster': {'localhost': 'es-01.dbap.de'}})
        self.checkConfiguration()
        key = 'Gambol'
        value = 'Putty'
        self.test_object.set(key, value)
        self.assertEquals(value, self.test_object.get(key))