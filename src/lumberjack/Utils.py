import re

dynamic_var_regex = re.compile('\$\{(.*?)\}')

def getDefaultDataDict(dict):
    default_dict = { "received_from": False, 
                     "data": False, 
                     "markers": [] }
    default_dict.update(dict)
    return default_dict

def replaceDynamicVarNameInString(string, data_dictionary):
    for match in dynamic_var_regex.finditer(string):
        replace_string = match.group(0)
        field_name = match.group(1)
        start, end = match.span(1)
        if field_name not in data_dictionary:
            raise KeyError
            return string
        string = "%s%s%s" % (string[:start-2], data_dictionary[field_name], string[end+1:])
    return string

class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'