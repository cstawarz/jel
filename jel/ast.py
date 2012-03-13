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


class UnaryOpExpr(AST):

    _fields = ('op', 'operand')


class BinaryOpExpr(AST):

    _fields = ('op', 'operands')


class _AtomicLiteralExpr(AST):

    _fields = ('value',)


class StringLiteralExpr(_AtomicLiteralExpr):
    pass


class NumberLiteralExpr(AST):

    _fields = ('value', 'unit')


class BooleanLiteralExpr(_AtomicLiteralExpr):
    pass


class NullLiteralExpr(AST):
    pass


class IdentifierExpr(_AtomicLiteralExpr):
    pass
