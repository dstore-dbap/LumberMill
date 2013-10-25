# -*- coding: utf-8 -*-
import extendSysPath
import unittest
import ModuleBaseTestCase
import mock
import Utils
import XPathParser
import RedisClient

class TestXPathParser(ModuleBaseTestCase.ModuleBaseTestCase):

    xml_string = """<?xml version="1.0" encoding="ISO-8859-1"?>

<bookstore>

<book category="COOKING">
  <title lang="en">Everyday Italian</title>
  <author>Giada De Laurentiis</author>
  <year>2005</year>
  <price>30.00</price>
</book>

<book category="CHILDREN">
  <title lang="en">Harry Potter</title>
  <author>J K. Rowling</author>
  <year>2005</year>
  <price>29.99</price>
</book>

<book category="WEB">
  <title lang="en">XQuery Kick Start</title>
  <author>James McGovern</author>
  <author>Per Bothner</author>
  <author>Kurt Cagle</author>
  <author>James Linn</author>
  <author>Vaidyanathan Nagarajan</author>
  <year>2003</year>
  <price>49.99</price>
</book>

<book category="WEB">
  <title lang="en">Learning XML</title>
  <author>Erik T. Ray</author>
  <year>2003</year>
  <price>39.95</price>
</book>

</bookstore>"""

    def setUp(self):
        super(TestXPathParser, self).setUp(XPathParser.XPathParser(gp=mock.Mock()))

    def testHandleData(self):
        self.test_object.configure({'source-field': 'agora_product_xml',
                                    'query': '//bookstore/book[@category="%(category)s"]/title/text()'})
        data = Utils.getDefaultDataDict({'agora_product_xml': self.xml_string,
                                         'category': 'COOKING'})
        result = self.test_object.handleData(data)
        self.assertTrue('gambolputty_xpath' in result and len(result['gambolputty_xpath']) > 0)

    def testHandleDataWithTargetField(self):
        self.test_object.configure({'source-field': 'agora_product_xml',
                                    'target-field': 'book_title',
                                    'query': '//bookstore/book[@category="%(category)s"]/title/text()'})
        data = Utils.getDefaultDataDict({'agora_product_xml': self.xml_string,
                                         'category': 'COOKING'})
        result = self.test_object.handleData(data)
        self.assertTrue('book_title' in result and len(result['book_title']) > 0)

    def testRedis(self):
        rc = RedisClient.RedisClient(gp=mock.Mock())
        rc.configure({'server': 'es-01.dbap.de'})
        self.test_object.gp.modules = {'RedisClient': [{'instance': rc}]}
        self.test_object.configure({'source-field': 'agora_product_xml',
                                    'target-field': 'book_title',
                                    'query': '//bookstore/book[@category="%(category)s"]/title/text()',
                                    'redis-client': 'RedisClient',
                                    'redis-key': '%(category)s',
                                    'redis-ttl': 5})
        self.test_object.initRedisClient()
        data = Utils.getDefaultDataDict({'agora_product_xml': self.xml_string,
                                         'category': 'COOKING'})
        result = self.test_object.handleData(data)
        redis_entry = self.test_object.getRedisValue('COOKING')
        self.assertEquals(result['book_title'], redis_entry)

    def testQueueCommunication(self):
        config = {'source-field': 'agora_product_xml', 'query': '//bookstore/book[@category="%(category)s"]/title/text()'}
        super(TestXPathParser, self).testQueueCommunication(config)

    def testOutputQueueFilter(self):
        config = {'source-fields': 'agora_product_xml', 'query': '//bookstore/book[@category="%(category)s"]/title/text()'}
        super(TestXPathParser, self).testOutputQueueFilter(config)

    def testInvertedOutputQueueFilter(self):
        config = {'source-fields': 'agora_product_xml', 'query': '//bookstore/book[@category="%(category)s"]/title/text()'}
        super(TestXPathParser, self).testInvertedOutputQueueFilter(config)

    def testWorksOnCopy(self):
        config = {'source-fields': 'agora_product_xml', 'query': '//bookstore/book[@category="%(category)s"]/title/text()'}
        super(TestXPathParser, self).testWorksOnCopy(config)

    def testWorksOnOriginal(self):
        config = {'source-fields': 'agora_product_xml', 'query': '//bookstore/book[@category="%(category)s"]/title/text()'}
        super(TestXPathParser, self).testWorksOnOriginal(config)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()