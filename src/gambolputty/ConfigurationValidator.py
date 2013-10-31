# -*- coding: utf-8 -*-
import types
import Utils

class ConfigurationValidator():
    """
    Validate a module instance based on the configuration meta data retrieved from the docstring via the ModuleDocstringParser.

    The docstring should contain patterns like:
    ...
    target-field: 'my_timestamp' # <default: '@timestamp'; type: string; is: optional>
    ...

    Where:
    - target_field ist the configuration key
    - default: sets a standard value
    - type: sets the variable type
    - is: sets whether the parameter needs to be provided or not.
      Here a simple conditional syntax is supported, e.g.
      is: optional if other_key_name is False elsa required
    """

    typenames_to_type = {'None': types.NoneType,
                         'Boolean': types.BooleanType,
                         'Bool': types.BooleanType,
                         'Integer': types.IntType,
                         'Int': types.IntType,
                         'Float': types.FloatType,
                         'Str': types.StringType,
                         'String': types.StringType,
                         'Unicode': types.UnicodeType,
                         'Tuple': types.TupleType,
                         'List': types.ListType,
                         'Dictionary': types.DictType,
                         'Dict': types.DictType}

    def validateModuleInstance(self, moduleInstance):
        result = []
        if not hasattr(moduleInstance, 'configuration_metadata'):
            return result
        # Check if the live configuration provides a key that is not documented in modules docstring.
        config_keys_not_in_docstring = set(moduleInstance.configuration_data.keys()) - set(moduleInstance.configuration_metadata.keys())
        if config_keys_not_in_docstring:
            keys = []
            for key in config_keys_not_in_docstring:
                keys.append(key)
            error_msg = "%s: Found unknown configuration keys: %s. Please check module documentation." % (moduleInstance.__class__.__name__, keys)
            result.append(error_msg)
            return result
        for configuration_key, configuration_metadata in moduleInstance.configuration_metadata.iteritems():
            config_value = moduleInstance.getConfigurationValue(configuration_key)
            config_value_datatype = type(config_value)
            # Check for required parameter.
            if 'is' in configuration_metadata:
                dependency = configuration_metadata['is']
                edits = [('optional', '"optional"'), ('required', '"required"')]
                for search, replace in edits:
                    dependency = dependency.replace(search, replace)
                try:
                    exec(Utils.compileStringToConditionalObject("dependency = %s" % dependency, 'moduleInstance.getConfigurationValue("%s")'))
                except TypeError, e:
                    error_msg = "%s: Could not parse '%s'. Error: %s" % (moduleInstance.__class__.__name__, e, configuration_key)
                    result.append(error_msg)
                if dependency == 'required' and not config_value:
                    error_msg = "%s: '%s' not configured but is required. Please check module documentation." % (moduleInstance.__class__.__name__, configuration_key)
                    result.append(error_msg)
                    continue
            # Check for value type
            allowed_datatypes = []
            if 'type' in configuration_metadata:
                for allowed_datatypes_as_string in configuration_metadata['type']:
                    try:
                        allowed_datatypes.append(self.typenames_to_type[allowed_datatypes_as_string.title()])
                    except KeyError:
                        error_msg = "%s: Docstring config setting for '%s' has unknown datatype '%s'. Supported datatypes: %s" % (moduleInstance.__class__.__name__, configuration_key, allowed_datatypes_as_string.title(), self.typenames_to_type.keys())
                        result.append(error_msg)
                if config_value_datatype not in allowed_datatypes:
                    error_msg = "%s: '%s' not of correct datatype. Is: %s, should be: %s" % (moduleInstance.__class__.__name__, configuration_key, config_value_datatype, allowed_datatypes)
                    result.append(error_msg)
        return result


