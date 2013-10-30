# -*- coding: utf-8 -*-
import ast

def getDefaultDataDict(dict={}):
    default_dict = { "received_from": False, 
                     "data": "",
                     "markers": [] }
    default_dict.update(dict)
    return default_dict

def compileAstConditionalFilterObject(filter_as_string):
    """
    Parse a simple queue filter to an ast and replace key names with the actual values of the
    data dictionary.

    Example:
     ...
     - filter: VirtualHostName == "www.gambolutty.com"
     ...

     will be parsed and compiled to:
     matched = True if data['VirtualHostName'] == "www.gambolutty.com" else False
    """
    transformer = AstTransformer()
    try:
        # Build a complete expression from filter.
        conditional_ast = ast.parse("matched = %s" % filter_as_string)
        conditional_ast = transformer.visit(conditional_ast)
        conditional = compile(conditional_ast, '<string>', 'exec')
        return conditional
    except:
        return False

class AstTransformer(ast.NodeTransformer):
    def visit_Name(self, node):
        # ignore "matched" variable
        if node.id == "matched":
            return node
        new_node = ast.parse(ast.parse('data["%s"]' % node.id)).body[0].value
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
