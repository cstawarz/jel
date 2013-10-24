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
        self.ops = []

        def compile_wrapper(s):
            lexer.lineno = 1  # Reset lineno
            return self.assertOpList(
                self.compiler.compile(parser.parse(s, lexer=lexer))
                )

        self.compile = compile_wrapper

    def assertOpList(self, ops):
        self.assertIsInstance(ops, list)

        @contextmanager
        def ensure_ops_consumed():
            self.ops.append(collections.deque(ops))
            yield
            self.assertEqual(0, len(self.ops.pop()))

        return ensure_ops_consumed()

    def assertOp(self, op_name, lineno, lexpos, *args):
        op = self.ops[-1].popleft()
        self.assertEqual(
            self.compiler.op_codes[op_name],
            op[0],
            '%s != %s' % (op_name, self.compiler.op_names[op[0]]),
            )
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

    def test_object_literal_expr(self):
        with self.compile('{}'):
            self.assertOp('BUILD_OBJECT', 1, 0, 0)

        with self.compile('{a: 1, "b": 2, c: 3}'):
            self.assertOp('LOAD_CONST', 1, 0, 'a')
            self.assertOp('LOAD_CONST', 1, 4, 1.0, None)
            self.assertOp('LOAD_CONST', 1, 0, 'b')
            self.assertOp('LOAD_CONST', 1, 12, 2.0, None)
            self.assertOp('LOAD_CONST', 1, 0, 'c')
            self.assertOp('LOAD_CONST', 1, 18, 3.0, None)
            self.assertOp('BUILD_OBJECT', 1, 0, 3)

    def test_attribute_expr(self):
        with self.compile('foo.bar'):
            self.assertOp('LOAD_NAME', 1, 0, 'foo')
            self.assertOp('LOAD_ATTR', 1, 3, 'bar')

    def test_subscript_expr(self):
        with self.compile('foo[bar]'):
            self.assertOp('LOAD_NAME', 1, 0, 'foo')
            self.assertOp('LOAD_NAME', 1, 4, 'bar')
            args = self.assertOp('LOAD_SUBSCR', 1, 3)
            self.assertEqual(0, len(args))

    def test_call_expr(self):
        with self.compile('foo()'):
            self.assertOp('LOAD_NAME', 1, 0, 'foo')
            args = self.assertOp('CALL_FUNCTION', 1, 3)
            self.assertEqual(0, len(args))

        with self.compile('foo(a, b.c[d], true)'):
            self.assertOp('LOAD_NAME', 1, 0, 'foo')
            args = self.assertOp('CALL_FUNCTION', 1, 3)
            self.assertEqual(3, len(args))

            with self.assertOpList(args[0]):
                self.assertOp('LOAD_NAME', 1, 4, 'a')

            with self.assertOpList(args[1]):
                self.assertOp('LOAD_NAME', 1, 7, 'b')
                self.assertOp('LOAD_ATTR', 1, 8, 'c')
                self.assertOp('LOAD_NAME', 1, 11, 'd')
                self.assertOp('LOAD_SUBSCR', 1, 10)

            with self.assertOpList(args[2]):
                self.assertOp('LOAD_CONST', 1, 15, True)
