from __future__ import division, print_function, unicode_literals

from jel.ast import *


class Module(AST):

    _fields = ('statements',)


class LocalStmt(AST):

    _fields = ('name', 'value')
