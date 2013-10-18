from __future__ import division, print_function, unicode_literals

from jel.lexer import Lexer as JELLexer


class Lexer(JELLexer):

    keywords = JELLexer.keywords + (
        'else', 'end', 'function', 'local', 'return',
        )

    t_ASSIGN = r'='
    t_AUGASSIGN = r'(\+|-)='

    t_ignore_comment = r'\#[^\n]*'
