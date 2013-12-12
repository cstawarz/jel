from __future__ import division, print_function, unicode_literals

from .lexer import Lexer
from .parser import Parser


def parse(text):
    def print_error(msg, token=None, lineno=None, lexpos=None):
        print(msg, end='')
        if (lineno is not None) and (lexpos is not None):
            colno = lexpos - text.rfind('\n', 0, lexpos)
            print(' (line %d, column %d)' % (lineno, colno), end='')
        print()

    l = Lexer(print_error)
    p = Parser(l.tokens, print_error)

    lexer = l.build()
    parser = p.build(debug=True)

    return parser.parse(text, lexer=lexer)
