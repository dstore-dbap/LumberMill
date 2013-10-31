# -*- coding: utf-8 -*-
import ast

def getDefaultDataDict(dict={}):
    default_dict = { "received_from": False, 
                     "data": "",
                     "markers": [] }
    default_dict.update(dict)
    return default_dict

def compileStringToConditionalObject(condition_as_string, mapping):
    """
    Parse a condition passed in as string.

    Example:

    condition_as_string = "matched = VirtualHostName == 'www.gambolutty.com'"
    mapping = "data['%s']"

     will be parsed and compiled to:
     matched = data['VirtualHostName'] == "www.gambolutty.com"
    """
    transformer = AstTransformer(mapping)
    try:
        # Build a complete expression from filter.
        conditional_ast = ast.parse(condition_as_string)
        conditional_ast = transformer.visit(conditional_ast)
        conditional = compile(conditional_ast, '<string>', 'exec')
        return conditional
    except:
        return False

class AstTransformer(ast.NodeTransformer):
    def __init__(self, mapping="%s"):
        ast.NodeTransformer.__init__(self)
        self.mapping = mapping

    def visit_Name(self, node):
        # ignore "matched" variable
        if node.id in ["matched", "dependency", "True", "False"]:
            return node
        #new_node = ast.parse(ast.parse('data["%s"]' % node.id)).body[0].value
#        if node.id != "dependency":
#            print self.mapping % node.id
        new_node = ast.parse(ast.parse(self.mapping % node.id)).body[0].value
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