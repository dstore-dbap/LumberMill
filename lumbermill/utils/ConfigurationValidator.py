# -*- coding: utf-8 -*-
import sys

from lumbermill.constants import TYPENAMES_TO_TYPE
from lumbermill.utils.DynamicValues import replaceVarsAndCompileString

if sys.hexversion > 0x03000000:
    pass
else:
    pass

yaml_valid_config_template = {
    'Global': {'types': [dict],
               'fields': {'workers': {'types': [int]}}},
    'Module': {'types': [dict,str],
               'fields': {'id': {'types': [str]},
                          'filter': {'types': [str]},
                          'add_fields': {'types': [dict]},
                          'delete_fields': {'types': [list]},
                          'event_type': {'types': [str]},
                          'receivers': {'types': [list]}}
               }
}

class ConfigurationValidator():
    """
    Validate a module instance based on the configuration meta data retrieved from the docstring via the ModuleDocstringParser.

    The docstring should contain patterns like:
    ...
    compression: 'zlib' # <default: 'gzip'; type: string; is: optional; values: [gzip, zlib]>
    ...

    Where:
    - target_field ist the configuration key
    - default: sets a standard value
    - type: sets the variable type
    - is: sets whether the parameter needs to be provided or not.
      Here a simple conditional syntax is supported, e.g.
      is: required if tls is True else optional
    - values (optional): sets a list of allowed values.
    """

    default_module_config_keys = ('module', 'id', 'filter', 'receivers', 'pool_size', 'queue_size', 'mp_queue_buffer_size','redis_store', 'redis_key', 'redis_ttl', 'add_fields', 'delete_fields', 'event_type')

    @classmethod
    def validateConfiguration(self, configuration_data):
        """
        Simple schema test for the global configuration.

        Only a very simple "schema" is checked here.
        Global configuration item and each module configuration item should at least adhere to the data pattern defined in
        yaml_valid_config_template. Module specific configuration checks will be done in validateModuleInstanceConfiguration.
        """
        configuration_errors = []
        for configuration_item in configuration_data:
            if type(configuration_item) is str:
                # Simple modules names are ok.
                continue
            elif type(configuration_item) is list:
                # List items in root configuraion are not allowed.
                error_msg = "'%s'(list) is not allowed here. Please check your configuration." % configuration_item
                configuration_errors.append(error_msg)
                continue
            elif type(configuration_item) is dict:
                for key, value in configuration_item.items():
                    mapped_key = 'Module' if key != 'Global' else key
                    item_configuration_errors = self.validateConfigurationItem(mapped_key, value, key)
                    for item_configuration_error in item_configuration_errors:
                        configuration_errors.append(item_configuration_error)
                continue
            else:
                error_msg = "'%s' is of invalid type %s. Please check your configuration." % (configuration_item, type(configuration_item))
                configuration_errors.append(error_msg)
        return configuration_errors

    @classmethod
    def validateConfigurationItem(self, item_name, item_value, path, template=yaml_valid_config_template):
        configuration_errors = []
        if item_name in template:
            item_template = template[item_name]
            if type(item_value) not in item_template['types']:
                error_msg = "'%s' not of correct datatype. Is: %s, should be: %s. Please check your configuration." % (path, type(item_value), item_template['types'])
                configuration_errors.append(error_msg)
            if type(item_value) is dict:
                for field_key, field_value in item_value.items():
                    field_path = "%s.%s" % (path, field_key)
                    try:
                        field_configuration_errors = self.validateConfigurationItem(field_key, field_value, field_path, template=item_template['types'])
                    except KeyError:
                        sys.exit()
                    for field_configuration_error in field_configuration_errors:
                        configuration_errors.append(field_configuration_error)
        return configuration_errors

    def validateModuleConfiguration(self, moduleInstance):
        result = []
        # The ModifyFields module is an exception as it provides more than one configuration.
        # This needs to be taken into account when testing for required configuration values.
        # At the moment, I just skip this module until I have a good idea on how to tackle this.
        if not hasattr(moduleInstance, 'configuration_metadata') or moduleInstance.__class__.__name__ in ['ModifyFields']:
            return result
        # Check for pool_size > 1 in single threaded/processed modules.
        if 'pool_size' in moduleInstance.configuration_data and moduleInstance.getConfigurationValue('pool_size') > 1 and moduleInstance.can_run_forked is False:
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
        for configuration_key, configuration_metadata in moduleInstance.configuration_metadata.items():
            config_value = moduleInstance.getConfigurationValue(configuration_key)
            config_value_datatype = type(config_value)
            # Check for required parameter.
            if 'is' in configuration_metadata:
                dependency = configuration_metadata['is']
                edits = [('optional', '"optional"'), ('required', '"required"')]
                for search, replace in edits:
                    dependency = dependency.replace(search, replace)
                try:
                    # TODO: Think of a better and more secure way to evaluate the dependencies.
                    exec(replaceVarsAndCompileString("dependency = %s" % dependency, 'moduleInstance.getConfigurationValue("%s")'))
                except TypeError:
                    etype, evalue, etb = sys.exc_info()
                    error_msg = "%s: Could not parse dependency %s in '%s'. Exception: %s, Error: %s." % (dependency, moduleInstance.__class__.__name__, etype, evalue, configuration_key)
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
                        allowed_datatypes.append(TYPENAMES_TO_TYPE[allowed_datatypes_as_string.title()])
                    except KeyError:
                        error_msg = "%s: Docstring config setting for '%s' has unknown datatype '%s'. Supported datatypes: %s" % (moduleInstance.__class__.__name__, configuration_key, allowed_datatypes_as_string.title(), TYPENAMES_TO_TYPE.keys())
                        result.append(error_msg)
                if config_value_datatype not in allowed_datatypes:
                    error_msg = "%s: '%s' not of correct datatype. Is: %s, should be: %s" % (moduleInstance.__class__.__name__, configuration_key, config_value_datatype, allowed_datatypes)
                    result.append(error_msg)
            # Check for value restrictions.
            if 'values' in configuration_metadata:
                if config_value not in configuration_metadata['values']:
                    error_msg = "%s: '%s' has invalid value. Is: %s, should be one of: %s" % (moduleInstance.__class__.__name__, configuration_key, config_value, configuration_metadata['values'])
                    result.append(error_msg)
        return result