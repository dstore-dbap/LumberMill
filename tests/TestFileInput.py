import time

import sys

import ModuleBaseTestCase
import tempfile

from lumbermill.input import File


class TestFileInput(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        test_object = File.File(ModuleBaseTestCase.MockGambolPutty())
        test_object.lumbermill.addModule('File', test_object)
        super(TestFileInput, self).setUp(test_object)
        self.temp_file = None

    def testAbsoluteFilePath(self):
        self.test_object.configure({'paths': './test_data/file_input/cheese.py'})
        self.test_object.checkConfiguration()
        self.assertEquals(self.test_object.files, ['./test_data/file_input/cheese.py'])

    def testMultipleFilePaths(self):
        self.test_object.configure({'paths': ['./test_data/file_input/',
                                              './test_data/file_input/second_level']})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 5)

    def testFindFilesNotRecursive(self):
        self.test_object.configure({'paths': './test_data/file_input/'})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 3)

    def testFindFilesRecursive(self):
        self.test_object.configure({'paths': './test_data/file_input',
                                    'recursive': True})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 6)

    def testFindFilesWithPattern(self):
        self.test_object.configure({'paths': './test_data/file_input',
                                    'recursive': True,
                                    'pattern': '*.info'})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 2)
        self.assertEquals(self.test_object.files[1], './test_data/file_input/second_level_2/spam.info')

    def testReadFileComplete(self):
        self.test_object.configure({'paths': './test_data/file_input',
                                    'recursive': True,
                                    'pattern': 'spam.info'})
        self.test_object.checkConfiguration()
        self.test_object.start()
        time.sleep(.2)
        for event in self.receiver.getEvent():
            self.assertEquals(event['data'], 'Spam!\nSpam! Spam!\nSpam! Spam! Spam!')

    def testReadFileLineByLine(self):
        self.test_object.configure({'paths': './test_data/file_input',
                                    'recursive': True,
                                    'pattern': 'spam.info',
                                    'line_by_line': True})
        self.test_object.checkConfiguration()
        self.test_object.start()
        time.sleep(.2)
        line_counter = 0
        for event in self.receiver.getEvent():
            line_counter += 1
        self.assertEquals(line_counter, 3)
        self.assertEquals(event['data'], 'Spam! Spam! Spam!')

    def testFileTailMode(self):
        self.temp_file = tempfile.NamedTemporaryFile()
        self.test_object.configure({'log_level': 'info',
                                    'paths': self.temp_file.name,
                                    'line_by_line': True,
                                    'mode': 'tail',
                                    'stat_interval': .1})
        self.test_object.checkConfiguration()
        self.test_object.start()
        # Give tail threads a bit time to initialize.
        time.sleep(.2)
        self.temp_file.write("Spam!\nSpam! Spam!\nSpam! Spam! Spam!\n")
        # Force os to flush data to file.
        self.temp_file.read()
        time.sleep(.2)
        events = []
        for event in self.receiver.getEvent():
            events.append(event)
        self.assertTrue(len(events) == 3)
        self.assertTrue(events[0]['data'] == "Spam!")
        self.assertTrue(events[1]['data'] == "Spam! Spam!")
        self.assertTrue(events[2]['data'] == "Spam! Spam! Spam!")

    def tearDown(self):
        ModuleBaseTestCase.ModuleBaseTestCase.tearDown(self)
        if self.temp_file:
            try:
                self.temp_file.close()
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("Could not remove temporary file %s" % self.temp_file.name)