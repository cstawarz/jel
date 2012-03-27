from __future__ import division, print_function, unicode_literals

from . import abc


def singleton(cls):
    return cls()


Null = singleton(abc.Null)


@singleton
class True_(abc.Boolean):
    def __bool__(self):
        return True


@singleton
class False_(abc.Boolean):
    def __bool__(self):
        return False


class Number(abc.Number):

    def __init__(self, val):
        self._val = val

    @property
    def value(self):
        return self._val
