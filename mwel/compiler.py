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
        'LOAD_NONLOCAL',
        'POP_SCOPE',
        'PUSH_SCOPE',
        'ROT_THREE',
        'ROT_TWO',
        'STORE_ATTR',
        'STORE_GLOBAL',
        'STORE_LOCAL',
        'STORE_NONLOCAL',
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
                    self.store_nonlocal(ln, lp, t.value, name_depth)

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
                self.store_nonlocal(node.lineno,
                                    node.lexpos,
                                    node.target.value,
                                    name_depth)

    def local_stmt(self, node):
        self.genops(node.value)
        self._new_local(node.lineno, node.lexpos, node.name)

    def _new_local(self, lineno, lexpos, name):
        self.init_local(lineno, lexpos, name)
        self._local_names[0].add(name)

    def simple_call_stmt(self, node):
        self.genops(node.target)
        self.call_simple(node.lineno,
                         node.lexpos,
                         self.compile_arg_list(node))

    def compound_call_stmt(self, node):
        clauses = tuple((self.compile_arg_list(c),
                         len(c.local_names),
                         self.compile_stmt_list(c, c.body, c.local_names))
                        for c in node.clauses)
        self.call_compound(node.lineno,
                           node.lexpos,
                           node.function_name,
                           tuple(clauses))

    def compile_arg_list(self, node):
        if isinstance(node.args, collections.OrderedDict):
            return collections.OrderedDict((k, self.compile(v)) for k, v in
                                           node.args.items())
        return super(Compiler, self).compile_arg_list(node)

    def identifier_expr(self, node):
        name_depth = self._name_depth(node.value)
        if name_depth < 0:
            self.load_global(node.lineno, node.lexpos, node.value)
        elif name_depth == 0:
            self.load_local(node.lineno, node.lexpos, node.value)
        else:
            self.load_nonlocal(node.lineno, node.lexpos, node.value, name_depth)

    def compile_stmt_list(self, node, stmts, local_names=()):
        self._ops.append([])
        with self._new_scope(node.lineno, node.lexpos):
            for n in reversed(local_names):
                self._new_local(n.lineno, n.lexpos, n.value)
            for s in stmts:
                self.genops(s)
        return tuple(self._ops.pop())
