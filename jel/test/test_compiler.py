from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager
import unittest

from ..compiler import Compiler
from ..lexer import Lexer
from ..parser import Parser


class CompilerTestMixin(object):

    def setUp(self):
        def error_logger(*info):
            self.fail('unexpected error in input: %r' % info)
            
        l = self.lexer_class(error_logger)
        p = self.parser_class(l.tokens, error_logger)
        lexer = l.build()
        parser = p.build()
        self.compiler = self.compiler_class()

        @contextmanager
        def compile_wrapper(s):
            lexer.lineno = 1  # Reset lineno
            self.ops = collections.deque(
                self.compiler.compile(parser.parse(s, lexer=lexer))
                )
            yield
            self.assertEqual(0, len(self.ops))

        self.compile = compile_wrapper

    def assertOp(self, op_name, lineno, lexpos, *args):
        op = self.ops.popleft()
        self.assertEqual(self.compiler.op_codes[op_name], op[0])
        self.assertEqual(lineno, op[1])
        self.assertEqual(lexpos, op[2])
        if args:
            self.assertEqual(args, op[3])
        else:
            return op[3]


class TestCompiler(CompilerTestMixin, unittest.TestCase):

    lexer_class = Lexer
    parser_class = Parser
    compiler_class = Compiler

    def test_identifier_expr(self):
        with self.compile('foo'):
            self.assertOp('LOAD_NAME', 1, 0, 'foo')

    def test_null_literal_expr(self):
        with self.compile('null'):
            self.assertOp('LOAD_CONST', 1, 0, None)

    def test_boolean_literal_expr(self):
        def test_bool(expr, value):
            with self.compile(expr):
                args = self.assertOp('LOAD_CONST', 1, 0)
                self.assertEqual(1, len(args))
                self.assertIsInstance(args[0], bool)
                self.assertEqual(value, args[0])

        test_bool('true', True)
        test_bool('false', False)

    def test_number_literal_expr(self):
        def test_num(expr, value, tag=None):
            with self.compile(expr):
                args = self.assertOp('LOAD_CONST', 1, 0)
                self.assertEqual(2, len(args))
                self.assertIsInstance(args[0], float)
                self.assertEqual(value, args[0])
                self.assertEqual(tag, args[1])

        test_num('2', 2.0)
        test_num('1.5abc', 1.5, 'abc')

    def test_string_literal_expr(self):
        with self.compile('"foo"'):
            self.assertOp('LOAD_CONST', 1, 0, 'foo')

    def test_array_literal_expr(self):
        with self.compile('[]'):
            self.assertOp('BUILD_ARRAY', 1, 0, 0)

        with self.compile('[a, b, c]'):
            self.assertOp('LOAD_NAME', 1, 1, 'a')
            self.assertOp('LOAD_NAME', 1, 4, 'b')
            self.assertOp('LOAD_NAME', 1, 7, 'c')
            self.assertOp('BUILD_ARRAY', 1, 0, 3)
