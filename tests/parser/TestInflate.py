import zlib
import gzip
import mock
from io import BytesIO

import lumbermill.utils.DictUtils as DictUtils
from tests.ModuleBaseTestCase import ModuleBaseTestCase
from lumbermill.parser import Inflate


class TestInflate(ModuleBaseTestCase):

    def setUp(self):
        super(TestInflate, self).setUp(Inflate.Inflate(mock.Mock()))

    def testGzip(self):
        config = {'source_fields': 'gzip-compressed'}
        self.test_object.configure(config)
        self.checkConfiguration()
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(b"Spam! Spam! Spam! Lovely Spam! Spam! Spam!")
        payload = out.getvalue()
        data = DictUtils.getDefaultEventDict({'gzip-compressed': payload})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['gzip-compressed'] == "Spam! Spam! Spam! Lovely Spam! Spam! Spam!" )

    def testGzipWithTargetField(self):
        config = {'source_fields': 'gzip-compressed',
                  'target_fields': 'gzip-inflated'}
        self.test_object.configure(config)
        self.checkConfiguration()
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(b"Spam! Spam! Spam! Lovely Spam! Spam! Spam!")
        payload = out.getvalue()
        data = DictUtils.getDefaultEventDict({'gzip-compressed': payload})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['gzip-compressed'] == payload)
            self.assertTrue(event['gzip-inflated'] == "Spam! Spam! Spam! Lovely Spam! Spam! Spam!")

    def testMultipleGzipWithTargetFields(self):
        config = {'source_fields': ['gzip-compressed1', 'gzip-compressed2'],
                  'target_fields': ['gzip-inflated1', 'gzip-inflated2']}
        self.test_object.configure(config)
        self.checkConfiguration()
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(b"Spam! Spam! Spam! Lovely Spam! Spam! Spam!")
        payload1 = out.getvalue()
        out.seek(0)
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(b"Well, there's spam egg sausage and spam, that's not got much spam in it.")
        payload2 = out.getvalue()
        data = DictUtils.getDefaultEventDict({'gzip-compressed1': payload1, 'gzip-compressed2': payload2})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['gzip-compressed1'] == payload1)
            self.assertTrue(event['gzip-compressed2'] == payload2)
            self.assertTrue(event['gzip-inflated1'] == "Spam! Spam! Spam! Lovely Spam! Spam! Spam!")
            self.assertTrue(event['gzip-inflated2'] == "Well, there's spam egg sausage and spam, that's not got much spam in it.")

    def testZlib(self):
        config = {'source_fields': 'gzip-compressed',
                  'compression': 'zlib'}
        self.test_object.configure(config)
        self.checkConfiguration()
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(b"Spam! Spam! Spam! Lovely Spam! Spam! Spam!")
        payload = out.getvalue()
        data = DictUtils.getDefaultEventDict({'gzip-compressed': payload})
        for event in self.test_object.handleEvent(data):
            self.assertTrue(event['gzip-compressed'] == "Spam! Spam! Spam! Lovely Spam! Spam! Spam!" )
