from __future__ import division, print_function, unicode_literals
import unittest

from ..evaluator import UnsupportedOperation
from ..evaluator import value


class TestValue(unittest.TestCase):

    def test_default_implementations(self):
        v = value.Value()
        v2 = value.Value()
        
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
            len(v)
        with self.assertRaises(UnsupportedOperation):
            v[v2]
        with self.assertRaises(UnsupportedOperation):
            v.getattribute(v2)

    def test_implied_comparisons(self):
        class MyInt(value.Value):
            def __init__(self, val):
                self.val = val
            def __eq__(self, other):
                assert type(other) is type(self)
                return (self.val == other.val)

        i1 = MyInt(12)
        i2 = MyInt(12)
        i3 = MyInt(34)

        self.assertTrue(i1 == i2)
        self.assertFalse(i1 == i3)

        # __eq__ implies __ne__
        self.assertFalse(i1 != i2)
        self.assertTrue(i1 != i3)

        # ...but not any ordering comparison
        with self.assertRaises(UnsupportedOperation):
            i1 < i2
        with self.assertRaises(UnsupportedOperation):
            i1 <= i2
        with self.assertRaises(UnsupportedOperation):
            i1 > i2
        with self.assertRaises(UnsupportedOperation):
            i1 >= i2
        
        class MyInt2(MyInt):
            def __lt__(self, other):
                assert type(other) is type(self)
                return (self.val < other.val)

        i4 = MyInt2(12)
        i5 = MyInt2(12)
        i6 = MyInt2(34)

        # __lt__ implies all other ordering comparisons
        self.assertFalse(i4 < i5)
        self.assertTrue(i4 < i6)
        self.assertTrue(i4 <= i5)
        self.assertTrue(i4 <= i6)
        self.assertFalse(i4 > i5)
        self.assertFalse(i4 > i6)
        self.assertTrue(i4 >= i5)
        self.assertFalse(i4 >= i6)

        # ...but __contains__ stands alone
        with self.assertRaises(UnsupportedOperation):
            i5 in i4
        
        class MyInt3(MyInt2):
            def __contains__(self, item):
                assert type(item) is type(self)
                return (self.val % item.val == 0)

        i7 = MyInt3(9)
        i8 = MyInt3(3)
        i9 = MyInt3(4)

        # __contains__ implements both 'in' and 'not in'
        self.assertTrue(i8 in i7)
        self.assertFalse(i9 in i7)
        self.assertFalse(i8 not in i7)
        self.assertTrue(i9 not in i7)

    def test_null(self):
        n = value.Null
        
        self.assertFalse(bool(n))
        
        self.assertTrue(n == n)
        self.assertFalse(n == value.Value())

    def test_boolean(self):
        t = value.True_
        f = value.False_

        self.assertTrue(bool(t))
        self.assertFalse(bool(f))

        self.assertTrue(t == t)
        self.assertTrue(f == f)
        
        self.assertFalse(t == f)
        self.assertFalse(t == value.Value())

    def test_number(self):
        n1 = value.Number(1.2)
        n2 = value.Number(0.0)
        n3 = value.Number(-3.4)
        
        self.assertEqual(1.2, n1.value)
        self.assertEqual(0.0, n2.value)
        self.assertEqual(-3.4, n3.value)

        self.assertTrue(bool(n1))
        self.assertFalse(bool(n2))
        self.assertTrue(bool(n3))

        self.assertTrue(n1 == n1)
        self.assertTrue(n1 == value.Number(1.2))
        self.assertFalse(n1 == n2)
        self.assertFalse(n1 == value.Value())
