from __future__ import division, print_function, unicode_literals
import collections
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
                self.assertLocation(p, 1, 0)
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
            self.assertLocation(p, 1, 0)
            self.assertIsInstance(p.statements, tuple)
            self.assertEqual(2, len(p.statements))
            self.assertIsInstance(p.statements[0], ast.LocalStmt)
            self.assertIsInstance(p.statements[1], ast.LocalStmt)

    def test_chained_assignment(self):
        def test_assign(src, target_type, value_type, lexpos):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                self.assertIsInstance(p, ast.ChainedAssignmentStmt)
                self.assertLocation(p, (1,), lexpos)
                self.assertIsInstance(p.targets, tuple)
                self.assertEqual(1, len(p.targets))
                self.assertIsInstance(p.targets[0], target_type)
                self.assertIsInstance(p.value, value_type)

        test_assign('foo = 1', ast.IdentifierExpr, ast.NumberLiteralExpr, (4,))
        test_assign('foo.bar = foo', ast.AttributeExpr, ast.IdentifierExpr,
                    (8,))
        test_assign('foo[bar] = 2*x+1', ast.SubscriptExpr, ast.BinaryOpExpr,
                    (9,))

        with self.parse('foo[bar] = foo.bar = foo = 1') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            self.assertIsInstance(p, ast.ChainedAssignmentStmt)
            self.assertLocation(p, (1,1,1), (25,19,9))
            
            self.assertIsInstance(p.targets, tuple)
            self.assertEqual(3, len(p.targets))
            self.assertIsInstance(p.targets[0], ast.IdentifierExpr)
            self.assertIsInstance(p.targets[1], ast.AttributeExpr)
            self.assertIsInstance(p.targets[2], ast.SubscriptExpr)
            
            self.assertEqual(self.one, p.value)

        with self.parse('1 = 2'):
            self.assertError(token='=')

        with self.parse('f(1) = 2'):
            self.assertError(token='=')

    def test_augmented_assignment(self):
        def test_op(op):
            def test_assign(src, target_type, value_type, lexpos):
                with self.parse(src % op) as p:
                    self.assertIsInstance(p, ast.Module)
                    self.assertEqual(1, len(p.statements))
                    p = p.statements[0]
                    self.assertIsInstance(p, ast.AugmentedAssignmentStmt)
                    self.assertLocation(p, 1, lexpos)
                    self.assertIsInstance(p.target, target_type)
                    self.assertEqual(op, p.op)
                    self.assertIsInstance(p.value, value_type)

            test_assign('foo %s 1',
                        ast.IdentifierExpr,
                        ast.NumberLiteralExpr,
                        4)
            test_assign('foo.bar %s foo',
                        ast.AttributeExpr,
                        ast.IdentifierExpr,
                        8)
            test_assign('foo[bar] %s 2*x+1',
                        ast.SubscriptExpr,
                        ast.BinaryOpExpr,
                        9)

        test_op('+=')
        test_op('-=')
        test_op('*=')
        test_op('/=')
        test_op('%=')
        test_op('**=')

        with self.parse('1 += 2'):
            self.assertError(token='+=')

        with self.parse('f(1) -= 2'):
            self.assertError(token='-=')

        with self.parse('x += y -= 2'):
            self.assertError(token='-=')

    def test_local_stmt(self):
        with self.parse('local foo = 1') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            self.assertIsInstance(p, ast.LocalStmt)
            self.assertLocation(p, 1, 0)
            self.assertEqual('foo', p.name)
            self.assertEqual(self.one, p.value)

        with self.parse('local bar\n'):
            self.assertError(token='\n')

    def test_simple_call_stmt(self):
        def test_call(src, target_type, args, lexpos):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                
                self.assertIsInstance(p, ast.CallStmt)
                self.assertLocation(p, 1, lexpos)
                self.assertIsInstance(p.head, ast.CallExpr)
                self.assertIsNone(p.body)
                self.assertIsNone(p.tail)

                p = p.head
                self.assertIsInstance(p.target, target_type)
                self.assertEqual(args, p.args)

        test_call('foo()', ast.IdentifierExpr, (), 3)
        test_call('a.b(1)', ast.AttributeExpr, (self.one,), 3)
        test_call('(x+2*y)(foo, [1,2],)',
                  ast.BinaryOpExpr,
                  (self.foo, self.array_12),
                  7)

        def od(*args):
            return collections.OrderedDict(zip(args[:-1:2], args[1::2]))

        # Named args
        test_call('foo(a=1)', ast.IdentifierExpr, od('a', self.one), 3)
        test_call('a.b(foo = foo, bar=[1,2],)',
                  ast.AttributeExpr,
                  od('foo', self.foo, 'bar', self.array_12),
                  3)

        with self.parse('foo(1, a=2)'):
            self.assertError(token='=')

        with self.parse('foo("a"=2)'):
            self.assertError(token='=')

    def test_simple_call_stmt_with_attribute_ref(self):
        with self.parse('foo(a = 1, b <- x.y)') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 1, 3)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsNone(p.body)
            self.assertIsNone(p.tail)

            p = p.head
            self.assertEqual(self.foo, p.target)
            self.assertIsInstance(p.args, collections.OrderedDict)
            args = tuple(p.args.items())

            self.assertEqual('a', args[0][0])
            self.assertEqual(self.one, args[0][1])
            self.assertEqual('b', args[1][0])
            p = args[1][1]

            self.assertIsInstance(p, ast.AttributeReferenceExpr)
            self.assertLocation(p, 1, 17)
            self.assertIsInstance(p.target, ast.IdentifierExpr)
            self.assertEqual('x', p.target.value)
            self.assertEqual('y', p.name)

        with self.parse('foo(a <- 2)'):
            self.assertError(token=')')

        with self.parse('foo(a <- x)'):
            self.assertError(token=')')

        with self.parse('foo(a <- x["y"])'):
            self.assertError(token=')')

    def test_compound_call_stmt(self):
        with self.parse('''
                        foo ():
                        end
                        ''') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 2, 29)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(0, len(p.body))
            self.assertIsNone(p.tail)

        with self.parse('''
                        when (eye_in_window and not eye_in_saccade):
                            present_stimulus()
                        else after (500ms):
                            print('No fixation')
                            no_fixation()
                        end
                        ''') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 2, 30)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(1, len(p.body))
            self.assertIsInstance(p.tail, ast.CallStmt)
            p = p.tail
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 4, 152)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(2, len(p.body))
            self.assertIsNone(p.tail)

        with self.parse('''
                        if (x > 2):
                            local y = 2*x
                            do_something(y)
                        else if (x < -1):
                            error()
                        else if (2*y == foo):
                            # No idea what to do here!
                        else:
                            call_for_help()
                        end
                        ''') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 2, 28)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(2, len(p.body))
            self.assertIsInstance(p.tail, ast.CallStmt)
            p = p.tail
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 5, 155)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(1, len(p.body))
            self.assertIsInstance(p.tail, ast.CallStmt)
            p = p.tail
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertLocation(p, 7, 233)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(0, len(p.body))
            self.assertIsInstance(p.tail, tuple)
            self.assertEqual(1, len(p.tail))

        with self.parse('''
                        if (x):
                        else:
                        else:
                        end
                        ''') as p:
            self.assertError(token='else')

    def test_function_stmt(self):
        def test_func(src, name, args, num_stmts, local=False):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                self.assertIsInstance(p, ast.FunctionStmt)
                self.assertLocation(p, 2, (25 if local else 19))
                self.assertEqual(name, p.name)
                self.assertEqual(args, p.args)
                self.assertIsInstance(p.body, tuple)
                self.assertEqual(num_stmts, len(p.body))
                self.assertEqual(local, p.local)

        test_func('''
                  function foo():
                  end
                  ''', 'foo', (), 0)

        test_func('''
                  local function square(x):
                      return x*x
                  end
                  ''', 'square', ('x',), 1, True)

        test_func('''
                  function roots(a, b, c,):
                      local d = math.sqrt(b**2 - 4*a*c)
                      local r1 = (-b + d) / (2*a)
                      local r2 = (-b - d) / (2*a)
                      return [r1, r2]
                  end
                  ''', 'roots', ('a', 'b', 'c'), 4)

    def test_return_stmt(self):
        def test_return(src, value):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                self.assertIsInstance(p, ast.ReturnStmt)
                self.assertLocation(p, 1, 0)
                self.assertEqual(value, p.value)

        test_return('return foo', self.foo)
        test_return('return [1,2]', self.array_12)
        test_return('return', None)

    def test_function_expr(self):
        def test_func(src, args, expr_type):
            with self.parse('local f = ' + src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                self.assertIsInstance(p, ast.LocalStmt)
                self.assertIsInstance(p.value, ast.FunctionExpr)
                p = p.value
                self.assertLocation(p, 1, 10)
                self.assertEqual(args, p.args)
                self.assertIsInstance(p.body, expr_type)

        test_func('function () true end', (), ast.BooleanLiteralExpr)
        test_func('function (x) x*x end', ('x',), ast.BinaryOpExpr)
        test_func('function (foo, bar) foo < bar < 5 end',
                  ('foo', 'bar'),
                  ast.ComparisonExpr)

        with self.parse('function () end'):
            self.assertError(token='end')

    def test_array_item_range(self):
        with self.parse('local arr = [1, 2:(1+2), foo:3:f(4), 2]') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            
            self.assertIsInstance(p, ast.LocalStmt)
            self.assertIsInstance(p.value, ast.ArrayLiteralExpr)
            items = p.value.items
            self.assertEqual(4, len(items))
            self.assertEqual(self.one, items[0])
            self.assertEqual(self.two, items[3])

            p = items[1]
            self.assertIsInstance(p, ast.ArrayItemRange)
            self.assertLocation(p, 1, 17)
            self.assertEqual(self.two, p.start)
            self.assertIsInstance(p.stop, ast.BinaryOpExpr)
            self.assertIsNone(p.step)

            p = items[2]
            self.assertIsInstance(p, ast.ArrayItemRange)
            self.assertLocation(p, 1, 28)
            self.assertEqual(self.foo, p.start)
            self.assertEqual(self.three, p.stop)
            self.assertIsInstance(p.step, ast.CallExpr)
