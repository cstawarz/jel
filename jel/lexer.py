from __future__ import division, print_function, unicode_literals

from ply import lex
from ply.lex import TOKEN


class MatchString(unicode):

    def __new__(cls, value, groupdict):
        return super(MatchString, cls).__new__(cls, value)

    def __init__(self, value, groupdict):
        super(MatchString, self).__init__(value)
        self.__dict__.update(groupdict)


class JELLexer(object):

    def __init__(self, error_logger):
        self.error_logger = error_logger
        
        self.tokens = tuple(t for t in
                            (t.split('_')[-1] for t in dir(self)
                             if t.startswith('t_'))
                            if t.isupper())
        self.tokens += tuple(k.upper() for k in self.keywords)

    def build(self, **kwargs):
        return lex.lex(module=self, **kwargs)

    states = (
        ('lbrace', 'inclusive'),
        ('lbracket', 'inclusive'),
        ('lparen', 'inclusive'),
        )

    t_COLON = r':'
    t_COMMA = r','
    t_DIVIDE = r'/'
    t_DOT = r'\.'
    t_EQUAL = r'=='
    t_GREATERTHAN = r'>'
    t_GREATERTHANOREQUAL = r'>='
    t_LESSTHAN = r'<'
    t_LESSTHANOREQUAL = r'<='
    t_MINUS = r'-'
    t_MODULO = r'%'
    t_NOTEQUAL = r'!='
    t_PLUS = r'\+'
    t_POWER = r'\*\*'
    t_TIMES = r'\*'

    t_ignore = ' \t'

    keywords = ('and', 'false', 'in', 'not', 'null', 'or', 'true')

    def update_lineno(self, t):
        t.lexer.lineno += t.value.count('\n')

    @TOKEN(
        r"('''(.|\n)*?(?<!\\)''')"	# Multiline single quotes
        r'|("""(.|\n)*?(?<!\\)""")'	# Multiline double quotes
        r"|('[^\n]*?(?<!\\)')"		# Single quotes
        r'|("[^\n]*?(?<!\\)")'		# Double quotes
        )
    def t_STRING(self, t):
        self.update_lineno(t)
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
        t.lexer.push_state(t.type.lower())
        return t

    def end_grouping(self, t):
        t.lexer.pop_state()
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

    def t_lbrace_RBRACE(self, t):
        r'\}'
        return self.end_grouping(t)

    def t_lbracket_RBRACKET(self, t):
        r'\]'
        return self.end_grouping(t)

    def t_lparen_RPAREN(self, t):
        r'\)'
        return self.end_grouping(t)

    newline_re = r'(\\[%s]*\n)|(\n+)' % repr(t_ignore)[1:-1]

    @TOKEN(newline_re)
    def t_lbrace_lbracket_lparen_newline(self, t):
        self.update_lineno(t)

    @TOKEN(newline_re)
    def t_NEWLINE(self, t):
        self.update_lineno(t)
        # Discard escaped newlines
        if t.value[0] != '\\':
            return t

    def t_error(self, t):
        bad_char = t.value[0]
        self.error_logger(bad_char, t.lexer.lineno, t.lexer.lexpos,
                          'Illegal character: %r' % bad_char)
        t.lexer.skip(1)
