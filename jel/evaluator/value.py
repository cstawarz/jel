from __future__ import division, print_function, unicode_literals
from abc import ABCMeta, abstractmethod


# This is a trick to avoid using Python 3's non-backwards compatible
# metaclass declaration syntax.  The class name is converted to str
# because Python 2.7 won't accept unicode.
_Value = ABCMeta(str('_Value'), (object,), {})
_Value.__module__ = __name__


class Value(_Value):

    @abstractmethod
    def __bool__(self):
        pass


class Null(Value):
    pass


class Boolean(Value):
    pass


class Number(Value):
    pass


class String(Value):
    pass


class List(Value):
    pass


class Dictionary(Value):
    pass
