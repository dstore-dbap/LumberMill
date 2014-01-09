# -*- coding: utf-8 -*-
import sys
import BaseModule
import msgpack
from Decorators import ModuleDocstringParser

for module_name in ['msgpack', 'msgpack_pure']:
    try:
        msgpack = __import__(module_name)
        break
    except ImportError:
        pass


@ModuleDocstringParser
class MsgPackParser(BaseModule.BaseModule):
    """
    It will parse the msgpack data and create or replace fields in the internal data dictionary with
    the corresponding json fields.

    Configuration example:

    - module: MsgPackParser
      configuration:
        source_field: 'data'                    # <default: 'data'; type: string; is: optional>
        keep_original: True                     # <default: False; type: boolean; is: optional>
      receivers:
        - NextHandler
    """

    module_type = "parser"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.source_field = self.getConfigurationValue('source_field')
        self.drop_original = not self.getConfigurationValue('keep_original')

    def handleEvent(self, event):
        if self.source_field not in event:
            yield event
            return
        #json_string = str(event[self.source_field]).strip("'<>() ").replace('\'', '\"')
        try:
            msgpack_data = msgpack.unpackb(event[self.source_field])
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not parse msgpack data %s. Exception: %s, Error: %s." % (event, etype, evalue))
            yield event
            return
        if self.drop_original:
            event.pop(self.source_field, None)
        event.update(msgpack_data)
        yield event