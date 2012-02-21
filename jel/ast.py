from __future__ import division, print_function, unicode_literals


class AST(object):

    @property
    def _name(self):
        return type(self).__name__

    def __init__(self, **kwargs):
        for field in self._fields:
            setattr(self, field, kwargs.pop(field))
        if kwargs:
            raise TypeError('%s has no field %r' %
                            (self._name, kwargs.popitem()[0]))

    def __repr__(self):
        args = ', '.join('%s=%r' % (f, getattr(self, f)) for f in self._fields)
        return '%s(%s)' % (self._name, args)


class UnaryOpExpr(AST):

    _fields = ('op', 'operand')


class BinaryOpExpr(AST):

    _fields = ('op', 'operands')


class NumberLiteralExpr(AST):

    _fields = ('value',)
