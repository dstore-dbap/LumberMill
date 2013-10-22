def getDefaultDataDict(dict={}):
    default_dict = { "received_from": False, 
                     "data": "",
                     "markers": [] }
    default_dict.update(dict)
    return default_dict

class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LIGHTBLUE = '\033[34m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'