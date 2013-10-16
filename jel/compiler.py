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
    'LOGICAL_AND',
    'LOGICAL_OR',
    'UNARY_OP',
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
        self._ops = []
        for name, code in op_codes.items():
            gen_name = name.lower()
            assert not hasattr(self, gen_name)
            setattr(self, gen_name, self._make_op_gen(code))

    def _make_op_gen(self, code):
        def genop(*args):
            self._ops[-1].append((code, args))
        return genop

    def _genops(self, node):
        getattr(self, self._cc_to_us(type(node).__name__))(node)

    def or_expr(self, node):
        operand_ops = tuple(self.compile(o) for o in node.operands)
        self.logical_or(*operand_ops)

    def and_expr(self, node):
        operand_ops = tuple(self.compile(o) for o in node.operands)
        self.logical_and(*operand_ops)

    def binary_op_expr(self, node):
        self._genops(node.operands[0])
        self._genops(node.operands[1])
        self.binary_op(binary_op_codes[node.op])

    def unary_op_expr(self, node):
        self._genops(node.operand)
        self.unary_op(unary_op_codes[node.op])

    def call_expr(self, node):
        self._genops(node.target)
        arg_ops = tuple(self.compile(arg) for arg in node.args)
        self.call_function(*arg_ops)

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
        self._ops.append([])
        self._genops(root)
        return self._ops.pop()

    @classmethod
    def print_ops(cls, ops, indent=0):
        for index, (op, args) in enumerate(ops):
            op = op_names[op]
            print('{}{:4} {:15}'.format(' ' * indent, index, op), end='')
            if op == 'BINARY_OP':
                print(binary_op_names[args[0]])
            elif op == 'UNARY_OP':
                print(unary_op_names[args[0]])
            elif op in ('CALL_FUNCTION', 'LOGICAL_AND', 'LOGICAL_OR'):
                print()
                for arg_num, arg_ops in enumerate(args):
                    print('{}arg {}:'.format(' ' * (indent+7), arg_num))
                    cls.print_ops(arg_ops, indent+9)
            elif op == 'LOAD_CONST':
                print(repr(args[0]))
            else:
                assert len(args) == 1
                print(args[0])
