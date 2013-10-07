from __future__ import division, print_function, unicode_literals
import unittest

from jel.test.test_lexer import LexerTestMixin

from ..lexer import Lexer


class TestLexer(LexerTestMixin, unittest.TestCase):

    lexer_class = Lexer

    def test_keywords(self):
        with self.input('else end function local return'):
            self.assertToken('ELSE', 'else')
            self.assertToken('END', 'end')
            self.assertToken('FUNCTION', 'function')
            self.assertToken('LOCAL', 'local')
            self.assertToken('RETURN', 'return')

    def test_operators(self):
        with self.input('= -= +='):
            self.assertToken('ASSIGN', '=')
            self.assertToken('MINUSASSIGN', '-=')
            self.assertToken('PLUSASSIGN', '+=')

    def test_comments(self):
        with self.input('   # foo # 123 abc'):
            self.assertIsNone(self.next_token)

        with self.input('1 # foo 123 abc\n# blah blah\n2'):
            self.assertToken('NUMBER', '1')
            self.assertToken('NEWLINE', '\n')
            self.assertToken('NEWLINE', '\n')
            self.assertToken('NUMBER', '2')
