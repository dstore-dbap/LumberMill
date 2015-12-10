# -*- coding: utf-8 -*-
import ModuleBaseTestCase
import mock

import lumbermill.Utils as Utils
from lumbermill.misc import RedisStore
from lumbermill.parser import XPathParser

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
        super(TestXPathParser, self).setUp(XPathParser.XPathParser(ModuleBaseTestCase.MockGambolPutty()))

    def testHandleData(self):
        self.test_object.configure({'source_field': 'agora_product_xml',
                                    'query': '//bookstore/book[@category="$(category)"]/title/text()'})
        self.checkConfiguration()
        event = Utils.getDefaultEventDict({'agora_product_xml': self.xml_string,
                                           'category': 'COOKING'})
        for event in self.test_object.handleEvent(event):
            self.assertTrue('gambolputty_xpath' in event and len(event['gambolputty_xpath']) > 0)

    def testHandleDataWithTargetField(self):
        self.test_object.configure({'source_field': 'agora_product_xml',
                                    'target_field': 'book_title',
                                    'query': '//bookstore/book[@category="$(category)"]/title/text()'})
        self.checkConfiguration()
        event = Utils.getDefaultEventDict({'agora_product_xml': self.xml_string,
                                         'category': 'COOKING'})
        for event in self.test_object.handleEvent(event):
            self.assertTrue('book_title' in event and len(event['book_title']) > 0)

    def testRedis(self):
        rc = RedisStore.RedisStore(mock.Mock())
        rc.configure({'server': 'localhost'})
        self.test_object.lumbermill.modules = {'RedisStore': {'instances': [rc]}}
        self.test_object.configure({'source_field': 'agora_product_xml',
                                    'target_field': 'book_title',
                                    'query': '//bookstore/book[@category="$(category)"]/title/text()',
                                    'redis_store': 'RedisStore',
                                    'redis_key': '$(category)',
                                    'redis_ttl': 60})
        self.checkConfiguration()
        event = Utils.getDefaultEventDict({'agora_product_xml': self.xml_string,
                                         'category': 'COOKING'})
        for event in self.test_object.handleEvent(event):
            redis_entry = rc.get('COOKING')
            self.assertEquals(event['book_title'], redis_entry)
