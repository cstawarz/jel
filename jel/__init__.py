from __future__ import division, print_function, unicode_literals

from .lexer import JELLexer
from .parser import JELParser


def parse(text):
    jl = JELLexer()
    jp = JELParser(jl.tokens)

    lexer = jl.build()
    parser = jp.build()

    return parser.parse(text, lexer=lexer)
