from __future__ import division, print_function, unicode_literals

from jel.compiler import Compiler as JELCompiler, gen_codes

from . import ast


class Compiler(JELCompiler):

    op_names, op_codes = gen_codes(
        'DUP_TOP',
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
