# -*- coding: utf-8 -*-
import mock

from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.misc import RedisStore

class TestRedisStore(ModuleBaseTestCase):

    def setUp(self):
        super(TestRedisStore, self).setUp(RedisStore.RedisStore(mock.Mock()))

    def testGetClient(self):
        self.test_object.configure({'server': 'localhost'})
        self.checkConfiguration()
        rc = self.test_object.getClient()
        self.assertEqual(rc.__class__.__name__, 'StrictRedis')

    def testSetGetValue(self):
        self.test_object.configure({'server': 'localhost'})
        value = 'de-von-Ausfern-schplenden-schlitter-crass-cren-bon-fried-digger-dingle-dangle-dongle-dungle-burstein-von-knacker-thrasher-apple-banger-horowitz-ticolensic-grander-knotty-spelltinkle-grandlich-grumblemeyer-spelter-wasser-kurstlich-himble-eisen-bahnwagen-guten-abend-bitte-ein-nürnburger-bratwürstel-gespurten-mitz-weimache-luber-hundsfut-gumberaber-schönendanker-kalbsfleisch-mittleraucher-von-Hautkopft of Ulm'
        self.checkConfiguration()
        rc = self.test_object.getClient()
        rc.setex('Johann Gambolputty', 10, value)
        test = rc.get('Johann Gambolputty')
        self.assertEquals(test, value)
