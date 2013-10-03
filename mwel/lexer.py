from __future__ import division, print_function, unicode_literals

from jel.lexer import Lexer as JELLexer


class Lexer(JELLexer):

    keywords = JELLexer.keywords + ('def', 'else', 'end', 'local')

    t_ASSIGN = r'='

    t_ignore_comment = r'\#[^\n]*'
