# -*- coding: utf-8 -*-
import sys
import re
import hashlib
import BaseThreadedModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class ModifyFields(BaseThreadedModule.BaseThreadedModule):
    """
    Simple module to add/delete/change field values.

    Configuration examples:

    # Keep all fields listed in source-fields, discard all others.
    - module: ModifyFields
      configuration:
        action: keep                                # <type: string; is: required>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Discard all fields listed in source-fields.
    - module: ModifyFields
      configuration:
        action: delete                              # <type: string; is: required>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Replace field values in data dictionary with self.getConfigurationValue['with'].
    - module: ModifyFields
      configuration:
        action: replace                             # <type: string; is: required>
        source_field: field1                        # <type: string; is: required>
        regex: ['<[^>]*>', 're.MULTILINE | re.DOTALL'] # <type: list; is: required>
        with: 'Johann Gambolputty'                  # <type: string; is: required>
      receivers:
        - NextModule

    # Map a field value.
    - module: ModifyFields
      configuration:
        action: map                                 # <type: string; is: required>
        source_field: http_status                   # <type: string; is: required>
        map: {100: 'Continue', 200: 'OK', ... }     # <type: dictionary; is: required>
        target_field: http_status                   # <default: "%(source_field)s_mapped"; type: string; is: optional>
      receivers:
        - NextModule

    # Cast field values to integer.
    - module: ModifyFields
      configuration:
        action: castToInteger                       # <type: string; is: required>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to float.
    - module: ModifyFields
      configuration:
        action: castToFloat                         # <type: string; is: required>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to string.
    - module: ModifyFields
      configuration:
        action: castToString                        # <type: string; is: required>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to boolean.
    - module: ModifyFields
      configuration:
        action: castToBoolean                       # <type: string; is: required>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Create a hash from a field value.
    # If target_fields is provided, it should have the same length as source_fields.
    # If target_fields is not provided, source_fields will be replaced with the hashed value.
    # Hash algorithm can be any of the in hashlib supported algorithms.
    - module: ModifyFields
      configuration:
        action: hash                                # <type: string; is: required>
        algorithm: sha1                             # <default: "md5"; type: string; is: optional;>
        source_fields: [field1, field2, ... ]       # <type: list; is: required>
        target_fields: [f1, f2, ... ]               # <default: []; type: list; is: optional>
      receivers:
        - NextModule
"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.BaseThreadedModule.configure(self, configuration)
        # Set defaults
        self.typecast_switch = { 'int': self.castToInteger,
                                 'integer': self.castToInteger,
                                 'float': self.castToFloat,
                                 'str': self.castToString,
                                 'string': self.castToString,
                                 'bool': self.castToBoolean,
                                 'boolean': self.castToBoolean,
                                }
        self.action = configuration['action']
        # Precompile regex for replacement if defined
        if 'regex' in configuration:
            regex_pattern = configuration['regex']
            regex_options = 0
            if isinstance(regex_pattern, list):
                i = iter(regex_pattern)
                # Pattern is the first entry
                regex_pattern = i.next()
                # Regex options the second
                try:
                    regex_options = eval(i.next())
                except:
                    etype, evalue, etb = sys.exc_info()
                    self.logger.error("RegEx error for options %s. Exception: %s, Error: %s" % (regex_options, etype, evalue))
                    self.gp.shutDown()
            try:
                self.regex = re.compile(regex_pattern, regex_options)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, etype, evalue))
                self.gp.shutDown()

    def handleData(self, event):
        try:
            event = self.__getattribute__("%s" % self.action)(event)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("ModifyFields action called that does not exist: %s. Exception: %s, Error: %s" % (self.action, etype, evalue))
            self.gp.shutDown()
        yield event

    def keep(self,data):
        """
        Field names not listed in self.configuration_data['source-fields'] will be deleted from data dictionary.

        @param data: dictionary
        @return: data: dictionary
        """
        fields_to_del = set(data).difference(self.getConfigurationValue('source_fields', data))
        for field in fields_to_del:
            data.pop(field, None)
        return data

    def delete(self, data):
        """
        Field names listed in ['source_fields'] will be deleted from data dictionary.

        @todo: pypy seems to handle simple tight loops better than
        - first building a set from data dictionary and
        - then get common keys from ['source_fields'] and data via intersection

        e.g.:
        fields_to_check = self.getConfigurationValue('source_fields').intersection(set(data))

        Still, if the field set is a large one, the above approach could be faster.

        This problem affects this and some more methods in this class.
        Maybe the code can be altered to take this into account.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source_fields', data):
            data.pop(field, None)
        return data

    def replace(self, data):
        """
        Field value in data dictionary will be replace with ['with']

        @param data: dictionary
        @return: data: dictionary
        """
        field = self.getConfigurationValue('source_field', data)
        try:
            data[field] = self.regex.sub(self.getConfigurationValue('with', data), data[field])
        except KeyError:
            pass
        return data

    def map(self, data):
        """
        Field values in data dictionary will be mapped to ['with'][data[field]].
        By default, the target field is ${fieldname}_mapped and can be overwritten by config
        value "target_field"

        Useful e.g. to map http status codes to human readable status codes.
        @param data: dictionary
        @return data: dictionary
        """
        field = self.getConfigurationValue('source_field', data)
        target_field_name = self.getConfigurationValue('target_field', data) if 'target_field' in self.configuration_data else "%s_mapped" % field
        try:
            data[target_field_name] = self.getConfigurationValue('map', data)[data[field]]
        except KeyError:
            pass
        return data

    def cast(self,data):
        """
        Field values in data dictionary will be cast to datatype set in ['type']
        This is just an alias function for the direct call to the castTo{DataType} method.

        @param data: dictionary
        @return: data: dictionary
        """
        try:
            return self.typecast_switch[self.getConfigurationValue('type'), data](data)
        except:
            pass

    def castToInteger(self,data):
        """
       ['source-fields'] values in data dictionary will be cast to integer.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source_fields', data):
            try:
                data[field] = int(data[field])
            except ValueError:
                data[field] = 0
            except KeyError:
                pass
        return data

    def castToFloat(self,data):
        """
        ['source-fields'] values in data dictionary will be cast to float.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source_fields', data):
            try:
                data[field] = float(data[field])
            except ValueError:
                data[field] = 0.0
            except KeyError:
                pass
        return data

    def castToString(self,data):
        """
        ['source-fields'] values in data dictionary will be cast to string.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source_fields', data):
            try:
                data[field] = str(data[field])
            except ValueError:
                data[field] = ""
            except KeyError:
                   pass
        return data

    def castToBoolean(self,data):
        """
        ['source-fields'] values in data dictionary will be cast to boolean.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source_fields', data):
            try:
                data[field] = bool(data[field])
            except ValueError:
                data[field] = False
            except KeyError:
                pass
        return data

    def anonymize(self, data):
        """
        Alias function for hash.
        """
        return self.hash(data)

    def hash(self,data):
        """
        ['source-fields'] values in data dictionary will hashed with hash algorithm set in configuration.

        @param data: dictionary
        @return: data: dictionary
        """
        for idx, field in enumerate(self.getConfigurationValue('source_fields', data)):
            target_fieldname = field if not self.getConfigurationValue('target_fields', data) else self.getConfigurationValue('target_fields', data)[idx]
            try:
                data[target_fieldname] = getattr(hashlib, self.getConfigurationValue('algorithm', data))(data[field]).hexdigest()
            except:
                pass
        return data