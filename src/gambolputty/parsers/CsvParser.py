# -*- coding: utf-8 -*-
import sys
import BaseModule
import csv
from cStringIO import StringIO

class CsvParser(BaseModule.BaseModule):
   
    def configure(self, configuration):
        # Call parent configure method
        super(CsvParser, self).configure(configuration)
        # Set defaults
        self.escapechar = configuration['escapechar'] if 'escapechar' in configuration else "\\"
        self.skipinitialspace = configuration['skipinitialspace'] if 'skipinitialspace' in configuration else False
        self.quotechar = configuration['quotechar'] if 'quotechar' in configuration else '"'
        self.delimiter = configuration['delimiter'] if 'delimiter' in configuration else ';'
        self.fieldnames = configuration['fieldnames'] if 'fieldnames' in configuration else False
    
    def handleData(self, data):
        """
        This method expects csv content in the internal data dictionary data field.
        It will just parse the csv and create or replace fields in the internal data dictionary with
        the corresponding csv fields.
        Example configuration:
        
        - module: CsvParser
          configuration:
            escapechar: "\\"
            delimiter: "|"
            quotechar: '"'
            skipinitialspace: False
            fieldnames: ["gumby", "brain", "specialist"]
          receivers: 
            - NextHandler
        """
        try: 
            csv_dict = csv.reader(StringIO(data['data']), escapechar=self.escapechar, skipinitialspace=self.skipinitialspace, quotechar=self.quotechar, delimiter=self.delimiter)
        except:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("Could not parse csv data %s. Exception: %s, Error: %s." % (data, etype, evalue))
            return
        field_names = self.fieldnames
        for values in csv_dict:
            if not field_names:
                field_names = values
                continue
            for index,value in enumerate(values):
                data[field_names[index]] = value
        self.logger.debug("Output: %s" % data)