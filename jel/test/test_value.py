from __future__ import division, print_function, unicode_literals
import unittest

from ..evaluator.value import Value


class TestValue(unittest.TestCase):

    def test_cannot_create_base_instance(self):
        self.assertRaises(TypeError, Value)
