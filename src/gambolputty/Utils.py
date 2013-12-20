# -*- coding: utf-8 -*-
import ast
import sys
import logging
import collections
import __builtin__
import Utils
from pprint import pprint

def getDefaultEventDict(dict={}):
    default_dict = { "event_type": "Unknown",
                     "received_from": False,
                     "data": "",
                     "markers": [] }
    default_dict['__id'] = id(default_dict)
    default_dict.update(dict)
    return default_dict

def compileStringToConditionalObject(condition_as_string, mapping):
    """
    Parse a condition passed in as string.

    Example:

    condition_as_string = "matched = VirtualHostName == 'www.gambolutty.com'", mapping = "event['%s']"

     will be parsed and compiled to:
     matched = event['VirtualHostName'] == "www.gambolutty.com"
     matched = event.get('VirtualHostName', False) == "www.gambolutty.com"
    """
    try:
        # Build a complete expression from filter.
        transformer = AstTransformer(mapping)
        conditional_ast = ast.parse(condition_as_string)
        conditional_ast = transformer.visit(conditional_ast)
        conditional = compile(conditional_ast, '<string>', 'exec')
        return conditional
    except :
        etype, evalue, etb = sys.exc_info()
        logging.getLogger("compileStringToConditionalObject").error("%sCould not compile conditional %s. Exception: %s, Error: %s.%s" % (Utils.AnsiColors.WARNING, condition_as_string, etype, evalue, Utils.AnsiColors.ENDC))
        return False

class AstTransformer(ast.NodeTransformer):
    def __init__(self, mapping="%s"):
        ast.NodeTransformer.__init__(self)
        self.mapping = mapping

    def visit_Name(self, node):
        # ignore builtins and some other vars
        ignore_nodes = dir(__builtin__)
        ignore_nodes.extend(["matched", "dependency"])
        if node.id in ignore_nodes:
            return node
        #pprint(ast.dump(ast.parse(self.mapping % node.id)))
        new_node = ast.parse(self.mapping % node.id).body[0].value
        return new_node

class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LIGHTBLUE = '\033[34m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
