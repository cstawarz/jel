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

    def test_chained_assignment(self):
        def test_assign(src, target_type, value_type):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                self.assertIsInstance(p, ast.ChainedAssignmentStmt)
                self.assertIsInstance(p.targets, tuple)
                self.assertEqual(1, len(p.targets))
                self.assertIsInstance(p.targets[0], target_type)
                self.assertIsInstance(p.value, value_type)

        test_assign('foo = 1', ast.IdentifierExpr, ast.NumberLiteralExpr)
        test_assign('foo.bar = foo', ast.AttributeExpr, ast.IdentifierExpr)
        test_assign('foo[bar] = 2*x+1', ast.SubscriptExpr, ast.BinaryOpExpr)

        with self.parse('foo[bar] = foo.bar = foo = 1') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            self.assertIsInstance(p, ast.ChainedAssignmentStmt)
            
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
            def test_assign(src, target_type, value_type):
                with self.parse(src % op) as p:
                    self.assertIsInstance(p, ast.Module)
                    self.assertEqual(1, len(p.statements))
                    p = p.statements[0]
                    self.assertIsInstance(p, ast.AugmentedAssignmentStmt)
                    self.assertIsInstance(p.target, target_type)
                    self.assertEqual(op, p.op)
                    self.assertIsInstance(p.value, value_type)

            test_assign('foo %s 1', ast.IdentifierExpr, ast.NumberLiteralExpr)
            test_assign('foo.bar %s foo', ast.AttributeExpr, ast.IdentifierExpr)
            test_assign('foo[bar] %s 2*x+1', ast.SubscriptExpr,
                        ast.BinaryOpExpr)

        test_op('+=')
        test_op('-=')

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
            self.assertEqual('foo', p.name)
            self.assertEqual(self.one, p.value)

        with self.parse('local bar\n'):
            self.assertError(token='\n')

    def test_simple_call_stmt(self):
        def test_call(src, target_type, args):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                
                self.assertIsInstance(p, ast.CallStmt)
                self.assertIsInstance(p.head, ast.CallExpr)
                self.assertIsNone(p.body)
                self.assertIsNone(p.tail)

                p = p.head
                self.assertIsInstance(p.target, target_type)
                self.assertEqual(args, p.args)

        test_call('foo()', ast.IdentifierExpr, ())
        test_call('a.b(1)', ast.AttributeExpr, (self.one,))
        test_call('(x+2*y)(foo, [1,2],)',
                  ast.BinaryOpExpr,
                  (self.foo, self.array_12))

        # Named args
        test_call('foo(a=1)', ast.IdentifierExpr, self.od('a', self.one))
        test_call('a.b(foo = foo, bar=[1,2],)',
                  ast.AttributeExpr,
                  self.od('foo', self.foo, 'bar', self.array_12))

        with self.parse('foo(1, a=2)'):
            self.assertError(token='=')

        with self.parse('foo("a"=2)'):
            self.assertError(token='=')

    @staticmethod
    def od(*args):
        return collections.OrderedDict(zip(args[:-1:2], args[1::2]))

    def test_compound_call_stmt(self):
        with self.parse('''
                        foo ():
                        end
                        ''') as p:
            self.assertIsInstance(p, ast.Module)
            self.assertEqual(1, len(p.statements))
            p = p.statements[0]
            
            self.assertIsInstance(p, ast.CallStmt)
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
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(1, len(p.body))
            self.assertIsInstance(p.tail, ast.CallStmt)
            p = p.tail
            
            self.assertIsInstance(p, ast.CallStmt)
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
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(2, len(p.body))
            self.assertIsInstance(p.tail, ast.CallStmt)
            p = p.tail
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(1, len(p.body))
            self.assertIsInstance(p.tail, ast.CallStmt)
            p = p.tail
            
            self.assertIsInstance(p, ast.CallStmt)
            self.assertIsInstance(p.head, ast.CallExpr)
            self.assertIsInstance(p.body, tuple)
            self.assertEqual(0, len(p.body))
            self.assertIsInstance(p.tail, tuple)
            self.assertEqual(1, len(p.tail))

    def test_return_stmt(self):
        def test_return(src, value):
            with self.parse(src) as p:
                self.assertIsInstance(p, ast.Module)
                self.assertEqual(1, len(p.statements))
                p = p.statements[0]
                self.assertIsInstance(p, ast.ReturnStmt)
                self.assertEqual(value, p.value)

        test_return('return foo', self.foo)
        test_return('return [1,2]', self.array_12)
        test_return('return', None)
