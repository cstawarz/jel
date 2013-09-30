from __future__ import division, print_function, unicode_literals

from .lexer import Lexer
from .parser import Parser


def print_error(msg, token=None, lineno=None, lexpos=None):
    print(msg, end='')
    if token:
        print(' (line %d, position %d)' % (lineno, lexpos), end='')
    print()


def parse(text):
    l = Lexer(print_error)
    p = Parser(l.tokens, print_error)

    lexer = l.build()
    parser = p.build(debug=True)

    return parser.parse(text, lexer=lexer)
