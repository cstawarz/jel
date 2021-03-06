from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager
import unittest

from ..lexer import Lexer, MatchString


class LexerTestMixin(object):

    def setUp(self):
        self.errors = collections.deque()
        def error_logger(*info):
            self.errors.append(info)
            
        self.lexer = self.lexer_class(error_logger).build()

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

    def assertNumber(self, value, int='', frac='', exp='', tag=''):
        t = self.assertToken('NUMBER', value)
        self.assertIsInstance(t.value, MatchString)
        self.assertEqual(int, t.value.int)
        self.assertEqual(frac, t.value.frac)
        self.assertEqual(exp, t.value.exp)
        self.assertEqual(tag, t.value.tag)


class TestLexer(LexerTestMixin, unittest.TestCase):

    lexer_class = Lexer

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

    def test_groupings(self):
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
        with self.input('+ - : , <= < >= > == != . * / % **'):
            self.assertToken('ADDITIVEOP', '+')
            self.assertToken('ADDITIVEOP', '-')
            self.assertToken('COLON', ':')
            self.assertToken('COMMA', ',')
            self.assertToken('COMPARISONOP', '<=')
            self.assertToken('COMPARISONOP', '<')
            self.assertToken('COMPARISONOP', '>=')
            self.assertToken('COMPARISONOP', '>')
            self.assertToken('COMPARISONOP', '==')
            self.assertToken('COMPARISONOP', '!=')
            self.assertToken('DOT', '.')
            self.assertToken('MULTIPLICATIVEOP', '*')
            self.assertToken('MULTIPLICATIVEOP', '/')
            self.assertToken('MULTIPLICATIVEOP', '%')
            self.assertToken('POWER', '**')

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
            self.assertToken('NUMBER', '23foo')  # 'foo' is tag

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
            # so the letter is lexed as tag in '1.2e' and '-2.4E'
            self.assertNumber('1.2e', int='1', frac='2', tag='e')
            self.assertNumber('2.4E', int='2', frac='4', tag='E')
            self.assertNumber('5', int='5')

    def test_numbers_with_tags(self):
        with self.input(
                '0s 1ms 2.3us 0.1e23MpS2 '
                '12a1B2c345 1.23E123E123'
                ):
            self.assertNumber('0s', int='0', tag='s')
            self.assertNumber('1ms', int='1', tag='ms')
            self.assertNumber('2.3us', int='2', frac='3', tag='us')
            self.assertNumber('0.1e23MpS2', int='0', frac='1', exp='23',
                              tag='MpS2')
            
            self.assertNumber('12a1B2c345', int='12', tag='a1B2c345')
            self.assertNumber('1.23E123E123', int='1', frac='23', exp='123',
                              tag='E123')  # Poor choice of tag

    def test_string(self):
        with self.input(
                "'' ' ' 'foo' 'foo bar blah' 'can\\'t' '\"baz\"' 'foo\nbar'' "
                '"" " " "foo" "foo bar blah" "can\\"t" "\'baz\'" "foo\nbar""'
                ):
            self.assertToken('STRING', "")
            self.assertToken('STRING', " ")
            self.assertToken('STRING', "foo")
            self.assertToken('STRING', "foo bar blah")
            self.assertToken('STRING', "can't")
            self.assertToken('STRING', '"baz"')
            
            self.assertToken('STRING', 'foo', lineno=1)
            self.assertError('\n')
            self.assertToken('IDENTIFIER', 'bar', lineno=2)
            self.assertToken('STRING', "")
            
            self.assertToken('STRING', '')
            self.assertToken('STRING', ' ')
            self.assertToken('STRING', 'foo')
            self.assertToken('STRING', 'foo bar blah')
            self.assertToken('STRING', 'can"t')
            self.assertToken('STRING', "'baz'")
            
            self.assertToken('STRING', 'foo', lineno=2)
            self.assertError('\n')
            self.assertToken('IDENTIFIER', 'bar', lineno=3)
            self.assertToken('STRING', '')

    def test_multiline_string(self):
        with self.input(
                "'''''' ''' ''' '''foo''' '''foo\n'bar'\nblah''' "
                "'''foo\\'''bar''' '''\"baz\"''' "
                
                '"""""" """ """ """foo""" """foo\n"bar"\nblah""" '
                '"""foo\\"""bar"""  """\'baz\'"""'
                ):
            self.assertToken('STRING', "")
            self.assertToken('STRING', " ")
            self.assertToken('STRING', "foo")
            self.assertToken('STRING', "foo\n'bar'\nblah", lineno=1)
            self.assertToken('STRING', "foo'''bar", lineno=3)
            self.assertToken('STRING', '"baz"')
           
            self.assertToken('STRING', '')
            self.assertToken('STRING', ' ')
            self.assertToken('STRING', 'foo')
            self.assertToken('STRING', 'foo\n"bar"\nblah', lineno=3)
            self.assertToken('STRING', 'foo"""bar', lineno=5)
            self.assertToken('STRING', "'baz'")

    def for_all_string_types(self, func):
        func("'''")
        func('"""')
        func("'")
        func('"')

    def test_string_whitespace(self):
        @self.for_all_string_types
        def test_whitespace(delim):
            with self.input(delim + ' \t\r' + delim):
                self.assertToken('STRING', ' \t\r')

    def test_string_escape_sequences(self):
        @self.for_all_string_types
        def test_escapes(d):
            with self.input(d +
                            r''' \z \' \" \\ \/ \b \f \n \r \t ''' +
                            '\\u0061\\uD834\\udD1e\\u0062' +
                            d):
                self.assertError('\\')
                self.assertToken('STRING',
                                 (''' z \' \" \\ / \b \f \n \r \t ''' +
                                  'a\U0001d11eb'))
