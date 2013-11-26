from __future__ import division, print_function, unicode_literals

from jel.lexer import Lexer as JELLexer


class Lexer(JELLexer):

    keywords = JELLexer.keywords + (
        'else', 'end', 'function', 'local', 'return',
        )

    t_ASSIGN = r'='
    t_AUGASSIGN = r'(%s)=' % r'|'.join((
        JELLexer.t_ADDITIVEOP,
        JELLexer.t_MULTIPLICATIVEOP,
        JELLexer.t_POWER,
        ))

    t_ignore_comment = r'\#[^\n]*'

    def t_BIND(self, t):
        r'<-'
        return t
