from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager

from jel.compiler import Compiler as JELCompiler, gen_codes

from . import ast


class Compiler(JELCompiler):

    op_names, op_codes = gen_codes(
        'CALL_COMPOUND',
        'CALL_SIMPLE',
        'DUP_TOP',
        'DUP_TOP_TWO',
        'INIT_LOCAL',
        'LOAD_GLOBAL',
        'LOAD_LOCAL',
        'POP_SCOPE',
        'PUSH_SCOPE',
        'ROT_THREE',
        'ROT_TWO',
        'STORE_ATTR',
        'STORE_GLOBAL',
        'STORE_LOCAL',
        'STORE_NAME',
        'STORE_SUBSCR',
        *JELCompiler.op_names
        )

    def __init__(self):
        super(Compiler, self).__init__()
        self._local_names = collections.deque()

    def _new_scope(self, lineno, lexpos, toplevel=False):
        @contextmanager
        def scope():
            self._local_names.appendleft(set())
            if not toplevel:
                self.push_scope(lineno, lexpos)
            yield
            if not toplevel:
                self.pop_scope(lineno, lexpos)
            self._local_names.popleft()
        return scope()

    def _name_depth(self, name):
        for depth, local_names in enumerate(self._local_names):
            if name in local_names:
                return depth
        return -1

    def module(self, node):
        with self._new_scope(node.lineno, node.lexpos, toplevel=True):
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
                name_depth = self._name_depth(t.value)
                if name_depth < 0:
                    self.store_global(ln, lp, t.value)
                elif name_depth == 0:
                    self.store_local(ln, lp, t.value)
                else:
                    assert False

    def augmented_assignment_stmt(self, node):
        if isinstance(node.target, ast.SubscriptExpr):
            self.genops(node.target.target)
            self.genops(node.target.value)
            self.dup_top_two(node.lineno, node.lexpos)
            self.load_subscr(node.target.lineno, node.target.lexpos)
        elif isinstance(node.target, ast.AttributeExpr):
            self.genops(node.target.target)
            self.dup_top(node.lineno, node.lexpos)
            self.load_attr(node.target.lineno,
                           node.target.lexpos,
                           node.target.name)
        else:
            assert isinstance(node.target, ast.IdentifierExpr)
            self.genops(node.target)

        self.genops(node.value)
        self.binary_op(node.lineno,
                       node.lexpos,
                       self.binary_op_codes[node.op[:-1]])

        if isinstance(node.target, ast.SubscriptExpr):
            self.rot_three(node.lineno, node.lexpos)
            self.store_subscr(node.lineno, node.lexpos)
        elif isinstance(node.target, ast.AttributeExpr):
            self.rot_two(node.lineno, node.lexpos)
            self.store_attr(node.lineno, node.lexpos, node.target.name)
        else:
            name_depth = self._name_depth(node.target.value)
            if name_depth < 0:
                self.store_global(node.lineno, node.lexpos, node.target.value)
            elif name_depth == 0:
                self.store_local(node.lineno, node.lexpos, node.target.value)
            else:
                assert False

    def local_stmt(self, node):
        self.genops(node.value)
        self.init_local(node.lineno, node.lexpos, node.name)
        self._local_names[0].add(node.name)

    def simple_call_stmt(self, node):
        self.genops(node.target)
        if isinstance(node.args, tuple):
            args = (tuple(self.compile(a) for a in node.args),)
        else:
            assert isinstance(node.args, collections.OrderedDict)
            args = (tuple(node.args.keys()),
                    tuple(self.compile(a) for a in node.args.values()))
        self.call_simple(node.lineno, node.lexpos, *args)

    def compound_call_stmt(self, node):
        clauses = []
        for c in node.clauses:
            body_ops = self.compile_stmt_list(c, c.body)
            clauses.append(((), 0, body_ops))
        
        self.call_compound(node.lineno,
                           node.lexpos,
                           node.function_name,
                           tuple(clauses))

    def identifier_expr(self, node):
        name_depth = self._name_depth(node.value)
        if name_depth < 0:
            self.load_global(node.lineno, node.lexpos, node.value)
        elif name_depth == 0:
            self.load_local(node.lineno, node.lexpos, node.value)
        else:
            assert False

    def compile_stmt_list(self, node, stmts):
        self._ops.append([])
        with self._new_scope(node.lineno, node.lexpos):
            for s in stmts:
                self.genops(s)
        return tuple(self._ops.pop())
