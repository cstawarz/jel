from __future__ import division, print_function, unicode_literals
import collections

import ply.lex as lex
from ply.lex import TOKEN


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
        return lex.lex(object=self, **kwargs)

    def get_string_tokens(self):
        return {
            't_NUMBER': (
                r'-?'				# Sign
                r'(([1-9][0-9]+)|[0-9])'	# Integer
                r'(\.[0-9]+)?'			# Fraction
                r'([eE][+-]?[0-9]+)?'		# Exponent
                ),
            
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


if __name__ == '__main__':
    import sys

    o = JELLexer()
    l = o.build()
    
    if not sys.flags.interactive:
        o.print_errors = True
        lex.runmain(l)
