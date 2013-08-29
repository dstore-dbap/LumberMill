import sys
import re
import BaseModule

class ModifyField(BaseModule.BaseModule):

    def configure(self, configuration):
        # Set defaults
        self.action = configuration['action'] if 'action' in configuration else 'delete'
        self.configuration = configuration
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
            self.logger.error("ModifyField action called that does not exist: %s. Exception: %s, Error: %s" % (self.action, etype, evalue))
            self.shutDown()
        return data
    
    def delete(self, data):
        try:
            del data[self.configuration['field']]
        except KeyError:
            pass
        return data
    
    def replaceStatic(self, data):
        try:
            data[self.configuration['field']] = self.regex.sub(self.configuration['with'], data[self.configuration['field']])
        except KeyError:
            pass
        return data

    def replaceDynamic(self, data):
        try:
            data[self.configuration['field']] = self.regex.sub(data[self.configuration['with']], data[self.configuration['field']])
        except KeyError:
            pass
        return data