import pprint
import time
import ModuleBaseTestCase
from lumbermill.input import File


class TestFileInput(ModuleBaseTestCase.ModuleBaseTestCase):

    def setUp(self):
        test_object = File.File(ModuleBaseTestCase.MockGambolPutty())
        test_object.lumbermill.addModule('File', test_object)
        super(TestFileInput, self).setUp(test_object)

    def testAbsoluteFilePath(self):
        self.test_object.configure({'paths': './test_data/file_input/cheese.py'})
        self.test_object.checkConfiguration()
        self.assertEquals(len(self.test_object.files), 1)

    def testMultipleFilePaths(self):
        self.test_object.configure({'paths': ['./test_data/file_input/',
                                              './test_data/file_input/second_level']})
        print(self.test_object.files)
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

    def tearDown(self):
        pass