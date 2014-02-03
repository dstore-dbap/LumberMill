# -*- coding: utf-8 -*-
import extendSysPath
import ModuleBaseTestCase
import mock
import RedisStore

class TestRedisStore(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        super(TestRedisStore, self).setUp(RedisStore.RedisStore(gp=mock.Mock()))

    def testGetClient(self):
        self.test_object.configure({'server': 'es-01.dbap.de'})
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        rc = self.test_object.getClient()
        self.assertEqual(rc.__class__.__name__, 'StrictRedis')

    def testSetGetValue(self):
        self.test_object.configure({'server': 'es-01.dbap.de'})
        value = 'de-von-Ausfern-schplenden-schlitter-crass-cren-bon-fried-digger-dingle-dangle-dongle-dungle-burstein-von-knacker-thrasher-apple-banger-horowitz-ticolensic-grander-knotty-spelltinkle-grandlich-grumblemeyer-spelter-wasser-kurstlich-himble-eisen-bahnwagen-guten-abend-bitte-ein-nürnburger-bratwürstel-gespurten-mitz-weimache-luber-hundsfut-gumberaber-schönendanker-kalbsfleisch-mittleraucher-von-Hautkopft of Ulm'
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)
        rc = self.test_object.getClient()
        rc.setex('Johann Gambolputty', 10, value)
        test = rc.get('Johann Gambolputty')
        self.assertEquals(test, value)

if __name__ == '__main__':
    unittest.main()