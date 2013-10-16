from __future__ import division, print_function, unicode_literals
import re


def _gen_codes(*ops):
    return ops, dict((op, code) for code, op in enumerate(ops))


op_names, op_codes = _gen_codes(
    'BINARY_OP',
    'BINARY_SUBSCR',
    'BUILD_ARRAY',
    'BUILD_OBJECT',
    'CALL_FUNCTION',
    'LOAD_ATTR',
    'LOAD_CONST',
    'LOAD_NAME',
    'UNARY_OP',
    'UNARY_TRUTH',
    )

binary_op_names, binary_op_codes = _gen_codes(
    '+', '-', '*', '/', '%', '**',
    )

unary_op_names, unary_op_codes = _gen_codes(
    'not', '+', '-',
    )

comparison_op_names, comparison_op_codes = _gen_codes(
    '<', '<=', '>', '>=', '!=', '==', 'in', 'not in',
    )


class Compiler(object):

    _cc_to_us_re = re.compile(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))'
        )

    @classmethod
    def _cc_to_us(cls, s):
        return cls._cc_to_us_re.sub('_\\1', s).lower().strip('_')

    def __init__(self):
        for name, code in op_codes.items():
            gen_name = name.lower()
            assert not hasattr(self, gen_name)
            setattr(self, gen_name, self._make_op_gen(code))

    def _make_op_gen(self, code):
        def genop(*args):
            self._ops.append((code, args))
        return genop

    def _genops(self, node):
        getattr(self, self._cc_to_us(type(node).__name__))(node)

    def binary_op_expr(self, node):
        self._genops(node.operands[0])
        self._genops(node.operands[1])
        self.binary_op(binary_op_codes[node.op])

    def unary_op_expr(self, node):
        self._genops(node.operand)
        self.unary_op(unary_op_codes[node.op])

    def call_expr(self, node):
        self._genops(node.target)
        for arg in node.args:
            self._genops(arg)
        self.call_function(len(node.args))

    def subscript_expr(self, node):
        self._genops(node.target)
        self._genops(node.value)
        self.binary_subscr()

    def attribute_expr(self, node):
        self._genops(node.target)
        self.load_attr(node.name)

    def object_literal_expr(self, node):
        for key, value in node.items.items():
            self.load_const(key)
            self._genops(value)
        self.build_object(len(node.items))

    def array_literal_expr(self, node):
        for item in node.items:
            self._genops(item)
        self.build_array(len(node.items))

    def string_literal_expr(self, node):
        self.load_const(node.value)

    def number_literal_expr(self, node):
        assert node.tag is None
        self.load_const(float(node.value))

    def boolean_literal_expr(self, node):
        self.load_const(node.value)

    def null_literal_expr(self, node):
        self.load_const(None)

    def identifier_expr(self, node):
        self.load_name(node.value)

    def compile(self, root):
        self._ops = []
        self._genops(root)
        return self._ops

    @staticmethod
    def print_ops(ops):
        for index, (op, args) in enumerate(ops):
            if op == op_codes['BINARY_OP']:
                args = (binary_op_names[a] for a in args)
            elif op == op_codes['UNARY_OP']:
                args = (unary_op_names[a] for a in args)
            elif op == op_codes['LOAD_CONST']:
                args = (repr(a) for a in args)
            else:
                args = (str(a) for a in args)
            print('{:4} {:25}{}'.format(index, op_names[op], ','.join(args)))
