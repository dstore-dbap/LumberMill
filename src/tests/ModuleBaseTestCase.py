import extendSysPath
import threading
import unittest2
import mock
import ConfigurationValidator
import logging
import logging.config
import Queue
import Utils

class MockGambolPutty(mock.Mock):

    def __init__(self):
        mock.Mock.__init__(self)
        self.modules = {}

    def getModuleInfoById(self, module_name):
        try:
            return self.modules[module_name]
        except KeyError:
            self.logger.error("%sGet module by name %s failed. No such module.%s" % (Utils.AnsiColors.FAIL, module_name, Utils.AnsiColors.ENDC))
            return None

    def addModule(self, module_name, mod):
        if module_name not in self.modules:
            self.modules[module_name] = mod

    def shutDown(self):
        for module_name, mod in self.modules.iteritems():
            mod.shutDown()

class MockReceiver():

    def __init__(self):
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

class ModuleBaseTestCase(unittest2.TestCase):

    def setUp(self, test_object):
        logging.config.fileConfig('../conf/logger.conf')
        self.conf_validator = ConfigurationValidator.ConfigurationValidator()
        self.receiver = MockReceiver()
        test_object.logger.addHandler(logging.StreamHandler())
        test_object.addReceiver('MockReceiver', self.receiver)
        self.test_object = test_object
        if hasattr(test_object, 'setInputQueue'):
            self.input_queue = Queue.Queue()
            self.test_object.setInputQueue(self.input_queue)

    def checkConfiguration(self):
        result = self.conf_validator.validateModuleInstance(self.test_object)
        self.assertFalse(result)

    def startTornadoEventLoop(self):
        import tornado.ioloop
        self.ioloop_thread = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
        self.ioloop_thread.daemon = True
        self.ioloop_thread.start()

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
        config['work_on_copy'] = {'value': False, 'contains_placeholder': False}
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
        config['work_on_copy'] = {'value': True, 'contains_placeholder': False}
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
        self.test_object.shutDown()
