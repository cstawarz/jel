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
                self.assertOp('LOAD_CONST', 2, len(op)+37, 1.0)
                self.assertOp('BINARY_OP', 2, 35, op_code)
                self.assertOp('STORE_GLOBAL', 2, 35, 'foo')

            with self.compile('''
                              foo.bar %s= 2
                              ''' % op):
                self.assertOp('LOAD_GLOBAL', 2, 31, 'foo')
                self.assertOp('DUP_TOP', 2, 39)
                self.assertOp('LOAD_ATTR', 2, 34, 'bar')
                self.assertOp('LOAD_CONST', 2, len(op)+41, 2.0)
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
                self.assertOp('LOAD_CONST', 2, len(op)+42, 3.0)
                self.assertOp('BINARY_OP', 2, 40, op_code)
                self.assertOp('ROT_THREE', 2, 40)
                self.assertOp('STORE_SUBSCR', 2, 40)

        test_augassign('+')
        test_augassign('-')
        test_augassign('*')
        test_augassign('/')
        test_augassign('%')
        test_augassign('**')

    def get_call_stmt_body(self, lineno, lexpos):
        args = self.assertOp('CALL_COMPOUND', lineno, lexpos)
        return args[1][0][2]

    def test_local_stmt(self):
        #
        #  Test name depth
        #

        with self.compile('''
            local foo = 1
            foo += 2
            foo = true
            scope ():
                foo += 2
                foo = true
                scope ():
                    foo += 2
                    foo = true
                end
            end
            '''):
            self.assertOp('LOAD_CONST', 2, 25, 1.0)
            self.assertOp('INIT_LOCAL', 2, 13, 'foo')
            self.assertOp('LOAD_LOCAL', 3, 13, 'foo')
            self.assertOp('LOAD_CONST', 3, 20, 2.0)
            self.assertOp('BINARY_OP', 3, 17,
                          self.compiler.binary_op_codes['+'])
            self.assertOp('STORE_LOCAL', 3, 17, 'foo')
            self.assertOp('LOAD_CONST', 4, 19, True)
            self.assertOp('STORE_LOCAL', 4, 17, 'foo')

            with self.assertOpList(self.get_call_stmt_body(5, 13)):
                self.assertOp('LOAD_NONLOCAL', 6, 17, 'foo', 1)
                self.assertOp('LOAD_CONST', 6, 24, 2.0)
                self.assertOp('BINARY_OP', 6, 21,
                              self.compiler.binary_op_codes['+'])
                self.assertOp('STORE_NONLOCAL', 6, 21, 'foo', 1)
                self.assertOp('LOAD_CONST', 7, 23, True)
                self.assertOp('STORE_NONLOCAL', 7, 21, 'foo', 1)

                with self.assertOpList(self.get_call_stmt_body(8, 17)):
                    self.assertOp('LOAD_NONLOCAL', 9, 21, 'foo', 2)
                    self.assertOp('LOAD_CONST', 9, 28, 2.0)
                    self.assertOp('BINARY_OP', 9, 25,
                                  self.compiler.binary_op_codes['+'])
                    self.assertOp('STORE_NONLOCAL', 9, 25, 'foo', 2)
                    self.assertOp('LOAD_CONST', 10, 27, True)
                    self.assertOp('STORE_NONLOCAL', 10, 25, 'foo', 2)

        #
        #  Test name masking
        #

        with self.compile('''
            local foo = false
            scope ():
                local foo = foo
                scope ():
                    local foo = foo
                    foo = true
                end
                foo = true
            end
            foo = true
            '''):

            self.assertOp('LOAD_CONST', 2, 25, False)
            self.assertOp('INIT_LOCAL', 2, 13, 'foo')

            with self.assertOpList(self.get_call_stmt_body(3, 13)):
                self.assertOp('LOAD_NONLOCAL', 4, 29, 'foo', 1)
                self.assertOp('INIT_LOCAL', 4, 17, 'foo')

                with self.assertOpList(self.get_call_stmt_body(5, 17)):
                    self.assertOp('LOAD_NONLOCAL', 6, 33, 'foo', 1)
                    self.assertOp('INIT_LOCAL', 6, 21, 'foo')
                    self.assertOp('LOAD_CONST', 7, 27, True)
                    self.assertOp('STORE_LOCAL', 7, 25, 'foo')

                self.assertOp('LOAD_CONST', 9, 23, True)
                self.assertOp('STORE_LOCAL', 9, 21, 'foo')

            self.assertOp('LOAD_CONST', 11, 19, True)
            self.assertOp('STORE_LOCAL', 11, 17, 'foo')

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
                self.assertOp('LOAD_CONST', 3, 41, 2.0)
                self.assertOp('INIT_LOCAL', 3, 31, 'x')
                self.assertOp('LOAD_CONST', 4, 35, 3.0)
                self.assertOp('STORE_GLOBAL', 4, 33, 'y')

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
                self.assertOp('INIT_LOCAL', 2, 55, 'y')
                self.assertOp('INIT_LOCAL', 2, 52, 'x')
                self.assertOp('LOAD_LOCAL', 3, 35, 'x')
                self.assertOp('LOAD_LOCAL', 3, 39, 'y')
                self.assertOp('BINARY_OP', 3, 37,
                              self.compiler.binary_op_codes['+'])
                self.assertOp('STORE_GLOBAL', 3, 33, 'z')

            args, body = check_clause(clauses[1], 2, 1)
            args = tuple(args.items())
            self.assertEqual('a', args[0][0])
            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_CONST', 4, 38, True)
            self.assertEqual('b', args[1][0])
            with self.assertOpList(args[1][1]):
                self.assertOp('LOAD_CONST', 4, 46, False)
            with self.assertOpList(body):
                self.assertOp('INIT_LOCAL', 4, 56, 'q')
                self.assertOp('LOAD_CONST', 5, 35, 5.0)
                self.assertOp('LOAD_LOCAL', 5, 37, 'q')
                self.assertOp('BINARY_OP', 5, 36,
                              self.compiler.binary_op_codes['*'])
                self.assertOp('STORE_GLOBAL', 5, 33, 'z')

            args, body = check_clause(clauses[2], 0, 0)
            with self.assertOpList(body):
                self.assertOp('LOAD_CONST', 7, 35, 6.0)
                self.assertOp('STORE_GLOBAL', 7, 33, 'z')
 
    def test_call_expr_with_named_args(self):
        with self.compile('''
                          x = foo(a=true, b=false, c <- foo[0].bar, d=null)
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 31, 'foo')
            args = self.assertOp('CALL_FUNCTION', 2, 34)
            self.assertEqual(1, len(args))
            self.assertIsInstance(args[0], collections.OrderedDict)
            self.assertEqual(4, len(args[0]))
            args = tuple(args[0].items())

            self.assertEqual('a', args[0][0])
            with self.assertOpList(args[0][1]):
                self.assertOp('LOAD_CONST', 2, 37, True)

            self.assertEqual('b', args[1][0])
            with self.assertOpList(args[1][1]):
                self.assertOp('LOAD_CONST', 2, 45, False)

            self.assertEqual('c', args[2][0])
            with self.assertOpList(args[2][1]):
                self.assertOp('LOAD_GLOBAL', 2, 57, 'foo')
                self.assertOp('LOAD_CONST', 2, 61, 0.0)
                self.assertOp('LOAD_SUBSCR', 2, 60)
                self.assertOp('LOAD_ATTR_REF', 2, 63, 'bar')

            self.assertEqual('d', args[3][0])
            with self.assertOpList(args[3][1]):
                self.assertOp('LOAD_CONST', 2, 71, None)

            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

    def check_function(self,
                       lineno,
                       lexpos,
                       expected_num_args,
                       *expected_closures):
        args = self.assertOp('MAKE_FUNCTION', lineno, lexpos)
        self.assertEqual(3, len(args))
        self.assertIsInstance(args[0], int)
        self.assertEqual(expected_num_args, args[0])
        self.assertIsInstance(args[2], tuple)
        self.assertEqual(expected_closures, args[2])
        return args[1]

    def test_function_stmt(self):
        with self.compile('''
                          function two():
                              return 2
                          end
                          '''):
            body = self.check_function(2, 27, 0)
            with self.assertOpList(body):
                self.assertOp('LOAD_CONST', 3, 38, 2.0)
                self.assertOp('RETURN_VALUE', 3, 31)
            self.assertOp('STORE_GLOBAL', 2, 27, 'two')

        with self.compile('''
                          function sum(a, b):
                              return a+b
                          end
                          '''):
            body = self.check_function(2, 27, 2)
            with self.assertOpList(body):
                self.assertOp('INIT_LOCAL', 2, 43, 'b')
                self.assertOp('INIT_LOCAL', 2, 40, 'a')
                self.assertOp('LOAD_LOCAL', 3, 38, 'a')
                self.assertOp('LOAD_LOCAL', 3, 40, 'b')
                self.assertOp('BINARY_OP', 3, 39,
                              self.compiler.binary_op_codes['+'])
                self.assertOp('RETURN_VALUE', 3, 31)
            self.assertOp('STORE_GLOBAL', 2, 27, 'sum')

        with self.compile('''
                          local function self():
                              return self
                          end
                          '''):
            self.assertOp('LOAD_CONST', 2, 33, None)
            self.assertOp('INIT_LOCAL', 2, 33, 'self')
            body = self.check_function(2, 33, 0, ('self', 0))
            with self.assertOpList(body):
                self.assertOp('LOAD_CLOSURE', 3, 38, 'self')
                self.assertOp('RETURN_VALUE', 3, 31)
            self.assertOp('STORE_LOCAL', 2, 33, 'self')

        with self.compile('''
                          local function foo():
                          end
                          local bar = null
                          function bar():
                          end
                          scope ():
                              function foo():
                              end
                          end
                          '''):
            self.assertOp('LOAD_CONST', 2, 33, None)
            self.assertOp('INIT_LOCAL', 2, 33, 'foo')
            with self.assertOpList(self.check_function(2, 33, 0)):
                pass
            self.assertOp('STORE_LOCAL', 2, 33, 'foo')

            self.assertOp('LOAD_CONST', 4, 39, None)
            self.assertOp('INIT_LOCAL', 4, 27, 'bar')

            with self.assertOpList(self.check_function(5, 27, 0)):
                pass
            self.assertOp('STORE_LOCAL', 5, 27, 'bar')

            body = self.get_call_stmt_body(7, 27)
            with self.assertOpList(body):
                with self.assertOpList(self.check_function(8, 31, 0)):
                    pass
                self.assertOp('STORE_NONLOCAL', 8, 31, 'foo', 1)

    def test_function_stmt_with_closure(self):
        with self.compile('''local w = 2
                          local x = 1
                          local function foo():
                              local y = 2
                              scope ():
                                  local z = y*x
                                  local function bar(z):
                                      y += w
                                      return x+z
                                  end
                                  local x = 4
                                  x = 5
                                  y = 6
                                  return bar
                              end
                          end
                          '''):
            self.assertOp('LOAD_CONST', 1, 11, 2.0)
            self.assertOp('INIT_LOCAL', 1, 1, 'w')

            self.assertOp('LOAD_CONST', 2, 37, 1.0)
            self.assertOp('INIT_LOCAL', 2, 27, 'x')

            self.assertOp('LOAD_CONST', 3, 33, None)
            self.assertOp('INIT_LOCAL', 3, 33, 'foo')

            body = self.check_function(3, 33, 0, ('x', 0), ('w', 0))
            with self.assertOpList(body):
                self.assertOp('LOAD_CONST', 4, 41, 2.0)
                self.assertOp('INIT_LOCAL', 4, 31, 'y')

                body = self.get_call_stmt_body(5, 31)
                with self.assertOpList(body):
                    self.assertOp('LOAD_NONLOCAL', 6, 45, 'y', 1)
                    self.assertOp('LOAD_CLOSURE', 6, 47, 'x')
                    self.assertOp('BINARY_OP', 6, 46,
                                  self.compiler.binary_op_codes['*'])
                    self.assertOp('INIT_LOCAL', 6, 35, 'z')
    
                    self.assertOp('LOAD_CONST', 7, 41, None)
                    self.assertOp('INIT_LOCAL', 7, 41, 'bar')

                    body = self.check_function(7, 41, 1,
                                               ('y', 1), ('w', -2), ('x', -2))
                    with self.assertOpList(body):
                        self.assertOp('INIT_LOCAL', 7, 54, 'z')
    
                        self.assertOp('LOAD_CLOSURE', 8, 39, 'y')
                        self.assertOp('LOAD_CLOSURE', 8, 44, 'w')
                        self.assertOp('BINARY_OP', 8, 41,
                                      self.compiler.binary_op_codes['+'])
                        self.assertOp('STORE_CLOSURE', 8, 41, 'y')
    
                        self.assertOp('LOAD_CLOSURE', 9, 46, 'x')
                        self.assertOp('LOAD_LOCAL', 9, 48, 'z')
                        self.assertOp('BINARY_OP', 9, 47,
                                      self.compiler.binary_op_codes['+'])
                        self.assertOp('RETURN_VALUE', 9, 39)
    
                    self.assertOp('STORE_LOCAL', 7, 41, 'bar')
    
                    self.assertOp('LOAD_CONST', 11, 45, 4.0)
                    self.assertOp('INIT_LOCAL', 11, 35, 'x')
    
                    self.assertOp('LOAD_CONST', 12, 39, 5.0)
                    self.assertOp('STORE_LOCAL', 12, 37, 'x')
    
                    self.assertOp('LOAD_CONST', 13, 39, 6.0)
                    self.assertOp('STORE_NONLOCAL', 13, 37, 'y', 1)
    
                    self.assertOp('LOAD_LOCAL', 14, 42, 'bar')
                    self.assertOp('RETURN_VALUE', 14, 35)

            self.assertOp('STORE_LOCAL', 3, 33, 'foo')

    def test_return_stmt(self):
        with self.compile('''
                          return 2*x
                          '''):
            self.assertOp('LOAD_CONST', 2, 34, 2.0)
            self.assertOp('LOAD_GLOBAL', 2, 36, 'x')
            self.assertOp('BINARY_OP', 2, 35,
                          self.compiler.binary_op_codes['*'])
            self.assertOp('RETURN_VALUE', 2, 27)

        with self.compile('''
                          return
                          '''):
            self.assertOp('LOAD_CONST', 2, 27, None)
            self.assertOp('RETURN_VALUE', 2, 27)

    def test_function_expr(self):
        with self.compile('''
                          two = function () 2 end
                          '''):
            body = self.check_function(2, 33, 0)
            with self.assertOpList(body):
                self.assertOp('LOAD_CONST', 2, 45, 2.0)
                self.assertOp('RETURN_VALUE', 2, 45)
            self.assertOp('STORE_GLOBAL', 2, 31, 'two')

        with self.compile('''
                          local a1 = false
                          local x1 = true
                          scope ():
                              local b1 = false
                              local y1 = true
                              scope ():
                                  local c1 = false
                                  local z1 = true
                                  local function foo():
                                      local a2 = false
                                      local x2 = true
                                      scope ():
                                          local b2 = false
                                          local y2 = true
                                          scope ():
                                              local c2 = false
                                              local z2 = true
                                              local bar = function (m, n) [x1, y1, z1, x2, y2, z2, m, n] end
                                              return bar
                                          end
                                      end
                                  end
                              end
                          end
                          '''):
            self.assertOp('LOAD_CONST', 2, 38, False)
            self.assertOp('INIT_LOCAL', 2, 27, 'a1')

            self.assertOp('LOAD_CONST', 3, 38, True)
            self.assertOp('INIT_LOCAL', 3, 27, 'x1')

            body = self.get_call_stmt_body(4, 27)
            with self.assertOpList(body):
                self.assertOp('LOAD_CONST', 5, 42, False)
                self.assertOp('INIT_LOCAL', 5, 31, 'b1')
    
                self.assertOp('LOAD_CONST', 6, 42, True)
                self.assertOp('INIT_LOCAL', 6, 31, 'y1')

                body = self.get_call_stmt_body(7, 31)
                with self.assertOpList(body):
                    self.assertOp('LOAD_CONST', 8, 46, False)
                    self.assertOp('INIT_LOCAL', 8, 35, 'c1')
        
                    self.assertOp('LOAD_CONST', 9, 46, True)
                    self.assertOp('INIT_LOCAL', 9, 35, 'z1')
        
                    self.assertOp('LOAD_CONST', 10, 41, None)
                    self.assertOp('INIT_LOCAL', 10, 41, 'foo')

                    body = self.check_function(10, 41, 0,
                                               ('x1', 2),
                                               ('y1', 1),
                                               ('z1', 0))
                    with self.assertOpList(body):
                        self.assertOp('LOAD_CONST', 11, 50, False)
                        self.assertOp('INIT_LOCAL', 11, 39, 'a2')
            
                        self.assertOp('LOAD_CONST', 12, 50, True)
                        self.assertOp('INIT_LOCAL', 12, 39, 'x2')
            
                        body = self.get_call_stmt_body(13, 39)
                        with self.assertOpList(body):
                            self.assertOp('LOAD_CONST', 14, 54, False)
                            self.assertOp('INIT_LOCAL', 14, 43, 'b2')
                
                            self.assertOp('LOAD_CONST', 15, 54, True)
                            self.assertOp('INIT_LOCAL', 15, 43, 'y2')
            
                            body = self.get_call_stmt_body(16, 43)
                            with self.assertOpList(body):
                                self.assertOp('LOAD_CONST', 17, 58, False)
                                self.assertOp('INIT_LOCAL', 17, 47, 'c2')
                    
                                self.assertOp('LOAD_CONST', 18, 58, True)
                                self.assertOp('INIT_LOCAL', 18, 47, 'z2')

                                body = self.check_function(19, 59, 2,
                                                           ('x1', -5),
                                                           ('y1', -4),
                                                           ('z1', -3),
                                                           ('x2', 2),
                                                           ('y2', 1),
                                                           ('z2', 0))
                                with self.assertOpList(body):
                                    self.assertOp('INIT_LOCAL', 19, 72, 'n')
                                    self.assertOp('INIT_LOCAL', 19, 69, 'm')

                                    self.assertOp('LOAD_CLOSURE', 19, 76, 'x1')
                                    self.assertOp('LOAD_CLOSURE', 19, 80, 'y1')
                                    self.assertOp('LOAD_CLOSURE', 19, 84, 'z1')
                                    self.assertOp('LOAD_CLOSURE', 19, 88, 'x2')
                                    self.assertOp('LOAD_CLOSURE', 19, 92, 'y2')
                                    self.assertOp('LOAD_CLOSURE', 19, 96, 'z2')
                                    self.assertOp('LOAD_LOCAL', 19, 100, 'm')
                                    self.assertOp('LOAD_LOCAL', 19, 103, 'n')
                                    self.assertOp('BUILD_ARRAY', 19, 75, 8)
                                    self.assertOp('RETURN_VALUE', 19, 75)

                                self.assertOp('INIT_LOCAL', 19, 47, 'bar')

                                self.assertOp('LOAD_LOCAL', 20, 54, 'bar')
                                self.assertOp('RETURN_VALUE', 20, 47)
    
                    self.assertOp('STORE_LOCAL', 10, 41, 'foo')

    def test_array_literal_expr(self):
        with self.compile('''
                          x = []
                          '''):
            self.assertOp('BUILD_ARRAY', 2, 31, 0)
            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

        with self.compile('''
                          x = [a,b,c]
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
            self.assertOp('LOAD_GLOBAL', 2, 36, 'c')
            self.assertOp('BUILD_ARRAY', 2, 31, 3)
            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

        with self.compile('''
                          x = [a:b]
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
            self.assertOp('LOAD_CONST', 2, 31, None)
            self.assertOp('BUILD_RANGE_ARRAY', 2, 31)
            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

        with self.compile('''
                          x = [a:b:c]
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
            self.assertOp('LOAD_GLOBAL', 2, 36, 'c')
            self.assertOp('BUILD_RANGE_ARRAY', 2, 31)
            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

        with self.compile('''
                          x = [a:b,c]
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
            self.assertOp('LOAD_CONST', 2, 31, None)
            self.assertOp('BUILD_RANGE_ARRAY', 2, 31)

            self.assertOp('LOAD_GLOBAL', 2, 36, 'c')
            self.assertOp('BUILD_ARRAY', 2, 31, 1)

            self.assertOp('CONCAT_ARRAYS', 2, 31, 2)

            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

        with self.compile('''
                          x = [a,b:c]
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            self.assertOp('BUILD_ARRAY', 2, 31, 1)

            self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
            self.assertOp('LOAD_GLOBAL', 2, 36, 'c')
            self.assertOp('LOAD_CONST', 2, 31, None)
            self.assertOp('BUILD_RANGE_ARRAY', 2, 31)

            self.assertOp('CONCAT_ARRAYS', 2, 31, 2)

            self.assertOp('STORE_GLOBAL', 2, 29, 'x')

        with self.compile('''
                          x = [a,b,c:d:e,f,g,h,i:j,k]
                          '''):
            self.assertOp('LOAD_GLOBAL', 2, 32, 'a')
            self.assertOp('LOAD_GLOBAL', 2, 34, 'b')
            self.assertOp('BUILD_ARRAY', 2, 31, 2)

            self.assertOp('LOAD_GLOBAL', 2, 36, 'c')
            self.assertOp('LOAD_GLOBAL', 2, 38, 'd')
            self.assertOp('LOAD_GLOBAL', 2, 40, 'e')
            self.assertOp('BUILD_RANGE_ARRAY', 2, 31)

            self.assertOp('LOAD_GLOBAL', 2, 42, 'f')
            self.assertOp('LOAD_GLOBAL', 2, 44, 'g')
            self.assertOp('LOAD_GLOBAL', 2, 46, 'h')
            self.assertOp('BUILD_ARRAY', 2, 31, 3)

            self.assertOp('LOAD_GLOBAL', 2, 48, 'i')
            self.assertOp('LOAD_GLOBAL', 2, 50, 'j')
            self.assertOp('LOAD_CONST', 2, 31, None)
            self.assertOp('BUILD_RANGE_ARRAY', 2, 31)

            self.assertOp('LOAD_GLOBAL', 2, 52, 'k')
            self.assertOp('BUILD_ARRAY', 2, 31, 1)

            self.assertOp('CONCAT_ARRAYS', 2, 31, 5)

            self.assertOp('STORE_GLOBAL', 2, 29, 'x')
