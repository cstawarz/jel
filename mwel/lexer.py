from __future__ import division, print_function, unicode_literals

from jel.lexer import Lexer as JELLexer


class Lexer(JELLexer):

    keywords = JELLexer.keywords + ('else', 'end', 'local', 'var')

    t_ASSIGN = r'='
    t_PLUSASSIGN = r'\+='

    t_ignore_comment = r'\#[^\n]*'
