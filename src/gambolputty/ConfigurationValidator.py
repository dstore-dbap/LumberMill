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
      is: optional if other_key_name is Fa
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

    default_module_config_keys = ('module', 'id', 'filter', 'receivers', 'pool_size', 'queue_size', 'mp_queue_buffer_size','redis_store', 'redis_key', 'redis_ttl')

    def validateModuleInstance(self, moduleInstance):
        result = []
        # The ModifyFields module is an exception as it provides more than one configuration.
        # This needs to be taken into account when testing for required configuration values.
        # At the moment, I just skip this module until I have a good idea on how to tackle this.
        if not hasattr(moduleInstance, 'configuration_metadata') or moduleInstance.__class__.__name__ in ['ModifyFields']:
            return result
        # Check for pool_size > 1 in single threaded/processed modules.
        if 'pool_size' in moduleInstance.configuration_data and moduleInstance.getConfigurationValue('pool_size') > 1 and moduleInstance.can_run_parallel is False:
            error_msg = "%s: 'pool_size' has invalid value. Is: %s but the module can only run in one thread/process." % (moduleInstance.__class__.__name__, moduleInstance.getConfigurationValue('pool_size'))
            result.append(error_msg)
        # Check if the live configuration provides a key that is not documented in modules docstring.
        config_keys_not_in_docstring = set(moduleInstance.configuration_data.keys()) - set(moduleInstance.configuration_metadata.keys()) - set(self.default_module_config_keys)
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
                    #print "dependency = %s" % dependency
                    exec Utils.compileStringToConditionalObject("dependency = %s" % dependency, 'moduleInstance.getConfigurationValue("%s")')
                except TypeError, e:
                    error_msg = "%s: Could not parse dependency %s in '%s'. Error: %s" % (dependency, moduleInstance.__class__.__name__, e, configuration_key)
                    result.append(error_msg)
                if dependency == 'required' and not config_value:
                    error_msg = "%s: '%s' not configured but is required. Please check module documentation." % (moduleInstance.__class__.__name__, configuration_key)
                    result.append(error_msg)
                    continue
            # Check for value type.
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
            # Check for value restrictions.
            if 'values' in configuration_metadata:
                if config_value not in configuration_metadata['values']:
                    error_msg = "%s: '%s' has invalid value. Is: %s, should be on of: %s" % (moduleInstance.__class__.__name__, configuration_key, config_value, configuration_metadata['values'])
                    result.append(error_msg)
        return result


