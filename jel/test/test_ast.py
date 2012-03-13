from __future__ import division, print_function, unicode_literals
import unittest

from .. import ast


class Node(ast.AST):

    _fields = ('foo', 'bar')


class DerivedNode(Node):
    pass


class OtherNode(ast.AST):
    pass


class TestAST(unittest.TestCase):

    def test_missing_field(self):
        with self.assertRaises(KeyError) as cm:
            Node(foo=1)
        self.assertEqual('bar', cm.exception.message)

    def test_invalid_field(self):
        with self.assertRaises(TypeError) as cm:
            DerivedNode(foo=1, bar=2, blah=3)
        self.assertEqual("DerivedNode has no field 'blah'",
                         cm.exception.message)

    def test_repr(self):
        self.assertEqual('Node(foo=1, bar=2)', repr(Node(foo=1, bar=2)))
        self.assertEqual('DerivedNode(foo=3, bar=4)',
                         repr(DerivedNode(foo=3, bar=4)))
        self.assertEqual('OtherNode()', repr(OtherNode()))

    def test_equality(self):
        n1 = Node(foo=1, bar=2)
        n2 = Node(foo=1, bar=2)
        n3 = Node(foo=1, bar=3)

        self.assertTrue(n1 == n1)
        self.assertTrue(n1 == n2)
        self.assertFalse(n1 == n3)

        self.assertFalse(n1 != n1)
        self.assertFalse(n1 != n2)
        self.assertTrue(n1 != n3)

        d = DerivedNode(foo=n1.foo, bar=n1.bar)
        self.assertEqual(n1.foo, d.foo)
        self.assertEqual(n1.bar, d.bar)
        
        self.assertFalse(n1 == d)
        self.assertFalse(d == n1)
        
        self.assertTrue(n1 != d)
        self.assertTrue(d != n1)

        o1 = OtherNode()
        o2 = OtherNode()

        self.assertTrue(o1 == o1)
        self.assertTrue(o1 == o2)
        self.assertFalse(o1 == n1)

        self.assertFalse(o1 != o1)
        self.assertFalse(o1 != o2)
        self.assertTrue(o1 != n1)
