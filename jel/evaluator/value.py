from __future__ import division, print_function, unicode_literals
from abc import ABCMeta, abstractmethod, abstractproperty
import sys

from . import UnsupportedOperation


################################################################################
#
# Abstract base classes
#
################################################################################


# This is a trick to avoid using Python 3's non-backwards compatible
# metaclass declaration syntax.  The class name is converted to str
# because Python 2.7 won't accept unicode.
_Value = ABCMeta(str('_Value'), (object,), {})
_Value.__module__ = __name__


class Value(_Value):

    def _unsupported_op(self):
        raise UnsupportedOperation

    def _unsupported_binop(self, other):
        raise UnsupportedOperation

    @abstractmethod
    def __bool__(self):
        raise NotImplementedError

    if sys.version_info.major < 3:
        def __nonzero__(self):
            return self.__bool__()

    @abstractmethod
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


class NullLike(Value):

    def __bool__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, NullLike)


class BooleanLike(Value):

    def __eq__(self, other):
        return isinstance(other, BooleanLike) and (bool(self) == bool(other))


class NumberLike(Value):

    @abstractproperty
    def value(self):
        raise NotImplementedError

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return isinstance(other, NumberLike) and (self.value == other.value)


class StringLike(Value):
    pass


class ListLike(Value):
    pass


class DictionaryLike(Value):
    pass


################################################################################
#
# Concrete derived classes
#
################################################################################


def singleton(cls):
    return cls()


Null = singleton(NullLike)


@singleton
class True_(BooleanLike):
    def __bool__(self):
        return True


@singleton
class False_(BooleanLike):
    def __bool__(self):
        return False


class Number(NumberLike):

    def __init__(self, val):
        self._val = val

    @property
    def value(self):
        return self._val
