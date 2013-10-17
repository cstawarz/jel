from __future__ import division, print_function, unicode_literals


class AST(object):

    _fields = ()

    @property
    def _name(self):
        return type(self).__name__

    def __init__(self, **kwargs):
        for field in self._fields:
            setattr(self, field, kwargs.pop(field))
        if kwargs:
            raise TypeError('%s has no field %r' %
                            (self._name, kwargs.popitem()[0]))

    def __eq__(self, other):
        return ((type(other) is type(self)) and
                all(getattr(self, field) == getattr(other, field)
                    for field in self._fields))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        args = ', '.join('%s=%r' % (f, getattr(self, f)) for f in self._fields)
        return '%s(%s)' % (self._name, args)


class Expr(AST):

    _parenthetic = False


class OrExpr(Expr):

    _fields = ('operands',)


class AndExpr(Expr):

    _fields = ('operands',)


class BinaryOpExpr(Expr):

    _fields = ('op', 'operands')


class UnaryOpExpr(Expr):

    _fields = ('op', 'operand')


class ComparisonExpr(Expr):

    _fields = ('ops', 'operands')


class CallExpr(Expr):

    _fields = ('target', 'args')


class SubscriptExpr(Expr):

    _fields = ('target', 'value')


class AttributeExpr(Expr):

    _fields = ('target', 'name')


class ObjectLiteralExpr(Expr):

    _fields = ('items',)


class ArrayLiteralExpr(Expr):

    _fields = ('items',)


class StringLiteralExpr(Expr):

    _fields = ('value',)


class NumberLiteralExpr(Expr):

    _fields = ('value', 'tag')


class BooleanLiteralExpr(Expr):

    _fields = ('value',)


class NullLiteralExpr(Expr):
    pass


class IdentifierExpr(Expr):

    _fields = ('value',)
