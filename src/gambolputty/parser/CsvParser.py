# -*- coding: utf-8 -*-
import sys
import BaseThreadedModule
import csv
from cStringIO import StringIO
import Decorators


@Decorators.ModuleDocstringParser
class CsvParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse a string as csv data.

    It will parse the csv and create or replace fields in the internal data dictionary with
    the corresponding csv fields.

    Configuration template:

    - CsvParser:
        source_field:                           # <default: 'data'; type: string; is: optional>
        escapechar:                             # <default: '\'; type: string; is: optional>
        skipinitialspace:                       # <default: False; type: boolean; is: optional>
        quotechar:                              # <default: '"'; type: string; is: optional>
        delimiter:                              # <default: '|'; type: char; is: optional>
        fieldnames:                             # <default: False; type: [list]; is: optional>
        receivers:
          - NextModule
    """

    module_type = "parser"
    """Set module type"""

    def handleEvent(self, event):
        try:
            csv_dict = csv.reader(StringIO(event[self.getConfigurationValue('source_field', event)]),
                                  escapechar=self.getConfigurationValue('escapechar', event),
                                  skipinitialspace=self.getConfigurationValue('skipinitialspace', event),
                                  quotechar=self.getConfigurationValue('quotechar', event),
                                  delimiter=self.getConfigurationValue('delimiter', event))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.warning("Could not parse csv data %s. Exception: %s, Error: %s." % (event, etype, evalue))
            yield event
            return
        field_names = self.getConfigurationValue('fieldnames', event)
        for values in csv_dict:
            if not field_names:
                # Use first line for field names if none were provided.
                field_names = values
                continue
            for index,value in enumerate(values):
                try:
                    event[field_names[index]] = value
                except KeyError:
                    pass
                except IndexError:
                    pass
        yield event