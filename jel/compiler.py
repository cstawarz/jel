from __future__ import division, print_function, unicode_literals
from contextlib import contextmanager
import re


def gen_codes(*ops):
    sorted_ops = tuple(sorted(ops))
    return sorted_ops, dict((op, code) for code, op in enumerate(sorted_ops))


class Compiler(object):

    op_names, op_codes = gen_codes(
        'APPLY_TAG',
        'BINARY_OP',
        'BUILD_ARRAY',
        'BUILD_OBJECT',
        'CALL_FUNCTION',
        'COMPARE_OP',
        'LOAD_ATTR',
        'LOAD_CONST',
        'LOAD_NAME',
        'LOAD_SUBSCR',
        'LOGICAL_AND',
        'LOGICAL_OR',
        'UNARY_OP',
        )

    binary_op_names, binary_op_codes = gen_codes(
        '+', '-', '*', '/', '%', '**',
        )

    unary_op_names, unary_op_codes = gen_codes(
        'not', '+', '-',
        )

    comparison_op_names, comparison_op_codes = gen_codes(
        '<', '<=', '>', '>=', '!=', '==', 'in', 'not in',
        )

    _cc_to_us_re = re.compile(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))')

    @classmethod
    def _cc_to_us(cls, s):
        return cls._cc_to_us_re.sub('_\\1', s).lower().strip('_')

    def __init__(self):
        self._ops = []
        for name, code in self.op_codes.items():
            gen_name = name.lower()
            assert not hasattr(self, gen_name)
            setattr(self, gen_name, self._make_op_gen(code))

    def _make_op_gen(self, code):
        def genop(lineno, lexpos, *args):
            self._ops[-1].append((code, lineno, lexpos, args))
        return genop

    def genops(self, node):
        getattr(self, self._cc_to_us(type(node).__name__))(node)

    def _new_op_list(self):
        @contextmanager
        def op_list():
            self._ops.append([])
            yield self._ops[-1]
            self._ops.pop()
        return op_list()

    def compile(self, root):
        with self._new_op_list() as ops:
            self.genops(root)
        return tuple(ops)

    def or_expr(self, node):
        operand_ops = tuple(self.compile(o) for o in node.operands)
        self.logical_or(node.lineno, node.lexpos, operand_ops)

    def and_expr(self, node):
        operand_ops = tuple(self.compile(o) for o in node.operands)
        self.logical_and(node.lineno, node.lexpos, operand_ops)

    def binary_op_expr(self, node):
        self.genops(node.operands[0])
        self.genops(node.operands[1])
        self.binary_op(node.lineno, node.lexpos, self.binary_op_codes[node.op])

    def unary_op_expr(self, node):
        self.genops(node.operand)
        self.unary_op(node.lineno, node.lexpos, self.unary_op_codes[node.op])

    def comparison_expr(self, node):
        ops = tuple(self.comparison_op_codes[o] for o in node.ops)
        operand_ops = tuple(self.compile(o) for o in node.operands)
        self.compare_op(node.lineno, node.lexpos, ops, operand_ops)

    def call_expr(self, node):
        self.genops(node.target)
        self.call_function(node.lineno,
                           node.lexpos,
                           self.compile_arg_list(node))

    def compile_arg_list(self, node):
        return tuple(self.compile(arg) for arg in node.args)

    def subscript_expr(self, node):
        self.genops(node.target)
        self.genops(node.value)
        self.load_subscr(node.lineno, node.lexpos)

    def attribute_expr(self, node):
        self.genops(node.target)
        self.load_attr(node.lineno, node.lexpos, node.name)

    def object_literal_expr(self, node):
        for value in node.items.values():
            self.genops(value)
        self.build_object(node.lineno, node.lexpos, tuple(node.items.keys()))

    def array_literal_expr(self, node):
        for item in node.items:
            self.genops(item)
        self.build_array(node.lineno, node.lexpos, len(node.items))

    def string_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, node.value)

    def number_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, float(node.value))
        if node.tag is not None:
            self.apply_tag(node.lineno, node.lexpos, node.tag)

    def boolean_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, node.value)

    def null_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, None)

    def identifier_expr(self, node):
        self.load_name(node.lineno, node.lexpos, node.value)
