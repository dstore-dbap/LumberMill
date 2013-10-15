import sys
import re
import BaseModule

class RegexStringParser(BaseModule.BaseModule):
    """Parse a string by named regular expressions.

    Configuration example:

    - module: RegexStringParser
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

    def configure(self, configuration):
        # Call parent configure method
        super(RegexStringParser, self).configure(configuration)
        # Set defaults
        supported_regex_match_types = ['search', 'findall']
        # Set the data field name that will be matched against the regex.
        self.fieldname = configuration['field'] if 'field' in configuration else 'data'
        self.success_marker = configuration['mark-on-success'] if 'mark-on-success' in configuration else False
        self.failure_marker = configuration['mark-on-failure'] if 'mark-on-success' in configuration else False
        self.break_on_match = configuration['break_on_match'] if 'break_on_match' in configuration else True
        self.message_types = []
        self.fieldextraction_regexpressions = {}
        for message_type, regex_pattern in configuration['field_extraction_patterns'].items():
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
        try:
            if data[self.fieldname].index(">") <= 4:
                data[self.fieldname] = data[self.fieldname][data[self.fieldname].index(">")+1:] + "\n"
        except: 
            pass
        if data[self.fieldname].strip() == "":
            return
        return self.parseMessage(data)
        
    def parseMessage(self, data):
        """
        When a message type was successfully detected, extract the fields with to corresponding regex pattern
        """
        message = data[self.fieldname]
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
                if self.success_marker:
                    data['markers'].append(self.success_marker)
                if(self.break_on_match):
                    break
        if not matches_dict:
            if self.failure_marker:
                data['markers'].append(self.failure_marker)            
            self.logger.debug("Could not extract fields for message %s." % message);
            data.update({'message_type': 'unknown'})
        self.logger.debug("Output from parseMessage %s" % data)
        return data