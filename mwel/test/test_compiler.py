from __future__ import division, print_function, unicode_literals
import unittest

from jel.test.test_compiler import CompilerTestMixin

from ..compiler import Compiler
from ..lexer import Lexer
from ..parser import Parser


class TestCompiler(CompilerTestMixin, unittest.TestCase):

    lexer_class = Lexer
    parser_class = Parser
    compiler_class = Compiler

    def test_chained_assignment_stmt(self):
        with self.compile('foo = true'):
            self.assertOp('LOAD_CONST', 1, 6, True)
            self.assertOp('STORE_NAME', 1, 4, 'foo')

        with self.compile('a[b] = c.d = e = null'):
            self.assertOp('LOAD_CONST', 1, 17, None)
            self.assertOp('DUP_TOP', 1, 15)
            self.assertOp('STORE_NAME', 1, 15, 'e')
            self.assertOp('DUP_TOP', 1, 11)
            self.assertOp('LOAD_NAME', 1, 7, 'c')
            self.assertOp('STORE_ATTR', 1, 11, 'd')
            self.assertOp('LOAD_NAME', 1, 0, 'a')
            self.assertOp('LOAD_NAME', 1, 2, 'b')
            self.assertOp('STORE_SUBSCR', 1, 5)

    def test_augmented_assignment_stmt(self):
        def test_augassign(op):
            op_code = self.compiler.binary_op_codes[op]

            with self.compile('foo %s= 1' % op):
                self.assertOp('LOAD_NAME', 1, 0, 'foo')
                self.assertOp('LOAD_CONST', 1, len(op)+6, 1.0, None)
                self.assertOp('BINARY_OP', 1, 4, op_code)
                self.assertOp('STORE_NAME', 1, 4, 'foo')

            with self.compile('foo.bar %s= 2' % op):
                self.assertOp('LOAD_NAME', 1, 0, 'foo')
                self.assertOp('DUP_TOP', 1, 8)
                self.assertOp('LOAD_ATTR', 1, 3, 'bar')
                self.assertOp('LOAD_CONST', 1, len(op)+10, 2.0, None)
                self.assertOp('BINARY_OP', 1, 8, op_code)
                self.assertOp('ROT_TWO', 1, 8)
                self.assertOp('STORE_ATTR', 1, 8, 'bar')

            with self.compile('foo[bar] %s= 3' % op):
                self.assertOp('LOAD_NAME', 1, 0, 'foo')
                self.assertOp('LOAD_NAME', 1, 4, 'bar')
                self.assertOp('DUP_TOP_TWO', 1, 9)
                self.assertOp('LOAD_SUBSCR', 1, 3)
                self.assertOp('LOAD_CONST', 1, len(op)+11, 3.0, None)
                self.assertOp('BINARY_OP', 1, 9, op_code)
                self.assertOp('ROT_THREE', 1, 9)
                self.assertOp('STORE_SUBSCR', 1, 9)

        test_augassign('+')
        test_augassign('-')
        test_augassign('*')
        test_augassign('/')
        test_augassign('%')
        test_augassign('**')
