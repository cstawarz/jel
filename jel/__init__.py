from __future__ import division, print_function, unicode_literals

from .lexer import JELLexer
from .parser import JELParser


def parse(text):
    def error_logger(token, lineno, lexpos, msg):
        print('%s (line %d, position %d)' % (msg, lineno, lexpos))
        
    jl = JELLexer(error_logger)
    jp = JELParser(jl.tokens, error_logger)

    lexer = jl.build()
    parser = jp.build()

    return parser.parse(text, lexer=lexer)
