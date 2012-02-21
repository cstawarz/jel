from __future__ import division, print_function, unicode_literals
import inspect
import os

from ply import yacc

from . import ast


class JELParser(object):

    def __init__(self, tokens):
        self.tokens = tokens
        
        # PLY demands that start be str, not unicode
        self.start = str(self.get_start())

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

    def get_start(self):
        return 'expr'

    def same(self, p):
        assert len(p) == 2
        p[0] = p[1]

    def unary_op(self, p):
        if len(p) == 3:
            p[0] = ast.UnaryOpExpr(op=p[1], operand=p[2])
        else:
            self.same(p)

    def binary_op(self, p):
        if len(p) == 4:
            p[0] = ast.BinaryOpExpr(op=p[2], operands=(p[1], p[3]))
        else:
            self.same(p)

    def p_expr(self, p):
        '''
        expr : or_expr
        '''
        self.same(p)

    def p_or_expr(self, p):
        '''
        or_expr : or_expr OR and_expr
                | and_expr
        '''
        self.binary_op(p)

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

    def p_comparison_expr(self, p):
        '''
        comparison_expr : comparison_expr comparison_op additive_expr
                        | additive_expr
        '''
        self.binary_op(p)

    def p_comparison_op(self, p):
        '''
        comparison_op : LESSTHAN
                      | LESSTHANOREQUAL
                      | GREATERTHAN
                      | GREATERTHANOREQUAL
                      | NOTEQUAL
                      | EQUAL
                      | IN
                      | NOT IN
        '''
        p[0] = ' '.join(p[1:])

    def p_additive_expr(self, p):
        '''
        additive_expr : additive_expr PLUS multiplicative_expr
                      | additive_expr MINUS multiplicative_expr
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
        unary_expr : PLUS unary_expr
                   | MINUS unary_expr
                   | exponentiation_expr
        '''
        self.unary_op(p)

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
        raise NotImplementedError

    def p_subscript_expr(self, p):
        '''
        subscript_expr : postfix_expr LBRACKET expr RBRACKET
        '''
        raise NotImplementedError

    def p_attribute_expr(self, p):
        '''
        attribute_expr : postfix_expr DOT identifier_expr
        '''
        raise NotImplementedError

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
        raise NotImplementedError

    def p_dict_item_list(self, p):
        '''
        dict_item_list : dict_item COMMA dict_item_list
                       | dict_item
                       | empty
        '''
        raise NotImplementedError

    def p_dict_item(self, p):
        '''
        dict_item : dict_key COLON expr
        '''
        raise NotImplementedError

    def p_dict_key(self, p):
        '''
        dict_key : string_literal_expr
                 | identifier_expr
        '''
        self.same(p)

    def p_list_literal_expr(self, p):
        '''
        list_literal_expr : LBRACKET expr_list RBRACKET
        '''
        raise NotImplementedError

    def p_expr_list(self, p):
        '''
        expr_list : expr COMMA expr_list
                  | expr
                  | empty
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_string_literal_expr(self, p):
        '''
        string_literal_expr : STRING string_literal_expr
                            | STRING
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_number_literal_expr(self, p):
        '''
        number_literal_expr : NUMBER
        '''
        p[0] = ast.NumberLiteralExpr(value=p[1])

    def p_boolean_literal_expr(self, p):
        '''
        boolean_literal_expr : TRUE
                             | FALSE
        '''
        self.same(p)

    def p_null_literal_expr(self, p):
        '''
        null_literal_expr : NULL
        '''
        self.same(p)

    def p_identifier_expr(self, p):
        '''
        identifier_expr : IDENTIFIER
        '''
        self.same(p)

    def p_empty(self, p):
        '''
        empty :
        '''
        pass

    def p_error(self, p):
        raise NotImplementedError

    @classmethod
    def print_grammar(cls):
        p_funcs = sorted((getattr(cls, f) for f in dir(cls)
                          if f.startswith('p_')),
                         key = (lambda f: f.im_func.func_code.co_firstlineno))

        for prod in (f.__doc__ for f in p_funcs if f.__doc__):
            prod = prod.split(':')
            lhs = prod[0].strip()
            rhs = [rule.strip() for rule in prod[1].split('|')]
            
            print(lhs, end=('\n    : ' if (len(rhs) > 1) else ' : '))
            print('\n    | '.join(rhs))
            print()


if __name__ == '__main__':
    JELParser.print_grammar()