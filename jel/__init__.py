from __future__ import division, print_function, unicode_literals

from .lexer import JELLexer
from .parser import JELParser


def print_error(msg, token=None, lineno=None, lexpos=None):
    print(msg, end='')
    if token:
        print(' (line %d, position %d)' % (lineno, lexpos), end='')
    print()


def parse(text):
    jl = JELLexer(print_error)
    jp = JELParser(jl.tokens, print_error)

    lexer = jl.build()
    parser = jp.build()

    return parser.parse(text, lexer=lexer)
