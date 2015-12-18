# -*- coding: utf-8 -*-
import gzip
import sys
import types
import zlib
from cStringIO import StringIO

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class InflateParser(BaseThreadedModule):
    """
    Inflate any field with supported compression codecs.

    It will take the source fields and decompress them with the configured codecs. At the moment only gzip an zlib are
    supported.

    source_fields: Single field or list of fields to decompress.
    target_fields: Single field or list of fields to fill with decompressed data.
                   If not provided, contents of source_fields will be replaced.
    compression:   Compression lib to use for decompression.

    Configuration template:

    - InflateParser:
       source_fields:                   # <default: 'data'; type: string||list; is: optional>
       target_fields:                   # <default: None; type: None||string||list; is: optional>
       compression:                     # <default: 'gzip'; type: string; is: optional; values: ['gzip', 'zlib']>
       receivers:
        - NextModule
    """

    module_type = "parser"
    """Set module type"""
    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.target_fields = self.getConfigurationValue('target_fields')
        # Allow single string as well.
        if isinstance(self.target_fields, types.StringTypes):
            self.target_fields = [self.target_fields]
        # If target_fields were provided they need to be of same length as source_fields.
        if self.target_fields and len(self.source_fields) != len(self.target_fields):
            self.logger.error("Count of configured source and target fields need to match. Please check your configuration.")
            self.lumbermill.shutDown()
        self.compression = self.getConfigurationValue('compression')
        # Get compression specific handler.
        try:
            self.deflater = getattr(self, "deflate_with_%s" % self.compression)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Unknown decompression lib: %s. Exception: %s, Error: %s" % (self.compression, etype, evalue))
            self.lumbermill.shutDown()

    def handleEvent(self, event):
        for idx, source_field in enumerate(self.source_fields):
            infalted_data = self.deflater(event[source_field])
            if not self.target_fields:
                event[source_field] = infalted_data
            else:
                event[self.target_fields[idx]] = infalted_data
        yield event

    def deflate_with_gzip(self, value):
        buffer = StringIO(value)
        try:
            deflated_value = gzip.GzipFile(fileobj=buffer)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not decompress data %s. Exception: %s, Error: %s." % (value, etype, evalue))
        return deflated_value.read()

    def deflate_with_zlib(self, value):
        try:
            # Adding 32 to windowBits will trigger header detection.
            deflated_value = zlib.decompress(value, zlib.MAX_WBITS|32)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not decompress data %s. Exception: %s, Error: %s." % (value, etype, evalue))
        return deflated_value
