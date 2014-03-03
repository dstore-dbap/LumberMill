# -*- coding: utf-8 -*-
import sys
import types
import msgpack
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class MsgPackParser(BaseModule.BaseModule):
    """
    It will parse the msgpack data and create or replace fields in the internal data dictionary with
    the corresponding json fields.

    Configuration example:

    - MsgPackParser:
        mode:                                   # <default: 'decode'; type: string; values: ['decode','encode']; is: optional>
        source_fields:                          # <default: 'data'; type: string||list; is: optional>
        target_field:                           # <default: None; type: None||string; is: optional>
        keep_original:                          # <default: False; type: boolean; is: optional>
        receivers:
          - NextHandler
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.source_fields = self.getConfigurationValue('source_fields')
        # Allow single string as well.
        if isinstance(self.source_fields, types.StringTypes):
            self.source_fields = [self.source_fields]
        self.target_field = self.getConfigurationValue('target_field')
        self.drop_original = not self.getConfigurationValue('keep_original')
        if self.getConfigurationValue('mode') == 'decode':
            self.handleEvent = self.decodeEvent
        else:
            self.handleEvent = self.encodeEvent

    def decodeEvent(self, event):
        for source_field in self.source_fields:
            if source_field not in event:
                continue
            try:
                decoded_data = msgpack.unpackb(event[source_field])
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.warning("%sCould not parse msgpack event data: %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, event, etype, evalue, Utils.AnsiColors.ENDC))
                continue
            if self.drop_original:
                event.pop(source_field, None)
            if self.target_field:
                event.update({self.target_field: decoded_data})
            else:
                event.update(decoded_data)
        yield event

    def encodeEvent(self, event):
        if self.source_fields == 'all':
            encode_data = event
        else:
            encode_data = []
            for source_field in self.source_fields:
                if source_field not in event:
                    continue
                encode_data.append({source_field: event[source_field]})
                if self.drop_original:
                    event.pop(source_field, None)
        try:
            encode_data = msgpack.packb(encode_data)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("%sCould not msgpack encode event data: %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, event, etype, evalue, Utils.AnsiColors.ENDC))
            yield event
            return
        event.update({self.target_field: encode_data})
        yield event