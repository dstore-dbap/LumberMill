# -*- coding: utf-8 -*-
import csv
import sys
from cStringIO import StringIO

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser


@ModuleDocstringParser
class CsvParser(BaseThreadedModule):
    """
    Parse a string as csv data.

    It will parse the csv and create or replace fields in the internal data dictionary with
    the corresponding csv fields.

    source_field: Field that contains the csv data.
    escapechar: Char used to escape special characters.
    skipinitialspace: When True, whitespace immediately following the delimiter is ignored. The default is False.
    quotechar: A one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters.
    delimiter: A one-character string used to separate fields.
    fieldnames: Fieldnames to be used for the extracted csv data.

    Configuration template:

    - CsvParser:
       source_field:                    # <default: 'data'; type: string; is: optional>
       escapechar:                      # <default: '\'; type: string; is: optional>
       skipinitialspace:                # <default: False; type: boolean; is: optional>
       quotechar:                       # <default: '"'; type: string; is: optional>
       delimiter:                       # <default: '|'; type: string; is: optional>
       fieldnames:                      # <type: list; is: required>
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
            for index, value in enumerate(values):
                try:
                    event[field_names[index]] = value
                except KeyError:
                    pass
                except IndexError:
                    pass
        yield event