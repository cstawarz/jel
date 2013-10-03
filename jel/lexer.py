from __future__ import division, print_function, unicode_literals

from ply import lex
from ply.lex import TOKEN


class MatchString(type('')):

    def __new__(cls, value, groupdict):
        return super(MatchString, cls).__new__(cls, value)

    def __init__(self, value, groupdict):
        super(MatchString, self).__init__()
        self.__dict__.update(groupdict)


class Lexer(object):

    def __init__(self, error_logger):
        self.tokens += tuple(t for t in
                             (t.split('_')[-1] for t in dir(self)
                              if t.startswith('t_'))
                             if t.isupper())
        self.tokens += tuple(k.upper() for k in self.keywords)
        
        self.error_logger = error_logger

    def build(self, **kwargs):
        return lex.lex(module=self, **kwargs)

    states = (
        ('sstring', 'exclusive'),
        ('dstring', 'exclusive'),
        ('msstring', 'exclusive'),
        ('mdstring', 'exclusive'),
        
        ('lbrace', 'inclusive'),
        ('lbracket', 'inclusive'),
        ('lparen', 'inclusive'),
        
        ('nlescape', 'exclusive'),
        )

    tokens = ('STRING',)
    keywords = ('and', 'false', 'in', 'not', 'null', 'or', 'true')

    t_INITIAL_nlescape_ignore = ' \t\r'
    t_msstring_mdstring_sstring_dstring_ignore = ''

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

    def begin_string(self, t, state):
        t.lexer.push_state(state)
        self.string_value = ''

    def end_string(self, t):
        t.lexer.pop_state()
        t.type = 'STRING'
        t.value = self.string_value
        t.lexer.lineno += t.value.count('\n')
        return t

    def t_begin_msstring(self, t):
        r"'''"
        self.begin_string(t, 'msstring')

    def t_begin_mdstring(self, t):
        r'"""'
        self.begin_string(t, 'mdstring')

    def t_begin_sstring(self, t):
        r"'"
        self.begin_string(t, 'sstring')

    def t_begin_dstring(self, t):
        r'"'
        self.begin_string(t, 'dstring')

    def t_msstring_mdstring_sstring_dstring_escape_sequence(self, t):
        r'''(\\['"\\/bfnrt])|((\\u[a-fA-F0-9]{4})+)'''
        if t.value[1] == '/':
            value = '/'
        else:
            # Convert escape sequences into the characters they represent
            value = t.value.encode().decode('unicode_escape')
            if t.value.startswith('\\u'):
                # Recombine any surrogate pairs
                value = value.encode('utf-16').decode('utf-16')
        self.string_value += value

    def t_msstring_body(self, t):
        r"([^'\\]|('(?!'')))+"
        self.string_value += t.value

    def t_mdstring_body(self, t):
        r'([^"\\]|("(?!"")))+'
        self.string_value += t.value

    def t_sstring_body(self, t):
        r"[^'\\\n]+"
        self.string_value += t.value

    def t_dstring_body(self, t):
        r'[^"\\\n]+'
        self.string_value += t.value

    def t_sstring_dstring_newline(self, t):
        r'\n'
        self.error_logger('Unterminated string literal',
                          t.value[0], t.lexer.lineno, t.lexer.lexpos)
        self.end_string(t)
        t.lexer.lineno += 1
        return t

    def t_msstring_end(self, t):
        r"'''"
        return self.end_string(t)

    def t_mdstring_end(self, t):
        r'"""'
        return self.end_string(t)

    def t_sstring_end(self, t):
        r"'"
        return self.end_string(t)

    def t_dstring_end(self, t):
        r'"'
        return self.end_string(t)

    @TOKEN(
        r'(?P<t_NUMBER_value>'
        r'(?P<t_NUMBER_int>([1-9][0-9]+)|[0-9])'     # Integer
        r'(\.(?P<t_NUMBER_frac>[0-9]+))?'            # Fraction
        r'([eE](?P<t_NUMBER_exp>[+-]?[0-9]+))?'      # Exponent
        r')(?P<t_NUMBER_tag>[a-zA-Z][a-zA-Z0-9]*)?'  # Tag
        )
    def t_NUMBER(self, t):
        groupdict = dict((k.split('_')[2], v) for (k, v) in
                         t.lexer.lexmatch.groupdict('').items()
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

    def t_begin_nlescape(self, t):
        r'\\'
        t.lexer.push_state('nlescape')

    def t_nlescape_end(self, t):
        r'\n'
        t.lexer.pop_state()
        t.lexer.lineno += 1

    def t_lbrace_lbracket_lparen_newline(self, t):
        r'\n+'
        self.t_NEWLINE(t)  # Update lineno but discard token

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    def t_ANY_error(self, t):
        bad_char = t.value[0]
        self.error_logger('Illegal character: %r' % str(bad_char),
                          bad_char, t.lexer.lineno, t.lexer.lexpos)
        t.lexer.skip(1)
