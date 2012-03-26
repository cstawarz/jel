from __future__ import division, print_function, unicode_literals
import unittest

from ..evaluator.value import Value, UnsupportedOperation


class TestValue(unittest.TestCase):

    def test_abstract_methods(self):
        self.assertRaises(TypeError, Value)

        def no_args(_self):
            pass
        def one_arg(_self, _arg):
            pass
        
        bases = []
        def test_meth(name, imp):
            cls = type(str('Missing' + name), (Value,), {name: imp})
            self.assertRaises(TypeError, cls)
            bases.append(cls)

        test_meth('__bool__', no_args)
        test_meth('__eq__', one_arg)

        all_meths = type(str('AllMeths'), tuple(bases), {})
        all_meths()

    def test_default_implementations(self):
        class MyValue(Value):
            def __bool__(self):
                return super(MyValue, self).__bool__()
            def __eq__(self, other):
                return super(MyValue, self).__eq__(other)

        v = MyValue()
        v2 = MyValue()
        
        with self.assertRaises(NotImplementedError):
            bool(v)
        with self.assertRaises(UnsupportedOperation):
            v == v2
        with self.assertRaises(UnsupportedOperation):
            v != v2
        with self.assertRaises(UnsupportedOperation):
            v < v2
        with self.assertRaises(UnsupportedOperation):
            v <= v2
        with self.assertRaises(UnsupportedOperation):
            v > v2
        with self.assertRaises(UnsupportedOperation):
            v >= v2
        with self.assertRaises(UnsupportedOperation):
            v2 in v
        with self.assertRaises(UnsupportedOperation):
            v2 not in v
        with self.assertRaises(UnsupportedOperation):
            v + v2
        with self.assertRaises(UnsupportedOperation):
            v - v2
        with self.assertRaises(UnsupportedOperation):
            v * v2
        with self.assertRaises(UnsupportedOperation):
            # Evaluate without future imports, so that __div__ (rather
            # than __truediv__) is called under Python 2.7
            eval(compile('v / v2', '<string>', 'eval', 0, True),
                 globals(),
                 locals())
        with self.assertRaises(UnsupportedOperation):
            v % v2
        with self.assertRaises(UnsupportedOperation):
            +v
        with self.assertRaises(UnsupportedOperation):
            -v
        with self.assertRaises(UnsupportedOperation):
            v ** v2
        with self.assertRaises(UnsupportedOperation):
            v[v2]
        with self.assertRaises(UnsupportedOperation):
            v.getattribute(v2)
