# -*- coding: utf-8 -*-
import sys
import Queue
import logging
import logging.config
import threading
import unittest

import mock

sys.path.append('../')

from lumbermill.constants import LOGLEVEL_STRING_TO_LOGLEVEL_INT
from lumbermill.utils.ConfigurationValidator import ConfigurationValidator
from lumbermill.utils.misc import AnsiColors, coloredConsoleLogging


class StoppableThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class MockGambolPutty(mock.Mock):

    def __init__(self):
        mock.Mock.__init__(self)
        self.modules = {}

    def getModuleInfoById(self, module_name):
        try:
            return self.modules[module_name]
        except KeyError:
            self.logger.error("Get module by name %s failed. No such module." % (module_name, AnsiColors.ENDC))
            return None

    def initModule(self, module_name):
        instance = None
        try:
            module = __import__(module_name)
            module_class = getattr(module, module_name)
            instance = module_class(self)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not init module %s. Exception: %s, Error: %s." % (module_name, etype, evalue))
        return instance

    def addModule(self, module_name, mod):
        if module_name not in self.modules:
            self.modules[module_name] = mod

    def shutDown(self):
        for module_name, mod in self.modules.iteritems():
            mod.shutDown()

class MockReceiver(mock.Mock):

    def __init__(self):
        mock.Mock.__init__(self)
        self.events = []
        self.filter = False

    def setFilter(self, filter):
        self.filter = filter

    def getFilter(self):
        return self.filter

    def receiveEvent(self, event):
        self.handleEvent(event)
        return event

    def handleEvent(self, event):
        self.events.append(event)

    def getEvent(self):
        for event in self.events:
            yield event

    def hasEvents(self):
        return True if len(self.events) > 0 else False

class ModuleBaseTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ModuleBaseTestCase, self).__init__(*args, **kwargs)
        self.global_configuration = {'logging': {'level': 'info',
                                                 'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                                 'filename': None,
                                                 'filemode': 'w'}}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.configureLogging()
        self.conf_validator = ConfigurationValidator()
        self.receiver = MockReceiver()

    def configureLogging(self):
        # Logger configuration.
        if self.global_configuration['logging']['level'].lower() not in LOGLEVEL_STRING_TO_LOGLEVEL_INT:
            print("Loglevel unknown.")
            sys.exit(255)
        log_level = LOGLEVEL_STRING_TO_LOGLEVEL_INT[self.global_configuration['logging']['level'].lower()]
        logging.basicConfig(level=log_level,
                            format=self.global_configuration['logging']['format'],
                            filename=self.global_configuration['logging']['filename'],
                            filemode=self.global_configuration['logging']['filemode'])
        if not self.global_configuration['logging']['filename']:
            logging.StreamHandler.emit = coloredConsoleLogging(logging.StreamHandler.emit)

    def setUp(self, test_object):
        test_object.addReceiver('MockReceiver', self.receiver)
        self.test_object = test_object
        if hasattr(test_object, 'setInputQueue'):
            self.input_queue = Queue.Queue()
            self.test_object.setInputQueue(self.input_queue)

    def checkConfiguration(self):
        result = self.conf_validator.validateModuleConfiguration(self.test_object)
        self.assertFalse(result)

    def startTornadoEventLoop(self):
        import tornado.ioloop
        self.ioloop_thread = StoppableThread(target=tornado.ioloop.IOLoop.instance().start)
        self.ioloop_thread.daemon = True
        self.ioloop_thread.start()

    def stopTornadoEventLoop(self):
        if not hasattr(self, 'ioloop_thread'):
            return
        import tornado.ioloop
        tornado.ioloop.IOLoop.instance().stop()
        self.ioloop_thread.stop()

    """
    def testQueueCommunication(self, config = {}):
        self.test_object.configure(config)
        if hasattr(self.test_object, 'start'):
            self.test_object.start()
        else:
            self.test_object.run()
        self.input_queue.put(Utils.getDefaultEventDict({}))
        queue_emtpy = False
        try:
            self.output_queue.get(timeout=2)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy != True)

    def testWorksOnOriginal(self, config = {}):
        config['work_on_copy'] = {'value': False, 'contains_dynamic_value': False}
        data_dict = Utils.getDefaultEventDict({})
        self.test_object.configure(config)
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            returned_data_dict = self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy == False and returned_data_dict is data_dict)


    def testWorksOnCopy(self, config = {}):
        config['work_on_copy'] = {'value': True, 'contains_dynamic_value': False}
        data_dict = Utils.getDefaultEventDict({})
        self.test_object.configure(config)
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        try:
            returned_data_dict = self.output_queue.get(timeout=1)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy == False and returned_data_dict is not data_dict)


    def testOutputQueueFilterNoMatch(self, config = {}):
        output_queue = Queue.Queue()
        data_dict = Utils.getDefaultEventDict({})
        data_dict['Johann'] = 'Gambolputty'
        result = self.test_object.configure(config)
        self.assertFalse(result)
        self.test_object.addOutputQueue(output_queue, filter='Johann == "Gambolputty de von ausfern" or Johann != "Gambolputty"')
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        returned_data_dict = {}
        try:
            returned_data_dict = output_queue.get(timeout=2)
        except Queue.Empty:
            queue_emtpy = True
        self.assert_(queue_emtpy == True)

    def testOutputQueueFilterMatch(self,config = {}):
        output_queue = Queue.Queue()
        data_dict = Utils.getDefaultEventDict({'Johann': 'Gambolputty', 'event_type': 'agora_access_log'})
        result = self.test_object.configure(config)
        self.assertFalse(result)
        self.test_object.addOutputQueue(output_queue, filter='Johann in ["Gambolputty", "Blagr"] or Johan not in ["Gambolputty", "Blagr"]')
        self.test_object.start()
        self.input_queue.put(data_dict)
        queue_emtpy = False
        returned_data_dict = {}
        try:
            returned_data_dict = output_queue.get(timeout=2)
        except Queue.Empty:
            queue_emtpy = True
        print data_dict
        print returned_data_dict
        self.assert_(queue_emtpy == False and 'Johann' in returned_data_dict)
    """

    def tearDown(self):
        self.stopTornadoEventLoop()
        self.test_object.shutDown()
