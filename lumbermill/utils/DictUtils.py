# -*- coding: utf-8 -*-
import os
import random
import copy
from string import Formatter

from lumbermill.constants import MY_HOSTNAME


class KeyDotNotationDict(dict):
    """
    A dictionary that allows to access values via dot separated keys, e.g.:
    >>> my_dict = {"key1": {"key2": "value"}}
    >>> my_dict["key1.key2"]
    "value"
    """

    def __getitem__(self, key, item=None):
        item = item if item is not None else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(item, list):
                key = int(key)
            try:
                value = item.__getitem__(key)
            except (KeyError, IndexError, TypeError, AttributeError):
                raise KeyError(key)
            return value
        current_key, remaining_keys = key.split('.', 1)
        try:
            item = item.__getitem__(current_key)
        except TypeError:
            item = item.__getitem__(int(current_key))
        return self.__getitem__(remaining_keys, item)

    def __setitem__(self, key, value, item=None):
        item = item if item is not None else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(item, list):
                key = int(key)
            try:
                ret = item.__setitem__(key, value)
            except (KeyError, IndexError, TypeError, AttributeError):
                raise KeyError(key)
            return ret
        current_key, remaining_keys = key.split('.', 1)
        try:
            item = item.__getitem__(current_key)
        except TypeError:
            item = item.__getitem__(int(current_key))
        return self.__setitem__(remaining_keys, value, item)

    def __delitem__(self, key, item=None):
        item = item if item is not None else super(KeyDotNotationDict, self)
        if "." not in key:
            if isinstance(item, list):
                key = int(key)
            try:
                ret = item.__delitem__(key)
            except (KeyError, IndexError, TypeError, AttributeError):
                raise KeyError(key)
            return ret
        current_key, remaining_keys = key.split('.', 1)
        try:
            item = item.__getitem__(current_key)
        except TypeError:
            item = item.__getitem__(int(current_key))
        return self.__delitem__(remaining_keys, item)

    def __contains__(self, key, item=None):
        item = item if item is not None else super(KeyDotNotationDict, self)
        if "." not in key:
            try:
                value = item.__contains__(key)
            except (KeyError, IndexError, TypeError, AttributeError):
                raise KeyError(key)
            return value
        current_key, remaining_keys = key.split('.', 1)
        try:
            item = item.__getitem__(current_key)
            return self.__contains__(remaining_keys, item)
        except TypeError:
            item = item.__getitem__(int(current_key))
            return self.__contains__(remaining_keys, item)
        except KeyError:
            return False

    #def __del__(self, key):
    #    pass

    def __missing__(self, key):
        raise KeyError(key)

    def copy(self):
        new_dict = KeyDotNotationDict(copy.deepcopy(super(KeyDotNotationDict, self)))
        if "event_id" in new_dict.get("lumbermill", {}):
            new_dict['lumbermill']['event_id'] = "%032x%s" % (random.getrandbits(128), os.getpid())
        return new_dict

    def get(self, key, *args):
        try:
            return self.__getitem__(key)
        except (KeyError, IndexError) as e:
            # Try to return a default value for not existing dict keys.
            try:
                return args[0]
            except KeyError:
                raise e

    def __get(self, key, default, item=None):
        item = item if item else super(KeyDotNotationDict, self)
        if "." not in key:
            if not isinstance(item, list):
                return item.get(key, default)
            else:
                try:
                    return item[int(key)]
                except KeyError:
                    return default
        current_key, remaining_keys = key.split('.', 1)
        try:
            item = item.__getitem__(current_key)
            return self.get(remaining_keys, default, item)
        except KeyError:
            return default

    def pop(self, key, default=None, item=None):
        item = item if item else super(KeyDotNotationDict, self)
        if "." not in key:
            if not isinstance(item, list):
                return item.pop(key, default)
            else:
                try:
                    return item[int(key)]
                except KeyError:
                    return default
        current_key, remaining_keys = key.split('.', 1)
        try:
            try:
                item = item.__getitem__(current_key)
            except TypeError:
                item = item.__getitem__(int(current_key))
            return self.pop(remaining_keys, default, item)
        except KeyError:
            return default

class DotDictFormatter(Formatter):
    try:  # deal with Py 2 & 3 difference
        NUMERICS = (int, long)
    except NameError:
        NUMERICS = int

    def get_field(self, field_name, args, kwargs):
        first, rest = field_name._formatter_field_name_split()
        obj = self.get_value(first, args, kwargs)
        # loop through the rest of the field_name, doing
        #  getattr or getitem as needed
        for is_attr, i in rest:
            obj = obj[i]
        return obj, first

def mergeNestedDicts(a, b, path=None):
    "Merges a with b. If b provides same key as a, b takes precendence."
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                mergeNestedDicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                continue # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

def getDefaultEventDict(dict={}, caller_class_name='', received_from="Unknown", event_type="Unknown"):
    default_dict = { "data": "",
                     "lumbermill": {
                         'pid': os.getpid(),
                         'event_type': event_type,
                         'event_id': "%032x%s" % (random.getrandbits(128), os.getpid()),
                         'source_module': caller_class_name,
                         'received_from': received_from,
                         'received_by': MY_HOSTNAME
                     }
                }
    default_dict.update(dict)
    default_dict = KeyDotNotationDict(default_dict)
    return default_dict

def cloneDefaultDict(orig_dict):
    cloned_dict = copy.deepcopy(orig_dict)
    cloned_dict['lumbermill']['event_id'] = "%032x%s" % (random.getrandbits(128), os.getpid())
    #try:
    #    cloned_dict['lumbermill']['event_id'] = "%032x%s" % (random.getrandbits(128), os.getpid())
    #except KeyError:
    #    pass
    return cloned_dict
