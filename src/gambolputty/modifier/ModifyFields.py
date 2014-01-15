# -*- coding: utf-8 -*-
import sys
import re
import hashlib
import BaseModule
from Decorators import ModuleDocstringParser

@ModuleDocstringParser
class ModifyFields(BaseModule.BaseModule):
    """
    Simple module to add/delete/change field values.

    Configuration examples:

    # Keep all fields listed in source_fields, discard all others.
    - module: ModifyFields
      action: keep                                # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Discard all fields listed in source_fields.
    - module: ModifyFields
      action: delete                              # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Concat all fields listed in source_fields.
    - module: ModifyFields
      action: concat                              # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      target_field: field5                        # <type: string; is: required>
      receivers:
        - NextModule

    # Insert a new field with "target_field" name an "value" as new value.
    - module: ModifyFields
      action: insert                              # <type: string; is: required>
      target_field: "New field"                   # <type: string; is: required>
      value: "%(field1)s - %(field2)s are new."  # <type: string; is: required>
      receivers:
        - NextModule

    # Replace field values in data dictionary with self.getConfigurationValue['with'].
    - module: ModifyFields
      action: replace                             # <type: string; is: required>
      source_field: field1                        # <type: string; is: required>
      regex: ['<[^>]*>', 're.MULTILINE | re.DOTALL'] # <type: list; is: required>
      with: 'Johann Gambolputty'                  # <type: string; is: required>
      receivers:
        - NextModule

    # Map a field value.
    - module: ModifyFields
      action: map                                 # <type: string; is: required>
      source_field: http_status                   # <type: string; is: required>
      map: {100: 'Continue', 200: 'OK', ... }     # <type: dictionary; is: required>
      target_field: http_status                   # <default: "%(source_field)s_mapped"; type: string; is: optional>
      receivers:
        - NextModule

    # Cast field values to integer.
    - module: ModifyFields
      action: castToInteger                       # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to float.
    - module: ModifyFields
      action: castToFloat                         # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to string.
    - module: ModifyFields
      action: castToString                        # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Cast field values to boolean.
    - module: ModifyFields
      action: castToBoolean                       # <type: string; is: required>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      receivers:
        - NextModule

    # Create a hash from a field value.
    # If target_fields is provided, it should have the same length as source_fields.
    # If target_fields is not provided, source_fields will be replaced with the hashed value.
    # Hash algorithm can be any of the in hashlib supported algorithms.
    - module: ModifyFields
      action: hash                                # <type: string; is: required>
      algorithm: sha1                             # <default: "md5"; type: string; is: optional;>
      source_fields: [field1, field2, ... ]       # <type: list; is: required>
      target_fields: [f1, f2, ... ]               # <default: []; type: list; is: optional>
      receivers:
        - NextModule
"""

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
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

    def handleEvent(self, event):
        try:
            event = getattr(self, "%s" % self.action)(event)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("ModifyFields action called that does not exist: %s. Exception: %s, Error: %s" % (self.action, etype, evalue))
            self.gp.shutDown()
        yield event

    def keep(self,event):
        """
        Field names not listed in self.configuration_data['source_fields'] will be deleted from data dictionary.

        @param event: dictionary
        @return: event: dictionary
        """
        fields_to_del = set(event).difference(self.getConfigurationValue('source_fields', event))
        for field in fields_to_del:
            # Do not delete internal event information.
            if field == 'gambolputty':
                continue
            event.pop(field, None)
        return event

    def delete(self, event):
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

        @param event: dictionary
        @return: event: dictionary
        """
        for field in self.getConfigurationValue('source_fields', event):
            event.pop(field, None)
        return event

    def insert(self, event):
        """
        Insert a new field with a given value.

        @param event: dictionary
        @return: event: dictionary
        """
        event[self.getConfigurationValue('target_field', event)] = self.getConfigurationValue('value', event)
        return event

    def concat(self, event):
        """
        Field names listed in ['source_fields'] will be concatenated to a new string.
        The result will be stored in ['target_field']

        @param event: dictionary
        @return: event: dictionary
        """
        concat_str = ""
        for field in self.getConfigurationValue('source_fields', event):
            try:
                concat_str = "%s%s" % (concat_str,event[field])
            except KeyError:
                pass
        event[self.getConfigurationValue('target_field', event)] = concat_str
        return event

    def replace(self, event):
        """
        Field value in data dictionary will be replace with ['with']

        @param event: dictionary
        @return: event: dictionary
        """
        field = self.getConfigurationValue('source_field', event)
        try:
            event[field] = self.regex.sub(self.getConfigurationValue('with', event), event[field])
        except KeyError:
            pass
        return event

    def map(self, event):
        """
        Field values in data dictionary will be mapped to ['with'][data[field]].
        By default, the target field is ${fieldname}_mapped and can be overwritten by config
        value "target_field"

        Useful e.g. to map http status codes to human readable status codes.
        @param event: dictionary
        @return: event: dictionary
        """
        field = self.getConfigurationValue('source_field', event)
        target_field_name = self.getConfigurationValue('target_field', event) if 'target_field' in self.configuration_data else "%s_mapped" % field
        try:
            event[target_field_name] = self.getConfigurationValue('map', event)[event[field]]
        except KeyError:
            pass
        return event

    def cast(self,event):
        """
        Field values in data dictionary will be cast to datatype set in ['type']
        This is just an alias function for the direct call to the castTo{DataType} method.

        @param event: dictionary
        @return: event: dictionary
        """
        try:
            return self.typecast_switch[self.getConfigurationValue('type'), event](event)
        except:
            pass

    def castToInteger(self,event):
        """
       ['source_fields'] values in data dictionary will be cast to integer.

        @param event: dictionary
        @return: event: dictionary
        """
        for field in self.getConfigurationValue('source_fields', event):
            try:
                event[field] = int(event[field])
            except ValueError:
                event[field] = 0
            except KeyError:
                pass
        return event

    def castToFloat(self,event):
        """
        ['source_fields'] values in data dictionary will be cast to float.

        @param event: dictionary
        @return: event: dictionary
        """
        for field in self.getConfigurationValue('source_fields', event):
            try:
                event[field] = float(event[field])
            except ValueError:
                event[field] = 0.0
            except KeyError:
                pass
        return event

    def castToString(self,event):
        """
        ['source_fields'] values in data dictionary will be cast to string.

        @param event: dictionary
        @return: event: dictionary
        """
        for field in self.getConfigurationValue('source_fields', event):
            try:
                event[field] = str(event[field])
            except ValueError:
                event[field] = ""
            except KeyError:
                   pass
        return event

    def castToBoolean(self,event):
        """
        ['source_fields'] values in data dictionary will be cast to boolean.

        @param event: dictionary
        @return: event: dictionary
        """
        for field in self.getConfigurationValue('source_fields', event):
            try:
                event[field] = bool(event[field])
            except ValueError:
                event[field] = False
            except KeyError:
                pass
        return event

    def anonymize(self, data):
        """
        Alias function for hash.
        """
        return self.hash(data)

    def hash(self,event):
        """
        ['source_fields'] values in data dictionary will hashed with hash algorithm set in configuration.

        @param event: dictionary
        @return: event: dictionary
        """
        for idx, field in enumerate(self.getConfigurationValue('source_fields', event)):
            target_fieldname = field if not self.getConfigurationValue('target_fields', event) else self.getConfigurationValue('target_fields', event)[idx]
            try:
                event[target_fieldname] = getattr(hashlib, self.getConfigurationValue('algorithm', event))(event[field]).hexdigest()
            except:
                pass
        return event