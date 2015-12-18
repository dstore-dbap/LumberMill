# -*- coding: utf-8 -*-
import sys
import ast
import logging
import datetime
import re

GP_DYNAMIC_VAL_REGEX = re.compile('[\$|%]\((.*?)\)')
GP_DYNAMIC_VAL_REGEX_WITH_TYPES = re.compile('[\$|%]\((.*?)\)(-?\d*[-\.\*]?\d*[sdf]?)')
PYTHON_DYNAMIC_VAL_REGEX = re.compile('%\((.*?)\)')
DYNAMIC_VALUE_REPLACE_PATTERN = r"%(\1)"


# Conditional imports for python2/3
try:
    import __builtin__ as builtins
except ImportError:
    import builtins

def replaceVarsAndCompileString(code_as_string, replacement):
    """
    Parse a string to python code.

    This function will parse the code and replaces all variable names with the replacment.

    Example:

    code_as_string = "matched = VirtualHostName == 'www.gambolutty.com'", replacement = "event['%s']"

     will be parsed and compiled to:
     matched = event['VirtualHostName'] == "www.gambolutty.com"
    """
    try:
        code_ast = ast.parse(code_as_string)
    except:
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not parse code %s. Exception: %s, Error: %s." % (code_as_string, etype, evalue))
        return False
    transformer = ReplaceVars(replacement)
    transformer.visit(code_ast)
    try:
        code = compile(code_ast, '<ast>', 'exec')
    except:
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not compile code %s. Exception: %s, Error: %s." % (code_as_string, etype, evalue))
        return False
    return code


class ReplaceVars(ast.NodeTransformer):
    def __init__(self, replacement):
        ast.NodeTransformer.__init__(self)
        self.replacement = replacement

    def visit_Name(self, node):
        # ignore builtins and some other vars
        ignore_nodes = dir(builtins)
        ignore_nodes.extend(["matched", "dependency", "event"])
        if node.id in ignore_nodes:
            return node
        #pprint.pprint(self.mapping % node.id)
        #pprint.pprint(ast.dump(ast.parse(self.mapping % node.id)))
        new_node = ast.parse(self.replacement % node.id).body[0].value
        return new_node

def parseDynamicValuesInString(value):
    """
    Parse a string and replace the configuration notation for dynamic values with pythons notation.
    E.g:
    filter: $(lumbermill.source_module) == 'TcpServer'
    parsed:
    filter: %(lumbermill.source_module)s == 'TcpServer'
    """
    matches = GP_DYNAMIC_VAL_REGEX_WITH_TYPES.search(value)
    if not matches:
        return value
    # Get custom format if set.
    # Defaults to string.
    if matches.group(2):
        replace_pattern = DYNAMIC_VALUE_REPLACE_PATTERN + matches.group(2)
    else:
        replace_pattern = DYNAMIC_VALUE_REPLACE_PATTERN + "s"
    return GP_DYNAMIC_VAL_REGEX_WITH_TYPES.sub(replace_pattern, value)

def parseDynamicValuesInList(value_list, contains_dynamic_value):
    # Copy list since we might change it during iteration.
    value_list_copy = list(value_list)
    for idx, value in enumerate(value_list_copy):
        if isinstance(value, list):
            parseDynamicValuesInList(value_list[idx], contains_dynamic_value)
        elif isinstance(value, dict):
            parseDynamicValuesInDict(value_list[idx], contains_dynamic_value)
        elif isinstance(value, basestring):
            new_value = parseDynamicValuesInString(value)
            if new_value == value:
                continue
            contains_dynamic_value.append(True)
            value_list[idx] = new_value

def parseDynamicValuesInDict(value_dict, contains_dynamic_value):
    # Copy dict since we might change it during iteration.
    value_dict_copy = value_dict.copy()
    for key, value in value_dict_copy.items():
        new_key = key
        if(isinstance(key, basestring)):
            new_key = parseDynamicValuesInString(key)
        if isinstance(value, list):
            parseDynamicValuesInList(value_dict[key], contains_dynamic_value)
        elif isinstance(value, dict):
            parseDynamicValuesInDict(value_dict[key], contains_dynamic_value)
        elif isinstance(value, basestring):
            new_value = parseDynamicValuesInString(value)
            if key == new_key and value == new_value:
                continue
            if new_key != key:
                del value_dict[key]
            contains_dynamic_value.append(True)
            value_dict[new_key] = new_value

def parseDynamicValue(value):
    contains_dynamic_value = []
    if isinstance(value, list):
        parseDynamicValuesInList(value, contains_dynamic_value)
    elif isinstance(value, dict):
        parseDynamicValuesInDict(value, contains_dynamic_value)
    elif isinstance(value, basestring):
        new_value = parseDynamicValuesInString(value)
        if value != new_value:
            value = new_value
            contains_dynamic_value.append(True)
    return {'value': value, 'contains_dynamic_value': bool(contains_dynamic_value)}

def mapDynamicValueInString(value, mapping_dict, use_strftime=False):
    try:
        if use_strftime:
            if sys.platform .startswith('linux'):
                value = datetime.datetime.utcnow().strftime(value)
            # On linux strftime will not remove non-supported format characters.
            # On other platforms this might be different.
            # So we need to take care that other dynamic value notations, which also use the percent sign syntax,
            # are renamed prior to using strftime and renamed to original after strftime was applied.
            # This adds a considerable overhead in parsing.
            # @see: http://bugs.python.org/issue9811
            else:
                value = PYTHON_DYNAMIC_VAL_REGEX.sub(r"$(\1)", value)
                value = datetime.datetime.utcnow().strftime(value)
                value = GP_DYNAMIC_VAL_REGEX.sub(r"%(\1)", value)
        return value % mapping_dict # dot_dict_formatter.format(value, **mapping_dict)
    except KeyError:
        return value
    except (ValueError, TypeError):
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("mapDynamicValueInString").error("Mapping failed for %s. Mapping data: %s. Exception: %s, Error: %s." % (value, mapping_dict, etype, evalue))
        raise

def mapDynamicValueInList(value_list, mapping_dict, use_strftime=False):
    for idx, value in enumerate(value_list):
        if isinstance(value, list):
            mapDynamicValueInList(value, mapping_dict, use_strftime)
        elif isinstance(value, dict):
            mapDynamicValueInDict(value, mapping_dict, use_strftime)
        elif isinstance(value, basestring):
            new_value = mapDynamicValueInString(value, mapping_dict, use_strftime)
            if new_value == value:
                continue
            value_list[idx] = new_value

def mapDynamicValueInDict(value_dict, mapping_dict, use_strftime=False):
    for key, value in value_dict.items():
        new_key = key
        if(isinstance(key, basestring)):
            new_key = mapDynamicValueInString(key, mapping_dict, use_strftime)
        if isinstance(value, list):
            mapDynamicValueInList(value, mapping_dict, use_strftime)
        elif isinstance(value, dict):
            mapDynamicValueInDict(value, mapping_dict, use_strftime)
        elif isinstance(value, basestring):
            new_value = mapDynamicValueInString(value, mapping_dict, use_strftime)
            if key == new_key and value == new_value:
                continue
            value_dict[new_key] = new_value

def mapDynamicValue(value, mapping_dict={}, use_strftime=False):
    if isinstance(value, basestring):
        return mapDynamicValueInString(value, mapping_dict, use_strftime)
    if isinstance(value, list):
        mapDynamicValueInList(value, mapping_dict, use_strftime)
    elif isinstance(value, dict):
        mapDynamicValueInDict(value, mapping_dict, use_strftime)
    return value
