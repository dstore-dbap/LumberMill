import sys
import re
import BaseModule

class RegexParser(BaseModule.BaseModule):
    """Parse a string by named regular expressions.

    Configuration example:

    - module: RegexParser
      configuration:
        # Set marker if a regex matched
        mark-on-success: match
        # Set marker if no regex matched
        mark-on-failure: nomatch
        break_on_match: True
        field_extraction_patterns:
          httpd_access_log: ['(?P<httpd_access_log>.*)', 're.MULTILINE | re.DOTALL', 'findall']
        receivers:
          # Only messages that matched a regex will be send to this handler
          - ModuleContainer:
            filter-by-marker: match
          # Print out messages that did not match
          - StdOutHandler:
            filter-by-marker: nomatch
    """

    def setup(self):
        """
        Setup method to set default values.

        This method will be called by the GambolPutty main class after initializing the module
        and before the configure method of the module is called.
        """
        # Call parent setup method
        super(RegexParser, self).setup()
        # Set the default data field name that will be matched against the regex.
        self.configuration_data['source-fields'] = 'data'

    def configure(self, configuration):
        # Call parent configure method
        super(RegexParser, self).configure(configuration)
        # Set defaults
        supported_regex_match_types = ['search', 'findall']
        self.add_success_marker = True if 'mark-on-success' in configuration else False
        self.add_failure_marker = True if 'mark-on-failure' in configuration else False
        self.break_on_match = configuration['break-on-match'] if 'break-on-match' in configuration else True
        self.message_types = []
        self.fieldextraction_regexpressions = {}
        for message_type, regex_pattern in configuration['field-extraction-patterns'].items():
            regex_options = 0
            regex_match_type = 'search'
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
                # Regex match type the third (optional)
                try:
                    regex_match_type = i.next()
                except:
                    pass
            # Make sure regex_match_type is valid
            # At the moment only search and findall are supported
            if regex_match_type not in supported_regex_match_types:
                self.logger.error("RegEx error for match type %s. Only %s are supported." % (regex_options, supported_regex_match_types))
                self.shutDown()               
            try:
                regex = re.compile(regex_pattern, regex_options)
            except:
                etype, evalue, etb = sys.exc_info()
                self.logger.error("RegEx error for pattern %s. Exception: %s, Error: %s" % (regex_pattern, etype, evalue))
                self.shutDown()
            self.fieldextraction_regexpressions[message_type] = {'pattern': regex, 'match_type': regex_match_type}

    def handleData(self, data):
        """
        This method expects a syslog datagram.
        It might contain more then one message. We split at the newline char.
        """
        self.logger.debug("Received raw message: %s" % data)
        # Remove possible remaining syslog error code
        # i.e. message starts with <141>
        for fieldname in self.getConfigurationValue('source-fields', data):
            if fieldname not in data:
                continue
            try:
                if data[fieldname].index(">") <= 4:
                    data[fieldname] = data[fieldname][data[fieldname].index(">")+1:] + "\n"
            except:
                pass
            data = self.parseMessage(data, fieldname)
        return data
        
    def parseMessage(self, data, fieldname):
        """
        When a message type was successfully detected, extract the fields with to corresponding regex pattern
        """
        message = data[fieldname]
        matches_dict = False
        self.logger.debug("Input to parseMessage: %s" % message)
        for message_type, regex_data in self.fieldextraction_regexpressions.iteritems():
            matches_dict = {}
            if regex_data['match_type'] == 'search':
                matches = regex_data['pattern'].search(message);
                if matches:
                    matches_dict = matches.groupdict()
            elif regex_data['match_type'] == 'findall':
                for match in regex_data['pattern'].finditer(message):
                    for key, value in match.groupdict().iteritems():
                        try:
                            matches_dict[key].append(value)
                        except:
                            matches_dict[key] = [value]
            if matches_dict:
                data.update(matches_dict)
                data.update({'message_type': message_type})
                if self.add_success_marker:
                    data['markers'].append(self.getConfigurationValue('mark-on-success', data))
                if(self.break_on_match):
                    break
        if not matches_dict:
            if self.add_failure_marker:
                data['markers'].append(self.getConfigurationValue('mark-on-failure', data))
            self.logger.debug("Could not extract fields for message %s." % message);
            data.update({'message_type': 'unknown'})
        self.logger.debug("Output from parseMessage %s" % data)
        return data