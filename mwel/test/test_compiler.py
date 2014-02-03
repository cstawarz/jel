from __future__ import division, print_function, unicode_literals
import collections
import unittest

from jel.test.test_compiler import CompilerTestMixin

from ..compiler import Compiler
from ..lexer import Lexer
from ..parser import Parser


class TestCompiler(CompilerTestMixin, unittest.TestCase):

    lexer_class = Lexer
    parser_class = Parser
    compiler_class = Compiler

    def setUp(self):
        super(TestCompiler, self).setUp()

        orig_compile = self.compile
        def compile_wrapper(s):
            self.lineno_to_lexpos = {}
            current_lineno = 1
            current_lexpos = 0

            while True:
                self.lineno_to_lexpos[current_lineno] = current_lexpos
                index = s.find('\n', current_lexpos)
                if index == -1:
                    break
                current_lineno += 1
                current_lexpos = index + 1

            return orig_compile(s)

        self.compile = compile_wrapper

    def assertOp(self, op_name, lineno, colno, *args):
        lexpos = self.lineno_to_lexpos[lineno] + colno - 1
        return super(TestCompiler, self).assertOp(op_name,
                                                  lineno,
                                                  lexpos,
                                                  *args)

    def test_chained_assignment_stmt(self):
        with self.compile('''
                          foo = true
                          '''):
            self.assertOp('LOAD_CONST', 2, 33, True)
            self.assertOp('STORE_GLOBAL', 2, 31, 'foo')

        with self.compile('''
                          a[b] = c.d = e = null
                          '''):
            self.assertOp('LOAD_CONST', 2, 44, None)
            self.assertOp('DUP_TOP', 2, 42)
            self.assertOp('STORE_GLOBAL', 2, 42, 'e')
            self.assertOp('DUP_TOP', 2, 38)
            self.assertOp('LOAD_GLOBAL', 2, 34, 'c')
            self.assertOp('STORE_ATTR', 2, 38, 'd')
            self.assertOp('LOAD_GLOBAL', 2, 27, 'a')
            self.assertOp('LOAD_GLOBAL', 2, 29, 'b')
            self.assertOp('STORE_SUBSCR', 2, 32)

    def test_augmented_assignment_stmt(self):
        def test_augassign(op):
            op_code = self.compiler.binary_op_codes[op]

            with self.compile('''
                              foo %s= 1
                              ''' % op):
                self.assertOp('LOAD_GLOBAL', 2, 31, 'foo')
                self.assertOp('LOAD_CONST', 2, len(op)+37, 1.0, None)
                self.assertOp('BINARY_OP', 2, 35, op_code)
                self.assertOp('STORE_GLOBAL', 2, 35, 'foo')

            with self.compile('''
                              foo.bar %s= 2
                              ''' % op):
                self.assertOp('LOAD_GLOBAL', 2, 31, 'foo')
                self.assertOp('DUP_TOP', 2, 39)
                self.assertOp('LOAD_ATTR', 2, 34, 'bar')
                self.assertOp('LOAD_CONST', 2, len(op)+41, 2.0, None)
                self.assertOp('BINARY_OP', 2, 39, op_code)
                self.assertOp('ROT_TWO', 2, 39)
                self.assertOp('STORE_ATTR', 2, 39, 'bar')

            with self.compile('''
                              foo[bar] %s= 3
                              ''' % op):
                self.assertOp('LOAD_GLOBAL', 2, 31, 'foo')
                self.assertOp('LOAD_GLOBAL', 2, 35, 'bar')
                self.assertOp('DUP_TOP_TWO', 2, 40)
                self.assertOp('LOAD_SUBSCR', 2, 34)
                self.assertOp('LOAD_CONST', 2, len(op)+42, 3.0, None)
                self.assertOp('BINARY_OP', 2, 40, op_code)
                self.assertOp('ROT_THREE', 2, 40)
                self.assertOp('STORE_SUBSCR', 2, 40)

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

            self.assertOp('LOAD_LOCAL', 3, 13, 'foo')
            self.assertOp('LOAD_CONST', 3, 20, 2.0, None)
            self.assertOp('BINARY_OP', 3, 17,
                          self.compiler.binary_op_codes['+'])
            self.assertOp('STORE_LOCAL', 3, 17, 'foo')

            self.assertOp('LOAD_CONST', 4, 19, True)
            self.assertOp('STORE_LOCAL', 4, 17, 'foo')

    def test_simple_call_stmt(self):
        with self.compile('''
                          foo()
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 27, 'foo')
            args = self.assertOp('CALL_SIMPLE', 2, 30)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], tuple)
            self.assertEqual(0, len(args[0]))

        with self.compile('''
                          foo(a, b.c[d], true)
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 27, 'foo')
            args = self.assertOp('CALL_SIMPLE', 2, 30)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], tuple)
            self.assertEqual(3, len(args[0]))

            with self.assertOpList(args[0][0]):
                self.assertOp('LOAD_GLOBAL', 2, 31, 'a')

            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
                self.assertOp('LOAD_ATTR', 2, 35, 'c')
                self.assertOp('LOAD_GLOBAL', 2, 38, 'd')
                self.assertOp('LOAD_SUBSCR', 2, 37)

            with self.assertOpList(args[0][2]):
                self.assertOp('LOAD_CONST', 2, 42, True)

        with self.compile('''
                          foo(a=true, b=false)
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 27, 'foo')
            args = self.assertOp('CALL_SIMPLE', 2, 30)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], collections.OrderedDict)
            self.assertEqual(2, len(args[0]))
            args = tuple(args[0].items())

            self.assertEqual('a', args[0][0])
            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_CONST', 2, 33, True)

            self.assertEqual('b', args[1][0])
            with self.assertOpList(args[1][1]):
                self.assertOp('LOAD_CONST', 2, 41, False)

    def test_compound_call_stmt(self):
        def check_clause(c, expected_num_args, expected_num_local_names):
            self.assertIsInstance(c, tuple)
            self.assertEqual(3, len(c))

            args = c[0]
            self.assertIsInstance(args, (tuple, collections.OrderedDict))
            self.assertEqual(expected_num_args, len(args))

            num_local_names = c[1]
            self.assertIsInstance(num_local_names, int)
            self.assertEqual(expected_num_local_names, num_local_names)

            body = c[2]
            return args, body

        with self.compile('''
                          foo ():
                              local x = 2
                              y = 3
                          end
                          '''):
            args = self.assertOp('CALL_COMPOUND', 2, 27)
            self.assertEqual(2, len(args))
            self.assertEqual('foo:', args[0])
            clauses = args[1]
            self.assertIsInstance(clauses, tuple)
            self.assertEqual(1, len(clauses))
            args, body = check_clause(clauses[0], 0, 0)
            with self.assertOpList(body):
                self.assertOp('PUSH_SCOPE', 2, 33)
                self.assertOp('LOAD_CONST', 3, 41, 2.0, None)
                self.assertOp('INIT_LOCAL', 3, 31, 'x')
                self.assertOp('LOAD_CONST', 4, 35, 3.0, None)
                self.assertOp('STORE_GLOBAL', 4, 33, 'y')
                self.assertOp('POP_SCOPE', 2, 33)

        with self.compile('''
                          foo (a, b.c[d], true) -> x, y:
                              z = x + y
                          else bar(a=true, b=false) -> q:
                              z = 5*q
                          else:
                              z = 6
                          end
                          '''):
            args = self.assertOp('CALL_COMPOUND', 2, 27)
            self.assertEqual(2, len(args))
            self.assertEqual('foo:bar::', args[0])
            clauses = args[1]
            self.assertIsInstance(clauses, tuple)
            self.assertEqual(3, len(clauses))

            args, body = check_clause(clauses[0], 3, 2)
            with self.assertOpList(args[0]):
                self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            with self.assertOpList(args[1]):
                self.assertOp('LOAD_GLOBAL', 2, 35, 'b')
                self.assertOp('LOAD_ATTR', 2, 36, 'c')
                self.assertOp('LOAD_GLOBAL', 2, 39, 'd')
                self.assertOp('LOAD_SUBSCR', 2, 38)
            with self.assertOpList(args[2]):
                self.assertOp('LOAD_CONST', 2, 43, True)
            with self.assertOpList(body):
                self.assertOp('PUSH_SCOPE', 2, 56)
                self.assertOp('INIT_LOCAL', 2, 55, 'y')
                self.assertOp('INIT_LOCAL', 2, 52, 'x')
                self.assertOp('LOAD_LOCAL', 3, 35, 'x')
                self.assertOp('LOAD_LOCAL', 3, 39, 'y')
                self.assertOp('BINARY_OP', 3, 37,
                              self.compiler.binary_op_codes['+'])
                self.assertOp('STORE_GLOBAL', 3, 33, 'z')
                self.assertOp('POP_SCOPE', 2, 56)

            args, body = check_clause(clauses[1], 2, 1)
            args = tuple(args.items())
            self.assertEqual('a', args[0][0])
            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_CONST', 4, 38, True)
            self.assertEqual('b', args[1][0])
            with self.assertOpList(args[1][1]):
                self.assertOp('LOAD_CONST', 4, 46, False)
            with self.assertOpList(body):
                self.assertOp('PUSH_SCOPE', 4, 57)
                self.assertOp('INIT_LOCAL', 4, 56, 'q')
                self.assertOp('LOAD_CONST', 5, 35, 5.0, None)
                self.assertOp('LOAD_LOCAL', 5, 37, 'q')
                self.assertOp('BINARY_OP', 5, 36,
                              self.compiler.binary_op_codes['*'])
                self.assertOp('STORE_GLOBAL', 5, 33, 'z')
                self.assertOp('POP_SCOPE', 4, 57)

            args, body = check_clause(clauses[2], 0, 0)
            with self.assertOpList(body):
                self.assertOp('PUSH_SCOPE', 6, 31)
                self.assertOp('LOAD_CONST', 7, 35, 6.0, None)
                self.assertOp('STORE_GLOBAL', 7, 33, 'z')
                self.assertOp('POP_SCOPE', 6, 31)

    def test_call_expr_with_named_args(self):
        with self.compile('''
                          x = foo(a=true, b=false)
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 31, 'foo')
            args = self.assertOp('CALL_FUNCTION', 2, 34)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], collections.OrderedDict)
            self.assertEqual(2, len(args[0]))
            args = tuple(args[0].items())

            self.assertEqual('a', args[0][0])
            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_CONST', 2, 37, True)

            self.assertEqual('b', args[1][0])
            with self.assertOpList(args[1][1]):
                self.assertOp('LOAD_CONST', 2, 45, False)

            self.assertOp('STORE_GLOBAL', 2, 29, 'x')
