# All aspects of string and number REs
# Correct line numbers with multiline strings
# Identifiers vs keywords

from contextlib import contextmanager
import unittest
from jel_parser import JELLexer


class TestJELLexer(unittest.TestCase):

    def setUp(self):
        self.jl = JELLexer()
        self.lexer = self.jl.build()

        @contextmanager
        def input_wrapper(s):
            self.lexer.input(s)
            self.advance()
            
            yield

            extra_tokens = []
            while self.next_token is not None:
                extra_tokens.append(self.next_token)
                self.advance()
            
            if extra_tokens:
                self.fail('input contained unexpected tokens: ' +
                          ', '.join(repr(t) for t in extra_tokens))
                
            if self.jl.errors:
                self.fail('input contained unexpected errors: ' +
                          ', '.join(repr(e) for e in self.jl.errors))

        self.input = input_wrapper

    def advance(self):
        self.next_token = self.lexer.token()

    def assertToken(self, type, value, lineno=None, lexpos=None):
        t = self.next_token
        
        self.assertIsNotNone(t)
        self.assertEqual(type, t.type)
        self.assertEqual(value, t.value)
        if lineno:
            self.assertEqual(lineno, t.lineno)
        if lexpos:
            self.assertEqual(lexpos, t.lexpos)

        self.advance()

    def assertError(self, value, lineno=None, lexpos=None):
        self.assertTrue(self.jl.errors, 'expected error was not detected')
        e = self.jl.errors.popleft()
        
        self.assertEqual(value, e[0])
        if lineno:
            self.assertEqual(lineno, e[1])
        if lexpos:
            self.assertEqual(lexpos, e[2])

    def test_errors(self):
        with self.input('1 2 $@ & 3 4 #'):
            self.assertToken('NUMBER', '1')
            self.assertToken('NUMBER', '2')
            self.assertError('$')
            self.assertError('@')
            self.assertError('&')
            self.assertToken('NUMBER', '3')
            self.assertToken('NUMBER', '4')
            self.assertError('#')

    def test_whitespace(self):
        # Linefeed ('\n') is a token, space and horizontal tab ('\t')
        # are ignored, and all others ('\f', '\r', '\v') are invalid
        with self.input('  \n\t\t 1 2 \f 3 \r \v\r \n\n\n 4  \t'):
            self.assertToken('NEWLINE', '\n', lineno=1)
            self.assertToken('NUMBER', '1', lineno=2)
            self.assertToken('NUMBER', '2')
            self.assertError('\f')
            self.assertToken('NUMBER', '3')
            self.assertError('\r')
            self.assertError('\v')
            self.assertError('\r')
            self.assertToken('NEWLINE', '\n\n\n', lineno=2)
            self.assertToken('NUMBER', '4', lineno=5)

    def test_escaped_newline(self):
        with self.input('\n \n\n \\\n\n \\   \t  \n 3  \\  \r  \n'):
            self.assertToken('NEWLINE', '\n', lineno=1)
            self.assertToken('NEWLINE', '\n\n', lineno=2)
            # Escaped newline, no token
            self.assertToken('NEWLINE', '\n', lineno=5)
            # Escaped newline, no token
            self.assertToken('NUMBER', '3', lineno=7)
            self.assertError('\\')
            self.assertError('\r')
            self.assertToken('NEWLINE', '\n', lineno=7)

    def test_operators(self):
        with self.input(': , / . == > >= { [ < <= ( - % != + ** } ] ) *'):
            self.assertToken('COLON', ':')
            self.assertToken('COMMA', ',')
            self.assertToken('DIVIDE', '/')
            self.assertToken('DOT', '.')
            self.assertToken('EQUAL', '==')
            self.assertToken('GREATERTHAN', '>')
            self.assertToken('GREATERTHANOREQUAL', '>=')
            self.assertToken('LBRACE', '{')
            self.assertToken('LBRACKET', '[')
            self.assertToken('LESSTHAN', '<')
            self.assertToken('LESSTHANOREQUAL', '<=')
            self.assertToken('LPAREN', '(')
            self.assertToken('MINUS', '-')
            self.assertToken('MODULO', '%')
            self.assertToken('NOTEQUAL', '!=')
            self.assertToken('PLUS', '+')
            self.assertToken('POWER', '**')
            self.assertToken('RBRACE', '}')
            self.assertToken('RBRACKET', ']')
            self.assertToken('RPAREN', ')')
            self.assertToken('TIMES', '*')


if __name__ == '__main__':
    unittest.main()
