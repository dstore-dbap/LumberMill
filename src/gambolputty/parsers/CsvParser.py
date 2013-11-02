# -*- coding: utf-8 -*-
import sys
import BaseThreadedModule
import csv
from cStringIO import StringIO
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class CsvParser(BaseThreadedModule.BaseThreadedModule):
    """
    Parse a string as csv data.

    It will parse the csv and create or replace fields in the internal data dictionary with
    the corresponding csv fields.

    Configuration example:

    - module: CsvParser
      configuration:
        source_field: 'data'                    # <default: 'data'; type: string; is: optional>
        escapechar: \                           # <default: '\'; type: string; is: optional>
        skipinitialspace: False                 # <default: False; type: boolean; is: optional>
        quotechar: '"'                          # <default: '"'; type: string; is: optional>
        delimiter: ';'                          # <default: '|'; type: char; is: optional>
        fieldnames: ["gumby", "brain", "specialist"]        # <default: False; type: [list]; is: optional>
      receivers:
        - NextHandler
    """

    def handleData(self, data):
        try:
            csv_dict = csv.reader(StringIO(data[self.getConfigurationValue('source_field', data)]),
                                  escapechar=self.getConfigurationValue('escapechar', data),
                                  skipinitialspace=self.getConfigurationValue('skipinitialspace', data),
                                  quotechar=self.getConfigurationValue('quotechar', data),
                                  delimiter=self.getConfigurationValue('delimiter', data))
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not parse csv data %s. Exception: %s, Error: %s." % (data, etype, evalue))
            yield data
        field_names = self.getConfigurationValue('fieldnames', data)
        for values in csv_dict:
            if not field_names:
                # Use first line for field names if none were provided.
                field_names = values
                continue
            for index,value in enumerate(values):
                try:
                    data[field_names[index]] = value
                except KeyError:
                    pass
                except IndexError:
                    pass
        yield data