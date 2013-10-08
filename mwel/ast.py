from __future__ import division, print_function, unicode_literals

from jel.ast import *


class Module(AST):

    _fields = ('statements',)


class ChainedAssignmentStmt(AST):

    _fields = ('targets', 'value')


class AugmentedAssignmentStmt(AST):

    _fields = ('target', 'op', 'value')


class LocalStmt(AST):

    _fields = ('name', 'value')
