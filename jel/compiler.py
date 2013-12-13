from __future__ import division, print_function, unicode_literals
import re


def gen_codes(*ops):
    return ops, dict((op, code) for code, op in enumerate(ops))


class Compiler(object):

    op_names, op_codes = gen_codes(
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

    _cc_to_us_re = re.compile(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))'
        )

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
        arg_ops = tuple(self.compile(arg) for arg in node.args)
        self.call_function(node.lineno, node.lexpos, arg_ops)

    def subscript_expr(self, node):
        self.genops(node.target)
        self.genops(node.value)
        self.load_subscr(node.lineno, node.lexpos)

    def attribute_expr(self, node):
        self.genops(node.target)
        self.load_attr(node.lineno, node.lexpos, node.name)

    def object_literal_expr(self, node):
        for key, value in node.items.items():
            self.load_const(node.lineno, node.lexpos, key)
            self.genops(value)
        self.build_object(node.lineno, node.lexpos, len(node.items))

    def array_literal_expr(self, node):
        for item in node.items:
            self.genops(item)
        self.build_array(node.lineno, node.lexpos, len(node.items))

    def string_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, node.value)

    def number_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, float(node.value), node.tag)

    def boolean_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, node.value)

    def null_literal_expr(self, node):
        self.load_const(node.lineno, node.lexpos, None)

    def identifier_expr(self, node):
        self.load_name(node.lineno, node.lexpos, node.value)

    def compile(self, root):
        self._ops.append([])
        self.genops(root)
        return self._ops.pop()

    @classmethod
    def print_ops(cls, ops, indent=0):
        for index, (op, lineno, lexpos, args) in enumerate(ops):
            op = cls.op_names[op]
            if isinstance(lineno, tuple):
                loc = ','.join('{}:{}'.format(ln, lp)
                               for ln, lp in zip(lineno, lexpos))
            else:
                loc = '{}:{}'.format(lineno, lexpos)
            print('{}{:4} {:14} {}  '.format(' ' * indent, index, op, loc),
                  end = '')
            if op == 'BINARY_OP':
                print(cls.binary_op_names[args[0]])
            elif op == 'UNARY_OP':
                print(cls.unary_op_names[args[0]])
            elif op == 'COMPARE_OP':
                print(','.join(cls.comparison_op_names[code]
                                for code in args[0]))
                cls._print_arg_ops(args[1], indent)
            elif op in ('CALL_FUNCTION', 'LOGICAL_AND', 'LOGICAL_OR'):
                print()
                cls._print_arg_ops(args[0], indent)
            elif op == 'LOAD_CONST':
                print(repr(args[0]) if len(args) == 1 else args)
            else:
                assert len(args) <= 1
                print(args[0] if args else '')

    @classmethod
    def _print_arg_ops(cls, args, indent):
        for arg_num, arg_ops in enumerate(args):
            print('{}arg {}:'.format(' ' * (indent+7), arg_num))
            cls.print_ops(arg_ops, indent+9)
