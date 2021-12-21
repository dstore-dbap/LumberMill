# -*- coding: utf-8 -*-
import hashlib
import random
import re
import os
import sys

from lumbermill.BaseThreadedModule import BaseThreadedModule
from lumbermill.utils.Decorators import ModuleDocstringParser
from lumbermill.utils.DictUtils import cloneDefaultDict


@ModuleDocstringParser
class Field(BaseThreadedModule):
    """
    Simple module to insert/delete/change field values.

    Configuration templates:

    # Keep all fields listed in source_fields, discard all others.
    - modify.Field:
       action: keep                     # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Discard all fields listed in source_fields.
    - modify.Field:
       action: delete                   # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Concat all fields listed in source_fields.
    - modify.Field:
       action: concat                   # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       target_field:                    # <type: string; is: required>
       receivers:
        - NextModule

    # Convert all fields to lowercase.
    - modify.Field:
       action: lower                    # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       target_fields:                    # <type: string; is: optional>
       receivers:
        - NextModule

    # Convert all fields to uppercase.
    - modify.Field:
       action: upper                    # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       target_fields:                    # <type: string; is: optional>
       receivers:
        - NextModule

    # Insert a new field with "target_field" name and "value" as new value.
    - modify.Field:
       action: insert                   # <type: string; is: required>
       target_field:                    # <type: string; is: required>
       value:                           # <type: string; is: required>
       receivers:
        - NextModule

    # Slice field values.
    - modify.Field:
       action: slice                    # <type: string; is: required>
       start:                           # <default: 0; type: None||integer; is: optional>
       end:                             # <default: None; type: None||integer; is: optional>
       source_field:                    # <type: string; is: required>
       target_field:                    # <type: string; is: required>
       receivers:
        - NextModule

    # Replace field values matching string "old" in data dictionary with "new".
    - modify.Field:
       action: string_replace           # <type: string; is: required>
       source_field:                    # <type: string; is: required>
       old:                             # <type: string; is: required>
       new:                             # <type: string; is: required>
       max:                             # <default: -1; type: integer; is: optional>
       receivers:
        - NextModule

    # Replace field values in data dictionary with self.getConfigurationValue['with'].
    - modify.Field:
       action: replace                  # <type: string; is: required>
       source_field:                    # <type: string; is: required>
       regex: ['<[^>]*>', 're.MULTILINE | re.DOTALL'] # <type: list; is: required>
       with:                            # <type: string; is: required>
       receivers:
        - NextModule

    # Rename a field.
    - modify.Field:
       action: rename                   # <type: string; is: required>
       source_field:                    # <type: string; is: required>
       target_field:                    # <type: string; is: required>
       receivers:
        - NextModule

    # Rename a field by regex. Pythons re.sub method is used.
    - modify.Field:
       action: rename_regex             # <type: string; is: required>
       regex:                           # <type: string; is: required>
       source_field:                    # <default: None; type: None||string; is: optional>
       regex:                           # <type: string; is: required>
       replace:                         # <type: string; is: required>
       recursive:                       # <default: True; type: boolean; is: optional>
       receivers:
        - NextModule

    # Rename a field by replace.
    - modify.Field:
       action: rename_replace           # <type: string; is: required>
       old:                             # <type: string; is: required>
       new:                             # <type: string; is: required>
       source_field:                    # <default: None; type: None||string; is: optional>
       recursive:                       # <default: True; type: boolean; is: optional>
       receivers:
        - NextModule

    # Map a field value.
    - modify.Field:
       action: map                      # <type: string; is: required>
       source_field:                    # <type: string; is: required>
       map:                             # <type: dictionary; is: required>
       target_field:                    # <default: "$(source_field)_mapped"; type: string; is: optional>
       keep_unmappable:                 # <default: False; type: boolean; is: optional>
       receivers:
        - NextModule

    # Split source field to target fields based on key value pairs.
    - modify.Field:
       action: key_value                # <type: string; is: required>
       line_separator:                  # <type: string; is: required>
       kv_separator:                    # <type: string; is: required>
       source_field:                    # <type: list; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       prefix:                          # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule

    # Split source field to target fields based on key value pairs using regex.
    - modify.Field:
       action: key_value_regex          # <type: string; is: required>
       regex:                           # <type: string; is: required>
       source_field:                    # <type: list; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       prefix:                          # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule

    # Split source field to array at separator.
    - modify.Field:
       action: split                    # <type: string; is: required>
       separator:                       # <type: string; is: required>
       source_field:                    # <type: list; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule

    # Strip whitespaces from source field.
    - modify.Field:
       action: strip                    # <type: string; is: required>
       source_field:                    # <type: string; is: required>
       target_field:                    # <default: None; type: None||string; is: optional>
       receivers:
        - NextModule

    # Merge source fields to target field as list.
    - modify.Field:
       action: merge                    # <type: string; is: required>
       target_field:                    # <type: string; is: reuired>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Merge source field to target field as string.
    - modify.Field:
       action: join                     # <type: string; is: required>
       source_field:                    # <type: string; is: required>
       target_field:                    # <type: string; is: required>
       separator:                       # <type: string; is: required>
       receivers:
        - NextModule

    # Cast field values to integer.
    - modify.Field:
       action: cast_to_int              # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Cast field values to float.
    - modify.Field:
       action: cast_to_float            # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Cast field values to string.
    - modify.Field:
       action: cast_to_str              # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Cast field values to boolean.
    - modify.Field:
       action: cast_to_bool             # <type: string; is: required>
       source_fields:                   # <type: list; is: required>
       receivers:
        - NextModule

    # Create a hash from a field value.
    # If target_fields is provided, it should have the same length as source_fields.
    # If target_fields is not provided, source_fields will be replaced with the hashed value.
    # Hash algorithm can be any of the in hashlib supported algorithms.
    - modify.Field:
       action: hash                     # <type: string; is: required>
       algorithm:                       # <default: "md5"; type: string; is: optional>
       salt:                            # <default: None; type: None||string; is: optional>
       source_fields:                   # <type: list; is: required>
       target_fields:                   # <default: []; type: list; is: optional>
       receivers:
        - NextModule
"""

    module_type = "modifier"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseThreadedModule.configure(self, configuration)
        # Set defaults
        self.typecast_switch = { 'int': self.cast_to_int,
                                 'integer': self.cast_to_int,
                                 'float': self.cast_to_float,
                                 'str': self.cast_to_str,
                                 'string': self.cast_to_str,
                                 'bool': self.cast_to_bool,
                                 'boolean': self.cast_to_bool,
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
                    self.lumbermill.shutDown()
            try:
                self.regex = re.compile(regex_pattern, regex_options)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, etype, evalue))
                self.lumbermill.shutDown()
        self.source_field = self.getConfigurationValue('source_field') if "source_field" in self.configuration_data else []
        self.source_fields = self.getConfigurationValue('source_fields') if "source_fields" in self.configuration_data else []
        self.target_field = self.getConfigurationValue('target_field') if "target_field" in self.configuration_data else []
        self.target_fields = self.getConfigurationValue('target_fields') if "target_fields" in self.configuration_data else []
        # Get action specific method
        try:
            self.handleEvent = getattr(self, "%s" % self.action)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("ModifyFields action called that does not exist: %s. Exception: %s, Error: %s" % (self.action, etype, evalue))
            self.lumbermill.shutDown()
        # Call action specific configure method.
        if "configure_%s_action" % self.action in dir(self):
            getattr(self, "configure_%s_action" % self.action)(configuration)


    def configure_slice_action(self, configuration):
        self.slice_start = self.getConfigurationValue('start')
        self.slice_end = self.getConfigurationValue('end')

    def configure_rename_replace_action(self, configuration):
        self.recursive = self.getConfigurationValue('recursive')
        self.old = self.getConfigurationValue('old')
        self.new = self.getConfigurationValue('new')

    def configure_rename_regex_action(self, configuration):
        self.recursive = self.getConfigurationValue('recursive')
        self.regex = re.compile(self.getConfigurationValue('regex'))
        self.replace = self.getConfigurationValue('replace')

    def configure_split_action(self, configuration):
        if 'separator' in configuration:
            self.separator = self.getConfigurationValue('separator')
            self.logger.info(self.separator)
        else:
            self.handleEvent = getattr(self, "split_list")

    def configure_key_value_action(self, configuration):
        self.line_separator = self.getConfigurationValue('line_separator')
        self.kv_separator = self.getConfigurationValue('kv_separator')
        self.prefix = self.getConfigurationValue('prefix')

    def configure_key_value_regex_action(self, configuration):
        self.prefix = self.getConfigurationValue('prefix')

    def configure_join_action(self, configuration):
        self.separator = self.getConfigurationValue('separator')

    def configure_hash_action(self, configuration):
        # Import murmur hashlib if configured.
        self.salt = self.getConfigurationValue('salt') if self.getConfigurationValue('salt') else ""
        self.algorithm = self.getConfigurationValue('algorithm')
        if self.algorithm == "murmur":
            try:
                import mmh3
                self.hash_func = mmh3.hash
            except ImportError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Exception: %s, Error: %s" % (etype, evalue))
                self.lumbermill.shutDown()
        else:
            try:
                self.hashlib_func = getattr(hashlib, self.algorithm)
            except ImportError:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("Exception: %s, Error: %s" % (etype, evalue))
                self.lumbermill.shutDown()
                return
            self.hash_func = self.hashlibFunc

    def getStartMessage(self):
        """
        Return the module name.
        """
        source = self.source_field if self.source_field else self.source_fields
        target = self.target_field if self.target_field else self.target_fields
        if not source:
            return "%s: %s" % (self.action, target)
        elif not target:
            return "%s: %s" % (self.action, source)
        else:
            return "%s: %s => %s" % (self.action, source, target)

    def hashlibFunc(self, string):
        return self.hashlib_func(string).hexdigest()

    def __handleEvent(self, event):
        try:
            event = self.event_handler(event)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("ModifyFields action %s threw an error. Exception: %s, Error: %s" % (self.action, etype, evalue))
            self.lumbermill.shutDown()
        yield event

    def keep(self, event):
        """
        Field names not listed in self.configuration_data['source_fields'] will be deleted from data dictionary.

        @param event: dictionary
        @yields: event: dictionary
        """
        fields_to_del = set(event).difference(self.source_fields)
        for field in fields_to_del:
            # Do not delete internal event information.
            if field == 'lumbermill':
                continue
            event.pop(field, None)
        yield event

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
        @yields: event: dictionary
        """
        for field in self.source_fields:
            event.pop(field, None)
        yield event

    def insert(self, event):
        """
        Insert a new field with a given value.

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            event[self.target_field] = event[self.getConfigurationValue('value')]
        except KeyError:
            event[self.target_field] = self.getConfigurationValue('value', event)
        yield event

    def concat(self, event):
        """
        Field names listed in ['source_fields'] will be concatenated to a new string.
        The result will be stored in ['target_field']

        @param event: dictionary
        @yields: event: dictionary
        """
        concat_str = ""
        for field in self.source_fields:
            try:
                concat_str = "%s%s" % (concat_str,event[field])
            except KeyError:
                pass
        event[self.target_field] = concat_str
        yield event

    def lower(self, event):
        """
        Field names listed in ['source_fields'] will be converted to a lowercase.
        The result will be stored in ['target_field']

        @param event: dictionary
        @yields: event: dictionary
        """
        for idx, field in enumerate(self.source_fields):
            if self.target_fields:
                event[self.target_fields[idx]] = event[field].lower()
            else:
                event[field] = event[field].lower()
        yield event

    def upper(self, event):
        """
        Field names listed in ['source_fields'] will be converted to a uppercase.
        The result will be stored in ['target_field']

        @param event: dictionary
        @yields: event: dictionary
        """
        for idx, field in enumerate(self.source_fields):
            if self.target_fields:
                event[self.target_fields[idx]] = event[field].upper()
            else:
                event[field] = event[field].upper()
        yield event

    def slice(self, event):
        """
        Slice a field value to given parameters.

        :param event: dictionary
        :yields event: dictionary
        """
        try:
            event[self.target_field] = event[self.source_field][self.slice_start:self.slice_end]
        except KeyError:
            pass
        yield event

    def replace(self, event):
        """
        Field value in data dictionary will be replaced with ['with']

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            event[self.source_field] = self.regex.sub(self.getConfigurationValue('with', event), event[self.source_field])
        except KeyError:
            pass
        yield event

    def rename(self, event):
        """
        Field name ['from'] in data dictionary will be renamed to ['to']

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            event[self.target_field] = event.pop(self.source_field)
        except KeyError:
            pass
        yield event

    def rename_regex(self, event):
        if self.source_field:
            try:
                dict_to_scan = event[self.source_field]
            except KeyError:
                yield event
        else:
            dict_to_scan = event
        self._rename_regex_recursive(dict_to_scan)
        yield event

    def _rename_regex_recursive(self, dict_to_scan):
        fields_to_rename = {}
        for field_name, field_value in dict_to_scan.items():
            new_field_name = self.regex.sub(self.replace, field_name)
            if field_name != new_field_name:
                fields_to_rename[field_name] = new_field_name
            if self.recursive and isinstance(field_value, dict):
                self._rename_regex_recursive(field_value)
        for old_field_name, new_field_name in fields_to_rename.items():
            dict_to_scan[new_field_name] = dict_to_scan.pop(old_field_name)

    def rename_replace(self, event):
        self.event = event
        if self.source_field:
            try:
                dict_to_scan = event[self.source_field]
            except KeyError:
                yield event
        else:
            dict_to_scan = event
        self._rename_replace_recursive(dict_to_scan)
        yield event

    def _rename_replace_recursive(self, dict_to_scan):
        fields_to_rename = {}
        for field_name, field_value in dict_to_scan.items():
            new_field_name = field_name.replace(self.old, self.new)
            if field_name != new_field_name:
                fields_to_rename[field_name] = new_field_name
            if self.recursive and isinstance(field_value, dict):
                self._rename_replace_recursive(field_value)
        for old_field_name, new_field_name in fields_to_rename.items():
            dict_to_scan[new_field_name] = dict_to_scan.pop(old_field_name)

    def string_replace(self, event):
        """
        Field value matching string in data dictionary will be replace with new.

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            event[self.source_field] = event[self.source_field].replace(self.getConfigurationValue('old', event), self.getConfigurationValue('new', event), self.getConfigurationValue('max'))
        except KeyError:
            pass
        yield event

    def map(self, event):
        """
        Field values in data dictionary will be mapped to ['with'][data[field]].
        By default, the target field is ${fieldname}_mapped and can be overwritten by config
        value "target_field"

        Useful e.g. to map http status codes to human readable status codes.
        @param event: dictionary
        @yields: event: dictionary
        """
        target_field = self.target_field if self.target_field else "%s_mapped" % self.source_field
        try:
            event[target_field] = self.getConfigurationValue('map', event)[event[self.source_field]]
        except KeyError:
            if self.getConfigurationValue('keep_unmappable'):
                event[target_field] = event[self.source_field]
            else:
                pass
        yield event

    def key_value(self, event):
        """
        Split source field to target fields based on key value pairs.

        - modify.Field:
          action: key_value                           # <type: string; is: required>
          kv_separator:                               # <type: string; is: required>
          line_separator:                             # <default: None; type: None||string; is: required>
          source_field:                               # <type: list; is: required>
          target_field:                               # <default: None; type: None||string; is: optional>
          prefix:                                     # <default: None; type: None||string; is: optional>
          receivers:
            - NextModule

        @param event: dictionary
        @yields: event: dictionary
        """
        if self.line_separator:
            kv_dict = {}
            for kv in event[self.source_field].split(self.line_separator):
                try:
                    kv_dict.update(dict([tuple(kv.split(self.kv_separator))]))
                except ValueError:
                    pass
        else:
            kv_dict = event[self.source_field].split(self.kv_separator)
        if self.prefix:
            kv_dict = dict(map(lambda key, value: ("%s%s" % (self.prefix, str(key)), value), kv_dict.items()))
        if self.target_field:
            event[self.target_field] = kv_dict
        else:
            event.update(kv_dict)
        yield event


    def key_value_regex(self, event):
        """
        Split source field to target fields based on key value pairs.

        - modify.Field:
          action: key_value_regex                     # <type: string; is: required>
          regex:                                      # <type: string; is: required>
          source_field:                               # <type: list; is: required>
          target_field:                               # <default: None; type: None||string; is: optional>
          prefix:                                     # <default: None; type: None||string; is: optional>
          receivers:
            - NextModule

        # ([^=&?]+)[=]([^&=?]+)

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            kv_dict = dict(re.findall(self.regex, event[self.source_field]))
        except:
            yield event
        if self.prefix:
            kv_dict = dict(map(lambda key, value: ("%s%s" % (self.prefix, str(key)), value), kv_dict.items()))
        if self.target_field:
            event[self.target_field] = kv_dict
        else:
            event.update(kv_dict)
        yield event


    def split(self, event):
        """
        Split source field to array at separator.

        - modify.Field:
          action: split                               # <type: string; is: required>
          separator:                                  # <type: string; is: required>
          source_field:                               # <type: list; is: required>
          target_field:                               # <default: None; type: None||string; is: optional>
          receivers:
            - NextModule

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            values = event[self.source_field].split(self.separator)
        except:
            yield event
        target_field = self.target_field if self.target_field else self.source_field
        event[target_field] = values
        yield event

    def split_list(self, event):
        """
        Split source field list to multiple events. The new events will be clones of the original one,
        with the source list items as new payload.

        - modify.Field:
          action: split                               # <type: string; is: required>
          source_field:                               # <type: list; is: required>
          target_field:                               # <default: None; type: None||string; is: optional>
          receivers:
            - NextModule

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            values = event[self.source_field]
        except:
            yield event
        target_field = self.target_field if self.target_field else self.source_field
        for value in values:
            new_event = cloneDefaultDict(event)
            new_event.pop(self.source_field, None)
            new_event[target_field] = value
            yield new_event

    def strip(self, event):
        """
        Strip whitespaces from string.

        - modify.Field:
          action: strip                               # <type: string; is: required>
          source_field:                               # <type: list; is: required>
          target_field:                               # <default: None; type: None||string; is: optional>
          receivers:
            - NextModule

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            value = event[self.source_field].strip()
        except:
            yield event
        target_field = self.target_field if self.target_field else self.source_field
        event[target_field] = value
        yield event

    def merge(self, event):
        """
        Merge source fields to target field as list.

        @param event: dictionary
        @yields: event: dictionary
        """
        merged_fields = []
        for field in self.source_fields:
            try:
                merged_fields.append(event[field])
            except:
                pass
        event[self.target_field] = merged_fields
        yield event

    def join(self, event):
        """
        Join source field to target field as string.

        @param event: dictionary
        @yields: event: dictionary
        """
        #event.update({self.getConfigurationValue('target_field'): separator.join(fields)})
        try:
            event[self.target_field] = self.separator.join(event[self.source_field])
        except:
            pass
        yield event

    def cast(self, event):
        """
        Field values in data dictionary will be cast to datatype set in ['type']
        This is just an alias function for the direct call to the castTo{DataType} method.

        @param event: dictionary
        @yields: event: dictionary
        """
        try:
            yield self.typecast_switch[self.getConfigurationValue('type'), event](event)
        except:
            pass

    def cast_to_int(self, event):
        """
       ['source_fields'] values in data dictionary will be cast to integer.

        @param event: dictionary
        @yields: event: dictionary
        """
        for field in self.source_fields:
            try:
                event[field] = int(float(event[field]))
            except ValueError:
                event[field] = 0
            except KeyError:
                pass
        yield event

    def cast_to_float(self, event):
        """
        ['source_fields'] values in data dictionary will be cast to float.

        @param event: dictionary
        @yields: event: dictionary
        """
        for field in self.source_fields:
            try:
                event[field] = float(event[field])
            except ValueError:
                event[field] = 0
            except KeyError:
                pass
        yield event

    def cast_to_str(self, event):
        """
        ['source_fields'] values in data dictionary will be cast to string.

        @param event: dictionary
        @yields: event: dictionary
        """
        for field in self.source_fields:
            try:
                event[field] = str(event[field])
            except ValueError:
                event[field] = ""
            except KeyError:
                pass
        yield event

    def cast_to_bool(self, event):
        """
        ['source_fields'] values in data dictionary will be cast to boolean.

        @param event: dictionary
        @yields: event: dictionary
        """
        for field in self.source_fields:
            try:
                event[field] = bool(event[field])
            except ValueError:
                event[field] = False
            except KeyError:
                pass
        yield event

    def hash(self, event):
        """
        ['source_fields'] values in data dictionary will hashed with hash algorithm set in configuration.

        @param event: dictionary
        @yields: event: dictionary
        """
        for idx, field in enumerate(self.source_fields):
            target_fieldname = field if not self.target_fields else self.target_fields[idx]
            try:
                event[target_fieldname] = self.hash_func(("%s%s" % (self.salt, event[field])).encode('utf-8'))
            except:
                pass
        yield event
