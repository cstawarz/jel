from __future__ import division, print_function, unicode_literals
import abc
import sys

from . import UnsupportedOperation


# This is a trick to avoid using Python 3's non-backwards compatible
# metaclass declaration syntax.  The class name is converted to str
# because Python 2.7 won't accept unicode.
_Value = abc.ABCMeta(str('_Value'), (object,), {})
_Value.__module__ = __name__


class Value(_Value):

    def _unsupported_op(self):
        raise UnsupportedOperation

    def _unsupported_binop(self, other):
        raise UnsupportedOperation

    def __bool__(self):
        raise NotImplementedError

    if sys.version_info.major < 3:
        def __nonzero__(self):
            return self.__bool__()

    def __eq__(self, other):
        return self._unsupported_binop(other)

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self._unsupported_binop(other)

    def __le__(self, other):
        return (self < other) or (self == other)

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)

    def __contains__(self, item):
        return self._unsupported_op()

    def __add__(self, other):
        return self._unsupported_binop(other)

    def __sub__(self, other):
        return self._unsupported_binop(other)

    def __mul__(self, other):
        return self._unsupported_binop(other)

    def __truediv__(self, other):
        return self._unsupported_binop(other)

    if sys.version_info.major < 3:
        def __div__(self, other):
            return self.__truediv__(other)

    def __mod__(self, other):
        return self._unsupported_binop(other)

    def __pos__(self):
        return self._unsupported_op()

    def __neg__(self):
        return self._unsupported_op()

    def __pow__(self, other):
        return self._unsupported_binop(other)

    def __len__(self):
        return self._unsupported_op()

    def __getitem__(self, key):
        return self._unsupported_op()

    def getattribute(self, name):
        return self._unsupported_op()


class Null(Value):

    def __bool__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, Null)


class Boolean(Value):

    def __init__(self, val):
        self.value = bool(val)

    def __bool__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, Boolean) and (bool(self) == bool(other))


class Number(Value):

    def __init__(self, val):
        self.value = val

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return isinstance(other, Number) and (self.value == other.value)


class String(Value):
    pass


class List(Value):
    pass


class Dictionary(Value):
    pass
