from __future__ import division, print_function, unicode_literals

import ply.lex as lex
from ply.lex import TOKEN


class JELLexer(object):

    @classmethod
    def build(cls, **kwargs):
        return lex.lex(object=cls(), **kwargs)
        
    def __init__(self):
        self.__dict__.update(self.get_string_tokens())
        self.tokens = tuple(t[2:] for t in dir(self)
                            if t.startswith('t_') and t[2:].isupper())

        self.keywords = self.get_keywords()
        self.tokens += tuple(k.upper() for k in self.keywords)

        self.t_ignore = self.get_ignore()

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
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    def t_error(self, t):
        print('illegal character: %r' % t.value[0])
        t.lexer.skip(1)


if __name__ == '__main__':
    lex.runmain(JELLexer.build())
