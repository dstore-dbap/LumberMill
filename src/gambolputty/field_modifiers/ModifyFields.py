import sys
import re
import BaseModule

class ModifyFields(BaseModule.BaseModule):

    def setup(self):
        # Call parent setup method
        super(ModifyFields, self).setup()
        self.typecast_switch = { 'int': self.castToInteger,
                                 'integer': self.castToInteger,
                                 'float': self.castToFloat,
                                 'str': self.castToString,
                                 'string': self.castToString,
                                 'bool': self.castToBoolean,
                                 'boolean': self.castToBoolean,
                                }

    def configure(self, configuration):
        # Call parent configure method
        super(ModifyFields, self).configure(configuration)
        # Set defaults
        self.action = configuration['action'] if 'action' in configuration else 'delete'
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
                    self.shutDown()
            try:
                self.regex = re.compile(regex_pattern, regex_options)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, etype, evalue))
                self.shutDown()

    def handleData(self, data):
        try:
            data = self.__getattribute__("%s" % self.action)(data)
        except AttributeError:
            etype, evalue, etb = sys.exc_info()
            self.logger.error("ModifyFields action called that does not exist: %s. Exception: %s, Error: %s" % (self.action, etype, evalue))
            self.shutDown()
        return data

    def keep(self,data):
        """
        Field names not listed in self.configuration_data['source-fields'] will be deleted from data dictionary.

        @param data: dictionary
        @return: data: dictionary
        """
        fields_to_del = set(data).difference(self.getConfigurationValue('source-fields', data))
        for field in fields_to_del:
            data.pop(field, None)
        return data

    def delete(self, data):
        """
        Field names listed in self.configuration_data['source-fields'] will be deleted from data dictionary.

        @todo: pypy seems to handle simple tight loops better than
        - first building a set from data dictionary and
        - then get common keys from self.configuration_data['source-fields'] and data via intersection

        e.g.:
        fields_to_check = self.configuration_data['source-fields'].intersection(set(data))

        Still, if the field set is a large one, the above approach could be faster.

        This problem affects this and some more methods in this class.
        Maybe the code can be altered to take this into account.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            data.pop(field, None)
        return data

    def replace(self, data):
        """
        Field values in data dictionary will be replace with self.configuration_data['with']

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            try:
                data[field] = self.regex.sub(self.getConfigurationValue('with', data), data[field])
            except KeyError:
                pass
        return data

    def map(self, data):
        """
        Field values in data dictionary will be mapped to self.configuration_data['with'][data[field]]
        By default, the target field is ${fieldname}_mapped and can be overwritten by config
        value "target_field"

        Useful e.g. to map http status codes to human readable status codes.
        @param data: dictionary
        @return data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            target_field_name = self.getConfigurationValue('target-field', data) if 'target-field' in self.configuration_data else "%s_mapped" % field
            try:
                data[target_field_name] = self.getConfigurationValue('map', data)[data[field]]
            except KeyError:
                pass
        return data

    def cast(self,data):
        """
        Field values in data dictionary will be cast to datatype set in self.configuration_data['type']
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
        self.configuration_data['fields'] values in data dictionary will be cast to integer.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            try:
                data[field] = int(data[field])
            except ValueError:
                data[field] = 0
            except KeyError:
                pass
        return data

    def castToFloat(self,data):
        """
        self.configuration_data['fields'] values in data dictionary will be cast to float.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            try:
                data[field] = float(data[field])
            except ValueError:
                data[field] = 0.0
            except KeyError:
                pass
        return data

    def castToString(self,data):
        """
        self.configuration_data['fields'] values in data dictionary will be cast to string.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            try:
                data[field] = str(data[field])
            except ValueError:
                data[field] = ""
            except KeyError:
                   pass
        return data

    def castToBoolean(self,data):
        """
        self.configuration_data['fields'] values in data dictionary will be cast to boolean.

        @param data: dictionary
        @return: data: dictionary
        """
        for field in self.getConfigurationValue('source-fields', data):
            try:
                data[field] = bool(data[field])
            except ValueError:
                data[field] = False
            except KeyError:
                pass
        return data