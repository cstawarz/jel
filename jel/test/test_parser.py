from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager
import decimal
import unittest

from .. import ast
from ..lexer import Lexer
from ..parser import Parser


class TestParser(unittest.TestCase):

    def setUp(self):
        self.errors = collections.deque()
        def error_logger(*info):
            self.errors.append(info)
            
        l = Lexer(error_logger)
        p = Parser(l.tokens, error_logger)
        self.lexer = l.build()
        self.parser = p.build()

        @contextmanager
        def parse_wrapper(s):
            yield self.parser.parse(s, lexer=self.lexer)
            if self.errors:
                self.fail('input contained unexpected errors: ' +
                          ', '.join(repr(e) for e in self.errors))

        self.parse = parse_wrapper

        self.foo = ast.IdentifierExpr(value='foo')
        self.null = ast.NullLiteralExpr()
        self.true = ast.BooleanLiteralExpr(value=True)
        self.false = ast.BooleanLiteralExpr(value=False)
        self.foobar = ast.StringLiteralExpr(value='foobar')

        def make_number(value, tag=None):
            return ast.NumberLiteralExpr(value = decimal.Decimal(value),
                                         tag = tag)
        self.one = make_number('1')
        self.two = make_number('2')
        self.three = make_number('3')
        
        self.list_12 = ast.ListLiteralExpr(items=(self.one, self.two))
        self.empty_list = ast.ListLiteralExpr(items=())

    def assertError(self, msg=None, token=None, lineno=None, lexpos=None):
        self.assertTrue(self.errors, 'expected error was not detected')
        e = self.errors.popleft()

        if msg:
            self.assertEqual(msg, e[0])
        if token:
            self.assertEqual(token, e[1])
        if lineno:
            self.assertEqual(lineno, e[2])
        if lexpos:
            self.assertEqual(lexpos, e[3])

    def test_incomplete_input(self):
        with self.parse('"foo') as p:
            self.assertError(msg='Input ended unexpectedly')
            self.assertIsNone(p)

    def test_identifier_expr(self):
        with self.parse('foo') as p:
            self.assertIsInstance(p, ast.IdentifierExpr)
            self.assertEqual('foo', p.value)

    def test_null_literal_expr(self):
        with self.parse('null') as p:
            self.assertIsInstance(p, ast.NullLiteralExpr)

    def test_true_literal_expr(self):
        with self.parse('true') as p:
            self.assertIsInstance(p, ast.BooleanLiteralExpr)
            self.assertIs(True, p.value)

    def test_false_literal_expr(self):
        with self.parse('false') as p:
            self.assertIsInstance(p, ast.BooleanLiteralExpr)
            self.assertIs(False, p.value)

    def test_number_literal_expr(self):
        with self.parse('123') as p:
            self.assertIsInstance(p, ast.NumberLiteralExpr)
            self.assertIsInstance(p.value, decimal.Decimal)
            self.assertEqual('123', str(p.value))
            self.assertEqual(123, int(p.value))
            self.assertIsNone(p.tag)
            
        with self.parse('1.230E-45ms') as p:
            self.assertIsInstance(p, ast.NumberLiteralExpr)
            self.assertIsInstance(p.value, decimal.Decimal)
            self.assertEqual('1.230E-45', str(p.value))
            self.assertEqual(1.23e-45, float(p.value))
            self.assertEqual('ms', p.tag)

    def test_string_literal_expr(self):
        with self.parse('"foo bar\\nblah"') as p:
            self.assertIsInstance(p, ast.StringLiteralExpr)
            self.assertEqual('foo bar\nblah', p.value)

        s = ''' 'foo\\n' "bar\\tboo" """blah\nbaz\\r""" \'''\\ffuzz\ncuz\''' '''
        
        with self.parse(s) as p:
            self.assertIsInstance(p, ast.StringLiteralExpr)
            self.assertEqual('foo\nbar\tbooblah\nbaz\r\ffuzz\ncuz', p.value)

    def test_list_literal_expr(self):
        def test_list(expr, *items):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.ListLiteralExpr)
                self.assertIsInstance(p.items, tuple)
                self.assertEqual(items, p.items)

        null_lit = ast.NullLiteralExpr()
        true_lit = ast.BooleanLiteralExpr(value=True)
        false_lit = ast.BooleanLiteralExpr(value=False)

        test_list('[]')
        test_list('[null]', null_lit)
        test_list('[null,]', null_lit)
        test_list('[true, false]', true_lit, false_lit)
        test_list('[true, false,]', true_lit, false_lit)
        test_list('[true, false, null]', true_lit, false_lit, null_lit)
        test_list('[true, false, null,]', true_lit, false_lit, null_lit)

        with self.parse('[,]'):
            self.assertError(token=',')

    def test_dict_literal_expr(self):
        def test_dict(expr, *items):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.DictLiteralExpr)
                self.assertIsInstance(p.items, tuple)
                self.assertEqual(items, p.items)

        null_lit = ast.NullLiteralExpr()
        true_lit = ast.BooleanLiteralExpr(value=True)
        false_lit = ast.BooleanLiteralExpr(value=False)

        test_dict('{}')

        item = ('a', null_lit)
        test_dict('{"a": null}', item)
        test_dict('{a: null}', item)
        test_dict('{"a": null,}', item)
        test_dict('{a: null,}', item)

        items = (('foo', true_lit), ('bar', false_lit))
        test_dict("{'foo': true, bar: false}", *items)
        test_dict("{foo: true, 'bar': false,}", *items)

        items += (('blah', null_lit),)
        test_dict('{foo: true, bar: false, blah: null}', *items)

        with self.parse('{,}'):
            self.assertError(token=',')

        with self.parse('{"foo"}'):
            self.assertError(token='}')

    def test_parenthetic_expr(self):
        with self.parse('([null])') as p:
            expected = ast.ListLiteralExpr(items=(ast.NullLiteralExpr(),))
            self.assertEqual(expected, p)
            
        with self.parse('([null],)'):
            self.assertError(token=',')
            
        with self.parse('(true, false)'):
            self.assertError(token=',')
            
        with self.parse('()'):
            self.assertError(token=')')

    def test_attribute_expr(self):
        def test_attr(expr, target, name):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.AttributeExpr)
                self.assertEqual(target, p.target)
                self.assertIsInstance(p.name, type(''))
                self.assertEqual(name, p.name)

        id_lit = ast.IdentifierExpr(value='foo')

        test_attr('foo.bar', id_lit, 'bar')
        test_attr('(foo).blah', id_lit, 'blah')
        test_attr(
            '{foo123: null}.foo123',
            ast.DictLiteralExpr(items=(('foo123', ast.NullLiteralExpr()),)),
            'foo123')

        test_attr('foo.bar.blah',
                  ast.AttributeExpr(target=id_lit, name='bar'),
                  'blah')

        with self.parse('foo.1'):
            self.assertError(token='1')

    def test_subscript_expr(self):
        def test_sub(expr, target, value):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.SubscriptExpr)
                self.assertEqual(target, p.target)
                self.assertEqual(value, p.value)

        test_sub('foo[1]', self.foo, self.one)
        test_sub('(foo)[[]]', self.foo, self.empty_list)
        test_sub('[1,2]["foobar"]', self.list_12, self.foobar)

        test_sub('foo[1][2]',
                 ast.SubscriptExpr(target=self.foo, value=self.one),
                 self.two)

        with self.parse('foo[]'):
            self.assertError(token=']')

        with self.parse('foo[1,2]'):
            self.assertError(token=',')

        with self.parse('foo[,]'):
            self.assertError(token=',')

    def test_call_expr(self):
        def test_call(expr, name, *args):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.CallExpr)
                self.assertIsInstance(p.target, ast.IdentifierExpr)
                self.assertEqual(name, p.target.value)
                self.assertEqual(args, p.args)

        test_call('foo()', 'foo')
        test_call('bar(true)', 'bar', self.true)
        test_call('bar(true,)', 'bar', self.true)
        test_call('abc123(1, 2)', 'abc123', self.one, self.two)
        test_call('abc123(1, 2,)', 'abc123', self.one, self.two)
        test_call('(foo)(2)', 'foo', self.two)

        with self.parse('foo(,)'):
            self.assertError(token=',')

        with self.parse('foo(1)(2)') as outer:
            self.assertIsInstance(outer, ast.CallExpr)
            self.assertEqual((self.two,), outer.args)
            inner = outer.target
            self.assertIsInstance(inner, ast.CallExpr)
            self.assertIsInstance(inner.target, ast.IdentifierExpr)
            self.assertEqual('foo', inner.target.value)
            self.assertEqual((self.one,), inner.args)

    def _test_binary_op(self, op, sibling_ops=(), left_assoc=True):
        def test_binop(expr, *operands):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.BinaryOpExpr)
                self.assertEqual(op, p.op)
                assert len(operands) == 2
                self.assertEqual(operands, p.operands)
                
        test_binop('1 %s 2' % op, self.one, self.two)

        for other_op in (op,) + sibling_ops:
            if left_assoc:
                test_binop(
                    '1 %s 2 %s 3' % (other_op, op),
                    ast.BinaryOpExpr(op = other_op,
                                     operands = (self.one, self.two)),
                    self.three,
                    )
            else:
                test_binop(
                    '1 %s 2 %s 3' % (op, other_op),
                    self.one,
                    ast.BinaryOpExpr(op = other_op,
                                     operands = (self.two, self.three)),
                    )

    def _test_unary_op(self, op):
        def test_unop(expr, operand):
            with self.parse(expr) as p:
                self.assertIsInstance(p, ast.UnaryOpExpr)
                self.assertEqual(op, p.op)
                self.assertEqual(operand, p.operand)
                
        test_unop('%s 1' % op, self.one)
        test_unop(
            '%s %s 2' % (op, op),
            ast.UnaryOpExpr(op=op, operand=self.two),
            )

    def test_exponentiation_expr(self):
        self._test_binary_op('**', left_assoc=False)

        with self.parse('2**-1') as p:
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('**', p.op)
            self.assertEqual((self.two,
                              ast.UnaryOpExpr(op='-', operand=self.one)),
                             p.operands)

    def test_unary_expr(self):
        self._test_unary_op('+')
        self._test_unary_op('-')

    def test_multiplicative_expr(self):
        self._test_binary_op('*', ('/', '%'))
        self._test_binary_op('/', ('*', '%'))
        self._test_binary_op('%', ('*', '/'))

    def test_additive_expr(self):
        self._test_binary_op('+', ('-',))
        self._test_binary_op('-', ('+',))

    def test_comparison_expr(self):
        def test_comp(op):
            with self.parse('1 %s 2' % op) as p:
                self.assertIsInstance(p, ast.ComparisonExpr)
                self.assertEqual((op,), p.ops)
                self.assertEqual((self.one, self.two), p.operands)

        test_comp('<')
        test_comp('<=')
        test_comp('>')
        test_comp('>=')
        test_comp('!=')
        test_comp('==')
        test_comp('in')
        test_comp('not in')

        with self.parse('1 < 2 <= 3 not in [1,2]') as p:
            self.assertIsInstance(p, ast.ComparisonExpr)
            self.assertEqual(('<', '<=', 'not in'), p.ops)
            self.assertEqual((self.one, self.two, self.three, self.list_12),
                             p.operands)

        # Parentheses break comparison chaining
        with self.parse('(1 < 2) != (1 > 3)') as p:
            self.assertIsInstance(p, ast.ComparisonExpr)
            self.assertEqual(('!=',), p.ops)
            self.assertEqual(
                (
                    ast.ComparisonExpr(ops=('<',),
                                       operands=(self.one, self.two)),
                    ast.ComparisonExpr(ops=('>',),
                                       operands=(self.one, self.three)),
                    ),
                p.operands,
                )

    def test_not_expr(self):
        self._test_unary_op('not')

    def test_and_expr(self):
        self._test_binary_op('and')

    def test_or_expr(self):
        self._test_binary_op('or')

    def test_precedence(self):
        x = ast.IdentifierExpr(value='x')
        with self.parse('x or x and not x < x + x * -x ** (x or x) [x]') as p:
            # or
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('or', p.op)
            self.assertEqual(x, p.operands[0])
            p = p.operands[1]
            
            # and
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('and', p.op)
            self.assertEqual(x, p.operands[0])
            p = p.operands[1]

            # not
            self.assertIsInstance(p, ast.UnaryOpExpr)
            self.assertEqual('not', p.op)
            p = p.operand
            
            # <
            self.assertIsInstance(p, ast.ComparisonExpr)
            self.assertEqual(('<',), p.ops)
            self.assertEqual(x, p.operands[0])
            p = p.operands[1]
            
            # +
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('+', p.op)
            self.assertEqual(x, p.operands[0])
            p = p.operands[1]
            
            # *
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('*', p.op)
            self.assertEqual(x, p.operands[0])
            p = p.operands[1]

            # -
            self.assertIsInstance(p, ast.UnaryOpExpr)
            self.assertEqual('-', p.op)
            p = p.operand
            
            # **
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('**', p.op)
            self.assertEqual(x, p.operands[0])
            p = p.operands[1]
            
            # []
            self.assertIsInstance(p, ast.SubscriptExpr)
            self.assertEqual(x, p.value)
            p = p.target
            
            # ()
            self.assertIsInstance(p, ast.BinaryOpExpr)
            self.assertEqual('or', p.op)
            self.assertEqual((x, x), p.operands)
