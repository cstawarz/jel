from __future__ import division, print_function, unicode_literals
import collections
from contextlib import contextmanager
from itertools import dropwhile

from jel.compiler import Compiler as JELCompiler, gen_codes

from . import ast


class Compiler(JELCompiler):

    op_names, op_codes = gen_codes(
        'CALL_COMPOUND',
        'CALL_SIMPLE',
        'DUP_TOP',
        'DUP_TOP_TWO',
        'INIT_LOCAL',
        'LOAD_ATTR_REF',
        'LOAD_CLOSURE',
        'LOAD_GLOBAL',
        'LOAD_LOCAL',
        'LOAD_NONLOCAL',
        'MAKE_FUNCTION',
        'RETURN_VALUE',
        'ROT_THREE',
        'ROT_TWO',
        'STORE_ATTR',
        'STORE_CLOSURE',
        'STORE_GLOBAL',
        'STORE_LOCAL',
        'STORE_NONLOCAL',
        'STORE_SUBSCR',
        *filter((lambda n: n != 'LOAD_NAME'), JELCompiler.op_names)
        )

    def __init__(self):
        super(Compiler, self).__init__()
        self._scopes = collections.deque()
        self._closures = []

    def _new_scope(self):
        @contextmanager
        def scope():
            self._scopes.appendleft(set())
            yield
            self._scopes.popleft()
        return scope()

    def _new_local(self, lineno, lexpos, name):
        self._scopes[0].add(name)
        self.init_local(lineno, lexpos, name)

    def _new_closure(self):
        @contextmanager
        def closure():
            level = len(self._scopes) - 1
            names = collections.OrderedDict()
            self._closures.append((level, names))
            yield names
            self._closures.pop()
        return closure()

    def _load_name(self, lineno, lexpos, name):
        depth = self._name_depth(name)
        if depth is None:
            self.load_global(lineno, lexpos, name)
        elif depth == 0:
            self.load_local(lineno, lexpos, name)
        elif self._in_closure(name, depth):
            self.load_closure(lineno, lexpos, name)
        else:
            self.load_nonlocal(lineno, lexpos, name, depth)

    def _store_name(self, lineno, lexpos, name):
        depth = self._name_depth(name)
        if depth is None:
            self.store_global(lineno, lexpos, name)
        elif depth == 0:
            self.store_local(lineno, lexpos, name)
        elif self._in_closure(name, depth):
            self.store_closure(lineno, lexpos, name)
        else:
            self.store_nonlocal(lineno, lexpos, name, depth)

    def _in_closure(self, name, depth):
        if not self._closures:
            return False

        if name in self._closures[-1]:
            return True

        name_level = len(self._scopes) - depth - 1
        closures = tuple(dropwhile(lambda c: c[0] < 0,
                                   ((level - name_level - 1, names)
                                    for level, names in self._closures)))
        if not closures:
            return False

        for index, (relative_depth, closure_names) in enumerate(closures):
            closure_names[name] = relative_depth * (-1 if index > 0 else 1)
        return True

    def _name_depth(self, name):
        for depth, local_names in enumerate(self._scopes):
            if name in local_names:
                return depth

    def module(self, node):
        with self._new_scope():
            self.compile_stmt_list(node.statements)

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
                self._store_name(ln, lp, t.value)

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
            self._store_name(node.lineno, node.lexpos, node.target.value)

    def local_stmt(self, node):
        self.genops(node.value)
        self._new_local(node.lineno, node.lexpos, node.name)

    def simple_call_stmt(self, node):
        self.genops(node.target)
        self.call_simple(node.lineno,
                         node.lexpos,
                         self.compile_arg_list(node))

    def compound_call_stmt(self, node):
        clauses = []
        for c in node.clauses:
            arg_list = self.compile_arg_list(c)
            with self._new_op_list() as body:
                with self._new_scope():
                    self.compile_stmt_list(c.body, c.local_names)
            clauses.append((arg_list, len(c.local_names), tuple(body)))

        self.call_compound(node.lineno,
                           node.lexpos,
                           node.function_name,
                           tuple(clauses))

    def compile_arg_list(self, node):
        if isinstance(node.args, collections.OrderedDict):
            return collections.OrderedDict((k, self.compile(v)) for k, v in
                                           node.args.items())
        return super(Compiler, self).compile_arg_list(node)

    def function_stmt(self, node):
        if node.local:
            self.null_literal_expr(node)
            self._new_local(node.lineno, node.lexpos, node.name)

        with self._new_op_list() as body:
            with self._new_scope():
                with self._new_closure() as closure:
                    self.compile_stmt_list(node.body, node.args)

        self.make_function(node.lineno,
                           node.lexpos,
                           len(node.args),
                           tuple(body),
                           tuple(closure.items()))
        self._store_name(node.lineno, node.lexpos, node.name)

    def function_expr(self, node):
        with self._new_op_list() as body:
            with self._new_scope():
                with self._new_closure() as closure:
                    self.compile_stmt_list((node.body,), node.args)
                    self.return_value(node.body.lineno, node.body.lexpos)

        self.make_function(node.lineno,
                           node.lexpos,
                           len(node.args),
                           tuple(body),
                           tuple(closure.items()))

    def compile_stmt_list(self, stmts, local_names=()):
        for n in reversed(local_names):
            self._new_local(n.lineno, n.lexpos, n.value)
        for s in stmts:
            self.genops(s)

    def return_stmt(self, node):
        if node.value is not None:
            self.genops(node.value)
        else:
            self.null_literal_expr(node)
        self.return_value(node.lineno, node.lexpos)

    def attribute_reference_expr(self, node):
        self.genops(node.target)
        self.load_attr_ref(node.lineno, node.lexpos, node.name)

    def identifier_expr(self, node):
        self._load_name(node.lineno, node.lexpos, node.value)
