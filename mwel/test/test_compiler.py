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
            self.assertOp('STORE_GLOBAL', 1, 4, 'foo')

        with self.compile('a[b] = c.d = e = null'):
            self.assertOp('LOAD_CONST', 1, 17, None)
            self.assertOp('DUP_TOP', 1, 15)
            self.assertOp('STORE_GLOBAL', 1, 15, 'e')
            self.assertOp('DUP_TOP', 1, 11)
            self.assertOp('LOAD_GLOBAL', 1, 7, 'c')
            self.assertOp('STORE_ATTR', 1, 11, 'd')
            self.assertOp('LOAD_GLOBAL', 1, 0, 'a')
            self.assertOp('LOAD_GLOBAL', 1, 2, 'b')
            self.assertOp('STORE_SUBSCR', 1, 5)

    def test_augmented_assignment_stmt(self):
        def test_augassign(op):
            op_code = self.compiler.binary_op_codes[op]

            with self.compile('foo %s= 1' % op):
                self.assertOp('LOAD_GLOBAL', 1, 0, 'foo')
                self.assertOp('LOAD_CONST', 1, len(op)+6, 1.0, None)
                self.assertOp('BINARY_OP', 1, 4, op_code)
                self.assertOp('STORE_GLOBAL', 1, 4, 'foo')

            with self.compile('foo.bar %s= 2' % op):
                self.assertOp('LOAD_GLOBAL', 1, 0, 'foo')
                self.assertOp('DUP_TOP', 1, 8)
                self.assertOp('LOAD_ATTR', 1, 3, 'bar')
                self.assertOp('LOAD_CONST', 1, len(op)+10, 2.0, None)
                self.assertOp('BINARY_OP', 1, 8, op_code)
                self.assertOp('ROT_TWO', 1, 8)
                self.assertOp('STORE_ATTR', 1, 8, 'bar')

            with self.compile('foo[bar] %s= 3' % op):
                self.assertOp('LOAD_GLOBAL', 1, 0, 'foo')
                self.assertOp('LOAD_GLOBAL', 1, 4, 'bar')
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

    def test_local_stmt(self):
        with self.compile('''
            local foo = 1
            foo += 2
            foo = true
            '''):
            self.assertOp('LOAD_CONST', 2, 25, 1.0, None)
            self.assertOp('INIT_LOCAL', 2, 13, 'foo')

            self.assertOp('LOAD_LOCAL', 3, 39, 'foo')
            self.assertOp('LOAD_CONST', 3, 46, 2.0, None)
            self.assertOp('BINARY_OP', 3, 43,
                          self.compiler.binary_op_codes['+'])
            self.assertOp('STORE_LOCAL', 3, 43, 'foo')

            self.assertOp('LOAD_CONST', 4, 66, True)
            self.assertOp('STORE_LOCAL', 4, 64, 'foo')

    def test_simple_call_stmt(self):
        with self.compile('foo()'):
            self.assertOp('LOAD_GLOBAL', 1, 0, 'foo')
            args = self.assertOp('CALL_SIMPLE', 1, 3)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], tuple)
            self.assertEqual(0, len(args[0]))

        with self.compile('foo(a, b.c[d], true)'):
            self.assertOp('LOAD_GLOBAL', 1, 0, 'foo')
            args = self.assertOp('CALL_SIMPLE', 1, 3)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], tuple)
            self.assertEqual(3, len(args[0]))

            with self.assertOpList(args[0][0]):
                self.assertOp('LOAD_GLOBAL', 1, 4, 'a')

            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_GLOBAL', 1, 7, 'b')
                self.assertOp('LOAD_ATTR', 1, 8, 'c')
                self.assertOp('LOAD_GLOBAL', 1, 11, 'd')
                self.assertOp('LOAD_SUBSCR', 1, 10)

            with self.assertOpList(args[0][2]):
                self.assertOp('LOAD_CONST', 1, 15, True)

        with self.compile('foo(a=true, b=false)'):
            self.assertOp('LOAD_GLOBAL', 1, 0, 'foo')
            args = self.assertOp('CALL_SIMPLE', 1, 3)
            self.assertEqual(2, len(args))
            self.assertIsInstance(args[0], tuple)
            self.assertEqual(('a', 'b'), args[0])
            self.assertIsInstance(args[1], tuple)
            self.assertEqual(2, len(args[1]))

            with self.assertOpList(args[1][0]):
                self.assertOp('LOAD_CONST', 1, 6, True)

            with self.assertOpList(args[1][1]):
                self.assertOp('LOAD_CONST', 1, 14, False)

    def test_compound_call_stmt(self):
        def check_clause(c, expected_args, expected_local_names):
            self.assertIsInstance(c, tuple)
            self.assertEqual(3, len(c))

            args = c[0]
            self.assertIsInstance(args, tuple)
            self.assertEqual(expected_args, args)

            local_names = c[1]
            self.assertIsInstance(local_names, tuple)
            self.assertEqual(expected_local_names, local_names)

            body = c[2]
            return body

        with self.compile('''
                          foo ():
                              local x = 2
                              y = 3
                          end
                          '''):
            args = self.assertOp('CALL_COMPOUND', 2, 31)
            self.assertEqual(2, len(args))
            self.assertEqual('foo:', args[0])
            clauses = args[1]
            self.assertIsInstance(clauses, tuple)
            self.assertEqual(1, len(clauses))
            body = check_clause(clauses[0], (), ())
            with self.assertOpList(body):
                self.assertOp('LOAD_CONST', 3, 75, 2.0, None)
                self.assertOp('INIT_LOCAL', 3, 65, 'x')
                self.assertOp('LOAD_CONST', 4, 111, 3.0, None)
                self.assertOp('STORE_GLOBAL', 4, 109, 'y')
