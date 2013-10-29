from __future__ import division, print_function, unicode_literals

from jel.compiler import Compiler as JELCompiler, gen_codes

from . import ast


class Compiler(JELCompiler):

    op_names, op_codes = gen_codes(
        'DUP_TOP',
        'DUP_TOP_TWO',
        'ROT_THREE',
        'ROT_TWO',
        'STORE_ATTR',
        'STORE_NAME',
        'STORE_SUBSCR',
        *JELCompiler.op_names
        )

    def module(self, node):
        for stmt in node.statements:
            self.genops(stmt)

    def chained_assignment_stmt(self, node):
        self.genops(node.value)
        targets, lineno, lexpos = node.targets, node.lineno, node.lexpos
        while targets:
            t, targets = targets[0], targets[1:]
            ln, lineno = lineno[0], lineno[1:]
            lp, lexpos = lexpos[0], lexpos[1:]
            if targets:
                self.dup_top(ln, lp)
            if isinstance(t, ast.SubscriptExpr):
                self.genops(t.target)
                self.genops(t.value)
                self.store_subscr(ln, lp)
            elif isinstance(t, ast.AttributeExpr):
                self.genops(t.target)
                self.store_attr(ln, lp, t.name)
            else:
                assert isinstance(t, ast.IdentifierExpr)
                self.store_name(ln, lp, t.value)

    def augmented_assignment_stmt(self, node):
        if isinstance(node.target, ast.SubscriptExpr):
            self.genops(node.target.target)
            self.genops(node.target.value)
            self.dup_top_two(node.lineno, node.lexpos)
            self.load_subscr(node.target.lineno, node.target.lexpos)
        elif isinstance(node.target, ast.AttributeExpr):
            self.genops(node.target.target)
            self.dup_top(node.lineno, node.lexpos)
            self.load_attr(
                node.target.lineno,
                node.target.lexpos,
                node.target.name,
                )
        else:
            assert isinstance(node.target, ast.IdentifierExpr)
            self.genops(node.target)

        self.genops(node.value)
        self.binary_op(
            node.lineno,
            node.lexpos,
            self.binary_op_codes[node.op[:-1]],
            )

        if isinstance(node.target, ast.SubscriptExpr):
            self.rot_three(node.lineno, node.lexpos)
            self.store_subscr(node.lineno, node.lexpos)
        elif isinstance(node.target, ast.AttributeExpr):
            self.rot_two(node.lineno, node.lexpos)
            self.store_attr(node.lineno, node.lexpos, node.target.name)
        else:
            self.store_name(node.lineno, node.lexpos, node.target.value)
