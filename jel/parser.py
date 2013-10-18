from __future__ import division, print_function, unicode_literals
import collections
import decimal
import inspect
import os

from ply import yacc

from . import ast


class Parser(object):

    def __init__(self, tokens, error_logger):
        self.tokens = tokens
        self.error_logger = error_logger

    def build(self, debug=False, **kwargs):
        # Name the parsing table module 'yacctab' and store it in the
        # same directory as the file where the current class is
        # defined
        tabmodule = type(self).__module__.split('.')
        tabmodule[-1] = 'yacctab'
        tabmodule = '.'.join(tabmodule)
        outputdir = os.path.dirname(inspect.getfile(type(self)))
        
        return yacc.yacc(
            debug = debug,
            module = self,
            tabmodule = tabmodule,
            outputdir = outputdir,
            **kwargs
            )

    def p_expr(self, p):
        '''
        expr : or_expr
        '''
        self.same(p)

    def same(self, p):
        assert len(p) == 2
        p[0] = p[1]

    def p_or_expr(self, p):
        '''
        or_expr : or_expr OR and_expr
        '''
        self.logical_op(p, ast.OrExpr)

    def logical_op(self, p, node_type):
        if isinstance(p[1], node_type):
            p[1].lineno += (p.lineno(2),)
            p[1].lexpos += (p.lexpos(2),)
            p[0] = p[1]
        else:
            p[0] = node_type((p.lineno(2),), (p.lexpos(2),), operands=(p[1],))

        if isinstance(p[3], node_type):
            p[0].lineno += p[3].lineno
            p[0].lexpos += p[3].lexpos
            p[0].operands += p[3].operands
        else:
            p[0].operands += (p[3],)

    def p_or_expr_passthrough(self, p):
        '''
        or_expr : and_expr
        '''
        self.same(p)

    def p_and_expr(self, p):
        '''
        and_expr : and_expr AND not_expr
        '''
        self.logical_op(p, ast.AndExpr)

    def p_and_expr_passthrough(self, p):
        '''
        and_expr : not_expr
        '''
        self.same(p)

    def p_not_expr(self, p):
        '''
        not_expr : NOT not_expr
                 | comparison_expr
        '''
        self.unary_op(p)

    def unary_op(self, p):
        if len(p) == 3:
            p[0] = ast.UnaryOpExpr(p.lineno(1),
                                   p.lexpos(1),
                                   op = p[1],
                                   operand = p[2])
        else:
            self.same(p)

    def p_comparison_expr(self, p):
        '''
        comparison_expr : comparison_expr COMPARISONOP additive_expr
        '''
        self.comparison_op(p)

    def comparison_op(self, p):
        if isinstance(p[1], ast.ComparisonExpr) and (not p[1]._parenthetic):
            p[1].lineno += (p.lineno(2),)
            p[1].lexpos += (p.lexpos(2),)
            p[1].ops += (p[2],)
            p[1].operands += (p[3],)
            p[0] = p[1]
        else:
            p[0] = ast.ComparisonExpr((p.lineno(2),),
                                      (p.lexpos(2),),
                                      ops = (p[2],),
                                      operands = (p[1], p[3]))

    def p_comparison_expr_in(self, p):
        '''
        comparison_expr : comparison_expr IN additive_expr
        '''
        self.comparison_op(p)

    def p_comparison_expr_not_in(self, p):
        '''
        comparison_expr : comparison_expr NOT IN additive_expr
        '''
        p[2] = 'not in'
        p[3] = p[4]
        self.comparison_op(p)

    def p_comparison_expr_passthrough(self, p):
        '''
        comparison_expr : additive_expr
        '''
        self.same(p)

    def p_additive_expr(self, p):
        '''
        additive_expr : additive_expr ADDITIVEOP multiplicative_expr
                      | multiplicative_expr
        '''
        self.binary_op(p)

    def binary_op(self, p):
        if len(p) == 4:
            p[0] = ast.BinaryOpExpr(p.lineno(2),
                                    p.lexpos(2),
                                    op = p[2],
                                    operands = (p[1], p[3]))
        else:
            self.same(p)

    def p_multiplicative_expr(self, p):
        '''
        multiplicative_expr : multiplicative_expr MULTIPLICATIVEOP unary_expr
                            | unary_expr
        '''
        self.binary_op(p)

    def p_unary_expr(self, p):
        '''
        unary_expr : ADDITIVEOP unary_expr
                   | exponentiation_expr
        '''
        self.unary_op(p)

    def p_exponentiation_expr(self, p):
        '''
        exponentiation_expr : postfix_expr POWER unary_expr
                            | postfix_expr
        '''
        self.binary_op(p)

    def p_postfix_expr(self, p):
        '''
        postfix_expr : call_expr
                     | subscript_expr
                     | attribute_expr
                     | primary_expr
        '''
        self.same(p)

    def p_call_expr(self, p):
        '''
        call_expr : postfix_expr LPAREN call_arg_list RPAREN
        '''
        p[0] = ast.CallExpr(p.lineno(2),
                            p.lexpos(2),
                            target = p[1],
                            args = p[3])

    def p_call_arg_list(self, p):
        '''
        call_arg_list : expr_list
        '''
        self.same(p)

    def p_expr_list(self, p):
        '''
        expr_list : expr COMMA expr_list
                  | expr
                  | empty
        '''
        self.item_list(p)

    def p_subscript_expr(self, p):
        '''
        subscript_expr : postfix_expr LBRACKET expr RBRACKET
        '''
        p[0] = ast.SubscriptExpr(p.lineno(2),
                                 p.lexpos(2),
                                 target = p[1],
                                 value = p[3])

    def p_attribute_expr(self, p):
        '''
        attribute_expr : postfix_expr DOT identifier_expr
        '''
        p[0] = ast.AttributeExpr(p.lineno(2),
                                 p.lexpos(2),
                                 target = p[1],
                                 name = p[3].value)

    def p_primary_expr(self, p):
        '''
        primary_expr : parenthetic_expr
                     | literal_expr
                     | identifier_expr
        '''
        self.same(p)

    def p_parenthetic_expr(self, p):
        '''
        parenthetic_expr : LPAREN expr RPAREN
        '''
        p[2]._parenthetic = True
        p[0] = p[2]

    def p_literal_expr(self, p):
        '''
        literal_expr : object_literal_expr
                     | array_literal_expr
                     | string_literal_expr
                     | number_literal_expr
                     | boolean_literal_expr
                     | null_literal_expr
        '''
        self.same(p)

    def p_object_literal_expr(self, p):
        '''
        object_literal_expr : LBRACE object_item_list RBRACE
        '''
        p[0] = ast.ObjectLiteralExpr(p.lineno(1),
                                     p.lexpos(1),
                                     items = collections.OrderedDict(p[2]))

    def p_object_item_list(self, p):
        '''
        object_item_list : object_item COMMA object_item_list
                         | object_item
                         | empty
        '''
        self.item_list(p)

    def item_list(self, p):
        if len(p) == 4:
            p[0] = (p[1],) + p[3]
        else:
            assert len(p) == 2
            p[0] = (() if p[1] is None else (p[1],))

    def p_object_item(self, p):
        '''
        object_item : object_key COLON expr
        '''
        p[0] = (p[1], p[3])

    def p_object_key(self, p):
        '''
        object_key : string_literal_expr
                   | identifier_expr
        '''
        p[0] = p[1].value

    def p_array_literal_expr(self, p):
        '''
        array_literal_expr : LBRACKET array_item_list RBRACKET
        '''
        p[0] = ast.ArrayLiteralExpr(p.lineno(1), p.lexpos(1), items=p[2])

    def p_array_item_list(self, p):
        '''
        array_item_list : array_item COMMA array_item_list
                        | array_item
                        | empty
        '''
        self.item_list(p)

    def p_array_item(self, p):
        '''
        array_item : expr
        '''
        self.same(p)

    def p_string_literal_expr(self, p):
        '''
        string_literal_expr : STRING string_literal_expr
                            | STRING
        '''
        value = p[1]
        if len(p) == 3:
            value += p[2].value
        p[0] = ast.StringLiteralExpr(p.lineno(1), p.lexpos(1), value=value)

    def p_number_literal_expr(self, p):
        '''
        number_literal_expr : NUMBER
        '''
        p[0] = ast.NumberLiteralExpr(p.lineno(1),
                                     p.lexpos(1),
                                     value = decimal.Decimal(p[1].value),
                                     tag = (p[1].tag or None))

    def p_boolean_literal_expr(self, p):
        '''
        boolean_literal_expr : TRUE
                             | FALSE
        '''
        p[0] = ast.BooleanLiteralExpr(p.lineno(1),
                                      p.lexpos(1),
                                      value = (p[1] == 'true'))

    def p_null_literal_expr(self, p):
        '''
        null_literal_expr : NULL
        '''
        p[0] = ast.NullLiteralExpr(p.lineno(1), p.lexpos(1))

    def p_identifier_expr(self, p):
        '''
        identifier_expr : IDENTIFIER
        '''
        p[0] = ast.IdentifierExpr(p.lineno(1), p.lexpos(1), value=p[1])

    def p_empty(self, p):
        '''
        empty :
        '''
        pass

    def p_error(self, p):
        if p is None:
            self.error_logger('Input ended unexpectedly')
        else:
            bad_token = p.value
            self.error_logger('Invalid syntax at %r' % str(bad_token),
                              bad_token, p.lineno, p.lexpos)

    @classmethod
    def print_grammar(cls):
        p_funcs = []
        for base in inspect.getmro(cls):
            p_funcs.extend(sorted((getattr(base, f) for f in base.__dict__
                                   if f.startswith('p_')),
                                  key=(lambda f: inspect.getsourcelines(f)[1])))

        prods = collections.OrderedDict()

        for p in (f.__doc__ for f in p_funcs if f.__doc__):
            p = p.split(':')
            lhs = p[0].strip()
            rhs = [rule.strip() for rule in p[1].split('|')]
            rhs = [' '.join(rule.split()) for rule in rhs]
            prods[lhs] = prods.pop(lhs, []) + rhs
            
        for lhs, rhs in prods.items():
            print(lhs, end=('\n    : ' if (len(rhs) > 1) else ' : '))
            print('\n    | '.join(rhs))
            print()
