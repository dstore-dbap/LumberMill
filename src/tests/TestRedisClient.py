# -*- coding: utf-8 -*-
import extendSysPath
import ModuleBaseTestCase
import unittest2
import mock
import Utils
import RedisClient

class TestRedisClient(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestRedisClient, self).setUp(RedisClient.RedisClient(gp=mock.Mock()))

    def testGetClient(self):
        self.test_object.configure({'server': 'es-01.dbap.de'})
        rc = self.test_object.getClient()
        self.assertEqual(rc.__class__.__name__, 'StrictRedis')

    def testSetGetValue(self):
        self.test_object.configure({'server': 'es-01.dbap.de'})
        value = 'de-von-Ausfern-schplenden-schlitter-crass-cren-bon-fried-digger-dingle-dangle-dongle-dungle-burstein-von-knacker-thrasher-apple-banger-horowitz-ticolensic-grander-knotty-spelltinkle-grandlich-grumblemeyer-spelter-wasser-kurstlich-himble-eisen-bahnwagen-guten-abend-bitte-ein-nürnburger-bratwürstel-gespurten-mitz-weimache-luber-hundsfut-gumberaber-schönendanker-kalbsfleisch-mittleraucher-von-Hautkopft of Ulm'
        rc = self.test_object.getClient()
        rc.setex('Johann Gambolputty', 10, value)
        test = rc.get('Johann Gambolputty')
        self.assertEquals(test, value)

    @unittest2.skip("Skipping testQueueCommunication.")
    def testQueueCommunication(self):
        super(TestRedisClient, self).testQueueCommunication(self.default_config)

    @unittest2.skip("Skipping testOutputQueueFilterMatch.")
    def testOutputQueueFilterMatch(self):
        super(TestRedisClient, self).testOutputQueueFilterMatch(self.default_config)

    @unittest2.skip("Skipping testOutputQueueFilterNoMatch.")
    def testOutputQueueFilterNoMatch(self):
        super(TestRedisClient, self).testOutputQueueFilterNoMatch(self.default_config)

    @unittest2.skip("Skipping testWorksOnCopy.")
    def testWorksOnCopy(self):
        super(TestRedisClient, self).testWorksOnCopy(self.default_config)

    @unittest2.skip("Skipping testWorksOnOriginal.")
    def testWorksOnOriginal(self):
        super(TestRedisClient, self).testWorksOnOriginal(self.default_config)

if __name__ == '__main__':
    unittest.main()