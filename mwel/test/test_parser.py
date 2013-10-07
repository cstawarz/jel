from __future__ import division, print_function, unicode_literals
import unittest

from jel.test.test_parser import ParserTestMixin

from .. import ast
from ..lexer import Lexer
from ..parser import Parser


class TestParser(ParserTestMixin, unittest.TestCase):

    lexer_class = Lexer
    parser_class = Parser

    def test_empty_module(self):
        def test_module(src):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertIsInstance(p.statements, tuple)
                self.assertEqual(0, len(p.statements))

        test_module('')
        test_module('# This module is empty\n   \n')

    def test_nonempty_module(self):
        with self.parse('''
            # Not much to see here
            local foo = 1
            local bar = 2
            ''') as p:
            
            self.assertIsInstance(p, ast.Module)
            self.assertIsInstance(p.statements, tuple)
            self.assertEqual(2, len(p.statements))
            self.assertIsInstance(p.statements[0], ast.LocalStmt)
            self.assertIsInstance(p.statements[1], ast.LocalStmt)

    def test_local_stmt(self):
        with self.parse('local foo = 1') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            self.assertIsInstance(p, ast.LocalStmt)
            self.assertEqual('foo', p.name)
            self.assertEqual(self.one, p.value)

        with self.parse('local bar\n'):
            self.assertError(token='\n')
