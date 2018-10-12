import mock
import unittest
import tests.ModuleBaseTestCase

import lumbermill.utils.DictUtils as DictUtils
from lumbermill.modifier import Math


class TestModuleFilters(tests.ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        event = {'bytes_send': 3395,
                 'data': '192.168.2.20 - - [28/Jul/2006:10:27:10 -0300] "GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0" 200 3395\n',
                 'datetime': '28/Jul/2006:10:27:10 -0300',
                 'lumbermill': {
                                'event_id': '715bd321b1016a442bf046682722c78e',
                                'event_type': 'httpd_access_log',
                                'received_from': '127.0.0.1',
                                'source_module': 'StdIn',
                                'list': [10, 20, {'hovercraft': 'eels'}]
                  },
                 'http_status': 200,
                 'cache_hits': 5,
                 'identd': '-',
                 'remote_ip': '192.168.2.20',
                 'url': 'GET /wiki/Monty_Python/?spanish=inquisition HTTP/1.0',
                 'fields': ['nobody', 'expects', 'the'],
                 'params':  { u'spanish': [u'inquisition']},
                 'user': '-'}
        self.event = DictUtils.getDefaultEventDict(event)
        super(TestModuleFilters, self).setUp(Math.Math(mock.Mock()))

    def testInputFilterMatch(self):
        self.test_object.configure({'filter': 'if $(lumbermill.source_module) == "StdIn" and $(lumbermill.list.2.hovercraft) == "eels"',
                                    'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2'})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        for event in self.receiver.getEvent():
            self.assertTrue(event['test'] == 10)

    def testInputFilterOnNonExistingField(self):
        self.test_object.configure({'filter': 'if $() == "StdIn" and $(lumbermill.list.2.hovercraft) == "eels"',
                                    'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2'})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        for event in self.receiver.getEvent():
            self.assertTrue(event['test'] == 10)


    @unittest.skip("Some methodcalls are still failing due to problems with regex. Work in progress.")
    def testInputFilterMatchWithMethodCall(self):
        self.test_object.configure({'filter': 'if $(url).startswith("GET")',
                                    'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2'})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        for event in self.receiver.getEvent():
            self.assertTrue(event['test'] == 10)

    def testInputFilterNoMatch(self):
        self.test_object.configure({'filter': 'if $(lumbermill.source_module) == "StdIn" and $(lumbermill.list.2.hovercraft) == "fish"',
                                    'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2'})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        for event in self.receiver.getEvent():
            self.assertTrue('test' not in event)

    def testOutputFilterMatch(self):
        self.test_object.configure({'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2',
                                    'receivers': [{'MockReceiver': {
                                                      'filter': 'if $(lumbermill.source_module) == "StdIn"'}}]})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        received_event = None
        for event in self.receiver.getEvent():
            received_event = event
        self.assertTrue(received_event != None)

    def testOutputFilterNoMatch(self):
        self.test_object.configure({'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2',
                                    'receivers': [{'MockReceiver': {
                                                      'filter': 'if $(lumbermill.source_module) != "StdIn"'}}]})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        received_event = None
        for event in self.receiver.getEvent():
            received_event = event
        self.assertTrue(received_event == None)

    @unittest.skip("Some methodcalls are still failing due to problems with regex. Work in progress.")
    def testOutputFilterMatchWithMethodCall(self):
        self.test_object.configure({'target_field': 'test',
                                    'function': 'int($(cache_hits)) * 2',
                                    'receivers': [{'MockReceiver': {
                                                      'filter': 'if $(url).startswith("GET")'}}]})
        self.checkConfiguration()
        self.test_object.receiveEvent(self.event)
        received_event = None
        for event in self.receiver.getEvent():
            received_event = event
        self.assertTrue(received_event != None)