def getDefaultDataDict(dict):
    default_dict = { "received_from": False, 
                     "data": False, 
                     "markers": [] }
    default_dict.update(dict)
    return default_dict