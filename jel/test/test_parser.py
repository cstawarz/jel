from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager
import decimal
import unittest

from .. import ast
from ..lexer import JELLexer
from ..parser import JELParser


class TestJELParser(unittest.TestCase):

    def setUp(self):
        self.errors = collections.deque()
        def error_logger(*info):
            self.errors.append(info)
            
        jl = JELLexer(error_logger)
        jp = JELParser(jl.tokens, error_logger)
        self.lexer = jl.build()
        self.parser = jp.build()

        @contextmanager
        def parse_wrapper(s):
            yield self.parser.parse(s, lexer=self.lexer)
            if self.errors:
                self.fail('input contained unexpected errors: ' +
                          ', '.join(repr(e) for e in self.errors))

        self.parse = parse_wrapper

    def test_identifier_expr(self):
        with self.parse('foo') as p:
            self.assertIsInstance(p, ast.IdentifierExpr)
            self.assertEqual('foo', p.value)

    def test_null_literal_expr(self):
        with self.parse('null') as p:
            self.assertIsInstance(p, ast.NullLiteralExpr)

    def test_true_literal_expr(self):
        with self.parse('true') as p:
            self.assertIsInstance(p, ast.BooleanLiteralExpr)
            self.assertIs(True, p.value)

    def test_false_literal_expr(self):
        with self.parse('false') as p:
            self.assertIsInstance(p, ast.BooleanLiteralExpr)
            self.assertIs(False, p.value)

    def test_number_literal_expr(self):
        with self.parse('123') as p:
            self.assertIsInstance(p, ast.NumberLiteralExpr)
            self.assertIsInstance(p.value, decimal.Decimal)
            self.assertEqual('123', str(p.value))
            self.assertEqual(123, int(p.value))
            self.assertIsNone(p.unit)
            
        with self.parse('1.230E-45ms') as p:
            self.assertIsInstance(p, ast.NumberLiteralExpr)
            self.assertIsInstance(p.value, decimal.Decimal)
            self.assertEqual('1.230E-45', str(p.value))
            self.assertEqual(1.23e-45, float(p.value))
            self.assertEqual('ms', p.unit)
