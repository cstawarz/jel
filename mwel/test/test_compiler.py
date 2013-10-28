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
