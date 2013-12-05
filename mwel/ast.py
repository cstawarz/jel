from __future__ import division, print_function, unicode_literals

from jel.ast import *


class Module(AST):

    _fields = ('statements',)


class Stmt(AST):
    pass


class ChainedAssignmentStmt(Stmt):

    _fields = ('targets', 'value')


class AugmentedAssignmentStmt(Stmt):

    _fields = ('target', 'op', 'value')


class LocalStmt(Stmt):

    _fields = ('name', 'value')


class CallStmt(Stmt):

    _fields = ('head', 'local_names', 'body', 'tail')


class FunctionStmt(Stmt):

    _fields = ('name', 'args', 'body', 'local')


class ReturnStmt(Stmt):

    _fields = ('value',)


class AttributeReferenceExpr(Expr):

    _fields = ('target', 'name')


class FunctionExpr(Expr):

    _fields = ('args', 'body')


class ArrayItemRange(AST):

    _fields = ('start', 'stop', 'step')
