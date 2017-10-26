# -*- coding: utf-8 -*-
from pyparsing import *

identifier = Word(alphas).setName('identifier')
literal = pyparsing.pyparsing_common.number

print("%s" % identifier.parseString("12"))