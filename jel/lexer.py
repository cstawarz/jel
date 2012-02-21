from __future__ import division, print_function, unicode_literals
import collections

from ply import lex
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

        self.groupings = []
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
            't_LESSTHAN'		: r'<',
            't_LESSTHANOREQUAL'		: r'<=',
            't_MINUS'			: r'-',
            't_MODULO'			: r'%',
            't_NOTEQUAL'		: r'!=',
            't_PLUS'			: r'\+',
            't_POWER'			: r'\*\*',
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

    def begin_grouping(self, t):
        self.groupings.append(t.value)
        return t

    def end_grouping(self, t, start_token):
        if self.groupings and (self.groupings[-1] == start_token):
            self.groupings.pop()
        return t

    def t_LBRACE(self, t):
        r'\{'
        return self.begin_grouping(t)

    def t_LBRACKET(self, t):
        r'\['
        return self.begin_grouping(t)

    def t_LPAREN(self, t):
        r'\('
        return self.begin_grouping(t)

    def t_RBRACE(self, t):
        r'\}'
        return self.end_grouping(t, '{')

    def t_RBRACKET(self, t):
        r'\]'
        return self.end_grouping(t, '[')

    def t_RPAREN(self, t):
        r'\)'
        return self.end_grouping(t, '(')

    def t_NEWLINE(self, t):
        r'(\\[ \t]*\n)|(\n+)'
        t.lexer.lineno += t.value.count('\n')
        if self.groupings or (t.value[0] == '\\'):
            # Discard newlines inside groupings and escaped newlines
            return None
        return t

    def t_error(self, t):
        info = (t.value[0], t.lexer.lineno, t.lexer.lexpos)
        self.errors.append(info)
        if self.print_errors:
            print('Illegal character %r at line %d position %d' % info)
        t.lexer.skip(1)
