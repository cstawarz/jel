from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager
import unittest

from ..lexer import JELLexer, MatchString


class TestJELLexer(unittest.TestCase):

    def setUp(self):
        self.errors = collections.deque()
        def error_logger(*info):
            self.errors.append(info)
            
        self.lexer = JELLexer(error_logger).build()

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
                
            if self.errors:
                self.fail('input contained unexpected errors: ' +
                          ', '.join(repr(e) for e in self.errors))

        self.input = input_wrapper

    def advance(self):
        self.next_token = self.lexer.token()

    def assertToken(self, type, value, lineno=None):
        t = self.next_token
        
        self.assertIsNotNone(t)
        self.assertEqual(type, t.type)
        self.assertEqual(value, t.value)
        if lineno:
            self.assertEqual(lineno, t.lineno)

        self.advance()

        return t

    def assertError(self, value, lineno=None):
        self.assertTrue(self.errors, 'expected error was not detected')
        e = self.errors.popleft()
        
        self.assertEqual(value, e[1])
        if lineno:
            self.assertEqual(lineno, e[2])

    def assertNumber(self, value, int='', frac='', exp='', units=''):
        t = self.assertToken('NUMBER', value)
        self.assertIsInstance(t.value, MatchString)
        self.assertEqual(int, t.value.int)
        self.assertEqual(frac, t.value.frac)
        self.assertEqual(exp, t.value.exp)
        self.assertEqual(units, t.value.units)

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
        # Linefeed ('\n') is a token; space, horizontal tab ('\t'),
        # and carriage return ('\r') are ignored; and all others
        # ('\f', '\v') are invalid
        with self.input('  \n\t\t 1 2 \f 3 \r \v\r \n\n\n 4  \t'):
            self.assertToken('NEWLINE', '\n', lineno=1)
            self.assertToken('NUMBER', '1', lineno=2)
            self.assertToken('NUMBER', '2')
            self.assertError('\f')
            self.assertToken('NUMBER', '3')
            self.assertError('\v')
            self.assertToken('NEWLINE', '\n\n\n', lineno=2)
            self.assertToken('NUMBER', '4', lineno=5)

    def test_escaped_newline(self):
        with self.input('\n \n\n \\\n\n \\   \t  \n 3  \\  \f 4  \n5'):
            self.assertToken('NEWLINE', '\n', lineno=1)
            self.assertToken('NEWLINE', '\n\n', lineno=2)
            # Escaped newline, no token
            self.assertToken('NEWLINE', '\n', lineno=5)
            # Escaped newline, no token
            self.assertToken('NUMBER', '3', lineno=7)
            self.assertError('\f')
            self.assertError('4')
            # Escaped newline, no token
            self.assertToken('NUMBER', '5', lineno=8)

    def test_newline_in_grouping(self):
        with self.input(
                '\n ( \n ) \n [ \n\n ] \n { \n \n \n } \n '
                '\n ( \n [ \n { \n } \n ] \n ) \n '
                '\n ( \n ] \n } \n ) \n '
                '\n [ \n ) \n } \n ] \n '
                '\n { \n ) \n ] \n } \n '
            ):
            self.assertToken('NEWLINE', '\n', lineno=1)
            self.assertToken('LPAREN', '(', lineno=2)
            self.assertToken('RPAREN', ')', lineno=3)
            self.assertToken('NEWLINE', '\n', lineno=3)
            self.assertToken('LBRACKET', '[', lineno=4)
            self.assertToken('RBRACKET', ']', lineno=6)
            self.assertToken('NEWLINE', '\n', lineno=6)
            self.assertToken('LBRACE', '{', lineno=7)
            self.assertToken('RBRACE', '}', lineno=10)
            self.assertToken('NEWLINE', '\n', lineno=10)
            
            self.assertToken('NEWLINE', '\n')
            self.assertToken('LPAREN', '(')
            self.assertToken('LBRACKET', '[')
            self.assertToken('LBRACE', '{')
            self.assertToken('RBRACE', '}')
            self.assertToken('RBRACKET', ']')
            self.assertToken('RPAREN', ')')
            self.assertToken('NEWLINE', '\n')
            
            self.assertToken('NEWLINE', '\n')
            self.assertToken('LPAREN', '(')
            self.assertError(']')
            self.assertError('}')
            self.assertToken('RPAREN', ')')
            self.assertToken('NEWLINE', '\n')
            
            self.assertToken('NEWLINE', '\n')
            self.assertToken('LBRACKET', '[')
            self.assertError(')')
            self.assertError('}')
            self.assertToken('RBRACKET', ']')
            self.assertToken('NEWLINE', '\n')
            
            self.assertToken('NEWLINE', '\n')
            self.assertToken('LBRACE', '{')
            self.assertError(')')
            self.assertError(']')
            self.assertToken('RBRACE', '}')
            self.assertToken('NEWLINE', '\n')

    def test_operators(self):
        with self.input(': , / . == > >= { [ < <= ( - % != + ** ) ] } *'):
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
            self.assertToken('RPAREN', ')')
            self.assertToken('RBRACKET', ']')
            self.assertToken('RBRACE', '}')
            self.assertToken('TIMES', '*')

    def test_identifiers(self):
        with self.input('a A z Z foo Bar12 FOO_bar _ _foo _f1 F_0_9 2_ 23foo'):
            self.assertToken('IDENTIFIER', 'a')
            self.assertToken('IDENTIFIER', 'A')
            self.assertToken('IDENTIFIER', 'z')
            self.assertToken('IDENTIFIER', 'Z')
            self.assertToken('IDENTIFIER', 'foo')
            self.assertToken('IDENTIFIER', 'Bar12')
            self.assertToken('IDENTIFIER', 'FOO_bar')
            self.assertToken('IDENTIFIER', '_')
            self.assertToken('IDENTIFIER', '_foo')
            self.assertToken('IDENTIFIER', '_f1')
            self.assertToken('IDENTIFIER', 'F_0_9')
            self.assertToken('NUMBER', '2')
            self.assertToken('IDENTIFIER', '_')
            self.assertToken('NUMBER', '23foo')  # 'foo' is units

    def test_keywords(self):
        with self.input('and false in not null or true And andyet andnot'):
            self.assertToken('AND', 'and')
            self.assertToken('FALSE', 'false')
            self.assertToken('IN', 'in')
            self.assertToken('NOT', 'not')
            self.assertToken('NULL', 'null')
            self.assertToken('OR', 'or')
            self.assertToken('TRUE', 'true')
            self.assertToken('IDENTIFIER', 'And')
            self.assertToken('IDENTIFIER', 'andyet')
            self.assertToken('IDENTIFIER', 'andnot')

    def test_numbers(self):
        with self.input(
                '1 2 0 12 123 012 '
                '0.0 1.23 34.0567 .1 2. '
                '0e0 1E23 1.2e+123 2.3E-00089 1.2e 2.4E 5'
                ):
            self.assertNumber('1', int='1')
            self.assertNumber('2', int='2')
            self.assertNumber('0', int='0')
            self.assertNumber('12', int='12')
            self.assertNumber('123', int='123')

            # Zero is the only number whose integer part can have a
            # leading '0', so '012' is lexed as '0' and '12'
            self.assertNumber('0', int='0')
            self.assertNumber('12', int='12')

            self.assertNumber('0.0', int='0', frac='0')
            self.assertNumber('1.23', int='1', frac='23')
            self.assertNumber('34.0567', int='34', frac='0567')

            # There must be at least one digit on either side of a
            # decimal point, so the '.' in '.1' and '2.' is lexed as
            # DOT
            self.assertToken('DOT', '.')
            self.assertNumber('1', int='1')
            self.assertNumber('2', int='2')
            self.assertToken('DOT', '.')
            
            self.assertNumber('0e0', int='0', exp='0')
            self.assertNumber('1E23', int='1', exp='23')
            self.assertNumber('1.2e+123', int='1', frac='2', exp='+123')
            self.assertNumber('2.3E-00089', int='2', frac='3', exp='-00089')

            # There must be at least one digit after the 'e' or 'E',
            # so the letter is lexed as units in '1.2e' and '-2.4E'
            self.assertNumber('1.2e', int='1', frac='2', units='e')
            self.assertNumber('2.4E', int='2', frac='4', units='E')
            self.assertNumber('5', int='5')

    def test_numbers_with_units(self):
        with self.input(
                '0s 1ms 2.3us 0.1e23MpS2 '
                '12a1B2c345 1.23E123E123'
                ):
            self.assertNumber('0s', int='0', units='s')
            self.assertNumber('1ms', int='1', units='ms')
            self.assertNumber('2.3us', int='2', frac='3', units='us')
            self.assertNumber('0.1e23MpS2', int='0', frac='1', exp='23',
                              units='MpS2')
            
            self.assertNumber('12a1B2c345', int='12', units='a1B2c345')
            self.assertNumber('1.23E123E123', int='1', frac='23', exp='123',
                              units='E123')  # Poor choice of units

    def test_string(self):
        with self.input(
                "'' ' ' 'foo' 'foo bar blah' 'can\\'t' 'foo\nbar' "
                '"" " " "foo" "foo bar blah" "can\\"t" "foo\nbar" '
                ):
            self.assertToken('STRING', "")
            self.assertToken('STRING', " ")
            self.assertToken('STRING', "foo")
            self.assertToken('STRING', "foo bar blah")
            self.assertToken('STRING', "can't")
            
            self.assertError('\n')
            self.assertToken('STRING', 'foobar')
            
            self.assertToken('STRING', '')
            self.assertToken('STRING', ' ')
            self.assertToken('STRING', 'foo')
            self.assertToken('STRING', 'foo bar blah')
            self.assertToken('STRING', 'can"t')
            
            self.assertError('\n')
            self.assertToken('STRING', 'foobar')

    def test_multiline_string(self):
        with self.input(
                "'''''' ''' ''' '''foo''' '''foo\nbar\nblah''' "
                "'''foo\\'''bar''' "
                
                '"""""" """ """ """foo""" """foo\nbar\nblah""" '
                '"""foo\\"""bar""" '
                ):
            self.assertToken('STRING', "")
            self.assertToken('STRING', " ")
            self.assertToken('STRING', "foo")
            self.assertToken('STRING', "foo\nbar\nblah", lineno=1)
            self.assertToken('STRING', "foo'''bar", lineno=3)
            
            self.assertToken('STRING', '')
            self.assertToken('STRING', ' ')
            self.assertToken('STRING', 'foo')
            self.assertToken('STRING', 'foo\nbar\nblah', lineno=3)
            self.assertToken('STRING', 'foo"""bar', lineno=5)

    @unittest.expectedFailure
    def test_string_escape_sequences(self):
        self.fail('escape sequences have not been implemented yet')
