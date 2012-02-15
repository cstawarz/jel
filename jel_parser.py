from __future__ import division, print_function, unicode_literals
import collections

from ply import lex, yacc
from ply.lex import TOKEN


class MatchString(unicode):

    def __new__(cls, value, groupdict):
        return super(MatchString, cls).__new__(cls, value)

    def __init__(self, value, groupdict):
        super(MatchString, self).__init__(value)
        self.__dict__.update(groupdict)


class JELLexer(object):
        
    def __init__(self, print_errors=False):
        self.__dict__.update(self.get_string_tokens())
        self.tokens = tuple(t[2:] for t in dir(self)
                            if t.startswith('t_') and t[2:].isupper())

        self.keywords = self.get_keywords()
        self.tokens += tuple(k.upper() for k in self.keywords)

        self.t_ignore = self.get_ignore()

        self.errors = collections.deque()
        self.print_errors = print_errors

    def build(self, **kwargs):
        return lex.lex(module=self, **kwargs)

    def get_string_tokens(self):
        return {
            't_COLON'			: r':',
            't_COMMA'			: r',',
            't_DIVIDE'			: r'/',
            't_DOT'			: r'\.',
            't_EQUAL'			: r'==',
            't_GREATERTHAN'		: r'>',
            't_GREATERTHANOREQUAL'	: r'>=',
            't_LBRACE'			: r'\{',
            't_LBRACKET'		: r'\[',
            't_LESSTHAN'		: r'<',
            't_LESSTHANOREQUAL'		: r'<=',
            't_LPAREN'			: r'\(',
            't_MINUS'			: r'-',
            't_MODULO'			: r'%',
            't_NOTEQUAL'		: r'!=',
            't_PLUS'			: r'\+',
            't_POWER'			: r'\*\*',
            't_RBRACE'			: r'\}',
            't_RBRACKET'		: r'\]',
            't_RPAREN'			: r'\)',
            't_TIMES'			: r'\*',
            }

    def get_keywords(self):
        return ('and', 'false', 'in', 'not', 'null', 'or', 'true')

    def get_ignore(self):
        return ' \t'

    @TOKEN(
        r"('''(.|\n)*?(?<!\\)''')"	# Multiline single quotes
        r'|("""(.|\n)*?(?<!\\)""")'	# Multiline double quotes
        r"|('[^\n]*?(?<!\\)')"		# Single quotes
        r'|("[^\n]*?(?<!\\)")'		# Double quotes
        )
    def t_STRING(self, t):
        t.lexer.lineno += t.value.count('\n')
        return t

    @TOKEN(
        r'(?P<t_NUMBER_int>([1-9][0-9]+)|[0-9])'	# Integer
        r'(\.(?P<t_NUMBER_frac>[0-9]+))?'		# Fraction
        r'([eE](?P<t_NUMBER_exp>[+-]?[0-9]+))?'		# Exponent
        r'(?P<t_NUMBER_units>[a-zA-Z][a-zA-Z0-9]*)?'	# Units
        )
    def t_NUMBER(self, t):
        groupdict = dict((k.split('_')[2], v) for (k, v) in
                         t.lexer.lexmatch.groupdict('').iteritems()
                         if k.startswith('t_NUMBER_'))
        t.value = MatchString(t.value, groupdict)
        return t
        
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        
        if t.value in self.keywords:
            t.type = t.value.upper()
            
        return t
        
    def t_NEWLINE(self, t):
        r'(\\[ \t]*\n)|(\n+)'
        t.lexer.lineno += t.value.count('\n')
        if t.value[0] == '\\':
            # Discard escaped newlines
            return None
        return t

    def t_error(self, t):
        info = (t.value[0], t.lexer.lineno, t.lexer.lexpos)
        self.errors.append(info)
        if self.print_errors:
            print('Illegal character %r at line %d position %d' % info)
        t.lexer.skip(1)


class JELParser(object):

    def __init__(self, tokens):
        self.tokens = tokens
        
        # PLY demands that start be str, not unicode
        self.start = str(self.get_start())

    def build(self, **kwargs):
        return yacc.yacc(module=self, **kwargs)

    def get_start(self):
        return 'expr'

    def p_expr(self, p):
        '''
        expr : or_expr
        '''
        p[0] = p[1]

    def p_or_expr(self, p):
        '''
        or_expr : or_expr OR and_expr
                | and_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_and_expr(self, p):
        '''
        and_expr : and_expr AND not_expr
                 | not_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_not_expr(self, p):
        '''
        not_expr : NOT not_expr
                 | comparison_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_comparison_expr(self, p):
        '''
        comparison_expr : comparison_expr comparison_op additive_expr
                        | additive_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

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
        raise NotImplementedError

    def p_additive_expr(self, p):
        '''
        additive_expr : additive_expr PLUS multiplicative_expr
                      | additive_expr MINUS multiplicative_expr
                      | multiplicative_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_multiplicative_expr(self, p):
        '''
        multiplicative_expr : multiplicative_expr multiplicative_op unary_expr
                            | unary_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_multiplicative_op(self, p):
        '''
        multiplicative_op : TIMES
                          | DIVIDE
                          | MODULO
        '''
        raise NotImplementedError

    def p_unary_expr(self, p):
        '''
        unary_expr : PLUS unary_expr
                   | MINUS unary_expr
                   | exponentiation_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_exponentiation_expr(self, p):
        '''
        exponentiation_expr : postfix_expr POWER exponentiation_expr
                            | postfix_expr
        '''
        assert len(p) == 2
        p[0] = p[1]

    def p_postfix_expr(self, p):
        '''
        postfix_expr : function_call_expr
                     | subscript_expr
                     | attribute_expr
                     | primary_expr
        '''
        p[0] = p[1]

    def p_function_call_expr(self, p):
        '''
        function_call_expr : IDENTIFIER LPAREN expr_list RPAREN
        '''
        raise NotImplementedError

    def p_subscript_expr(self, p):
        '''
        subscript_expr : postfix_expr LBRACKET expr RBRACKET
        '''
        raise NotImplementedError

    def p_attribute_expr(self, p):
        '''
        attribute_expr : postfix_expr DOT IDENTIFIER
        '''
        raise NotImplementedError

    def p_primary_expr(self, p):
        '''
        primary_expr : parenthetic_expr
                     | literal_expr
                     | IDENTIFIER
        '''
        p[0] = p[1]

    def p_parenthetic_expr(self, p):
        '''
        parenthetic_expr : LPAREN expr RPAREN
        '''
        raise NotImplementedError

    def p_literal_expr(self, p):
        '''
        literal_expr : dict_literal_expr
                     | list_literal_expr
                     | string_literal_expr
                     | NUMBER
                     | TRUE
                     | FALSE
                     | NULL
        '''
        p[0] = p[1]

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
                 | IDENTIFIER
        '''
        p[0] = p[1]

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
            for line in prod.split('\n'):
                line = line[8:]  # Remove indentation
                if line:
                    print(line)
            print()


if __name__ == '__main__':
    import sys

    jl = JELLexer()
    jp = JELParser(jl.tokens)

    lexer = jl.build()
    parser = jp.build(write_tables=False)

    def parse(text):
        return parser.parse(text, lexer=lexer)
