from __future__ import division, print_function, unicode_literals
import collections
import decimal
import inspect
import os

from ply import yacc

from . import ast


class JELParser(object):

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
                | and_expr
        '''
        self.binary_op(p)

    def binary_op(self, p):
        if len(p) == 4:
            p[0] = ast.BinaryOpExpr(op=p[2], operands=(p[1], p[3]))
        else:
            self.same(p)

    def p_and_expr(self, p):
        '''
        and_expr : and_expr AND not_expr
                 | not_expr
        '''
        self.binary_op(p)

    def p_not_expr(self, p):
        '''
        not_expr : NOT not_expr
                 | comparison_expr
        '''
        self.unary_op(p)

    def unary_op(self, p):
        if len(p) == 3:
            p[0] = ast.UnaryOpExpr(op=p[1], operand=p[2])
        else:
            self.same(p)

    def p_comparison_expr(self, p):
        '''
        comparison_expr : comparison_expr comparison_op additive_expr
        '''
        if isinstance(p[1], ast.ComparisonExpr) and (not p[1]._parenthetic):
            ops = p[1].ops + (p[2],)
            operands = p[1].operands + (p[3],)
        else:
            ops = (p[2],)
            operands = (p[1], p[3])
        p[0] = ast.ComparisonExpr(ops=ops, operands=operands)

    def p_comparison_expr_passthrough(self, p):
        '''
        comparison_expr : additive_expr
        '''
        self.same(p)

    def p_comparison_op(self, p):
        '''
        comparison_op : LESSTHAN
                      | LESSTHANOREQUAL
                      | GREATERTHAN
                      | GREATERTHANOREQUAL
                      | NOTEQUAL
                      | EQUAL
                      | IN
        '''
        self.same(p)

    def p_comparison_op_NOT_IN(self, p):
        '''
        comparison_op : NOT IN
        '''
        p[0] = p[1] + ' ' + p[2]

    def p_additive_expr(self, p):
        '''
        additive_expr : additive_expr plus_or_minus multiplicative_expr
                      | multiplicative_expr
        '''
        self.binary_op(p)

    def p_multiplicative_expr(self, p):
        '''
        multiplicative_expr : multiplicative_expr multiplicative_op unary_expr
                            | unary_expr
        '''
        self.binary_op(p)

    def p_multiplicative_op(self, p):
        '''
        multiplicative_op : TIMES
                          | DIVIDE
                          | MODULO
        '''
        self.same(p)

    def p_unary_expr(self, p):
        '''
        unary_expr : plus_or_minus unary_expr
                   | exponentiation_expr
        '''
        self.unary_op(p)

    def p_plus_or_minus(self, p):
        '''
        plus_or_minus : PLUS
                      | MINUS
        '''
        self.same(p)

    def p_exponentiation_expr(self, p):
        '''
        exponentiation_expr : postfix_expr POWER exponentiation_expr
                            | postfix_expr
        '''
        self.binary_op(p)

    def p_postfix_expr(self, p):
        '''
        postfix_expr : function_call_expr
                     | subscript_expr
                     | attribute_expr
                     | primary_expr
        '''
        self.same(p)

    def p_function_call_expr(self, p):
        '''
        function_call_expr : identifier_expr LPAREN expr_list RPAREN
        '''
        p[0] = ast.FunctionCallExpr(name=p[1].value, args=p[3])

    def p_subscript_expr(self, p):
        '''
        subscript_expr : postfix_expr LBRACKET expr RBRACKET
        '''
        p[0] = ast.SubscriptExpr(target=p[1], value=p[3])

    def p_attribute_expr(self, p):
        '''
        attribute_expr : postfix_expr DOT identifier_expr
        '''
        p[0] = ast.AttributeExpr(target=p[1], name=p[3].value)

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
        literal_expr : dict_literal_expr
                     | list_literal_expr
                     | string_literal_expr
                     | number_literal_expr
                     | boolean_literal_expr
                     | null_literal_expr
        '''
        self.same(p)

    def p_dict_literal_expr(self, p):
        '''
        dict_literal_expr : LBRACE dict_item_list RBRACE
        '''
        p[0] = ast.DictLiteralExpr(items=p[2])

    def p_dict_item_list(self, p):
        '''
        dict_item_list : dict_item COMMA dict_item_list
                       | dict_item
                       | empty
        '''
        self.item_list(p)

    def item_list(self, p):
        if len(p) == 4:
            p[0] = (p[1],) + p[3]
        else:
            assert len(p) == 2
            p[0] = (() if p[1] is None else (p[1],))

    def p_dict_item(self, p):
        '''
        dict_item : dict_key COLON expr
        '''
        p[0] = (p[1], p[3])

    def p_dict_key(self, p):
        '''
        dict_key : string_literal_expr
                 | identifier_expr
        '''
        p[0] = p[1].value

    def p_list_literal_expr(self, p):
        '''
        list_literal_expr : LBRACKET expr_list RBRACKET
        '''
        p[0] = ast.ListLiteralExpr(items=p[2])

    def p_expr_list(self, p):
        '''
        expr_list : expr COMMA expr_list
                  | expr
                  | empty
        '''
        self.item_list(p)

    def p_string_literal_expr(self, p):
        '''
        string_literal_expr : STRING string_literal_expr
                            | STRING
        '''
        value = p[1]
        if len(p) == 3:
            value += p[2].value
        p[0] = ast.StringLiteralExpr(value=value)

    def p_number_literal_expr(self, p):
        '''
        number_literal_expr : NUMBER
        '''
        p[0] = ast.NumberLiteralExpr(value = decimal.Decimal(p[1].value),
                                     unit = (p[1].unit or None))

    def p_boolean_literal_expr(self, p):
        '''
        boolean_literal_expr : TRUE
                             | FALSE
        '''
        p[0] = ast.BooleanLiteralExpr(value = (p[1] == 'true'))

    def p_null_literal_expr(self, p):
        '''
        null_literal_expr : NULL
        '''
        p[0] = ast.NullLiteralExpr()

    def p_identifier_expr(self, p):
        '''
        identifier_expr : IDENTIFIER
        '''
        p[0] = ast.IdentifierExpr(value=p[1])

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
                              bad_token, p.lexer.lineno, p.lexer.lexpos)

    @classmethod
    def print_grammar(cls):
        p_funcs = sorted((getattr(cls, f) for f in dir(cls)
                          if f.startswith('p_')),
                         key = (lambda f: inspect.getsourcelines(f)[1]))

        prods = collections.OrderedDict()

        for p in (f.__doc__ for f in p_funcs if f.__doc__):
            p = p.split(':')
            lhs = p[0].strip()
            rhs = [rule.strip() for rule in p[1].split('|')]
            prods.setdefault(lhs, []).extend(rhs)
            
        for lhs, rhs in prods.items():
            print(lhs, end=('\n    : ' if (len(rhs) > 1) else ' : '))
            print('\n    | '.join(rhs))
            print()


if __name__ == '__main__':
    JELParser.print_grammar()
