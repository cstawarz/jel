from __future__ import division, print_function, unicode_literals
import collections

from jel.parser import Parser as JELParser

from . import ast


class Parser(JELParser):

    # In Python 2.7, PLY insists that 'start' be str, not unicode
    start = str('module')

    def p_module(self, p):
        '''
        module : newline stmt_list
               | stmt_list
        '''
        p[0] = ast.Module(1, 0, statements=(p[2] if len(p) == 3 else p[1]))

    def p_stmt_list(self, p):
        '''
        stmt_list : stmt newline stmt_list
                  | stmt
                  | empty
        '''
        self.item_list(p)

    def p_stmt(self, p):
        '''
        stmt : assignment_stmt
             | local_stmt
             | call_stmt
             | function_stmt
             | return_stmt
        '''
        self.same(p)

    def p_assignment_stmt(self, p):
        '''
        assignment_stmt : chained_assignment_stmt
                        | augmented_assignment_stmt
        '''
        self.same(p)

    def p_chained_assignment_stmt(self, p):
        '''
        chained_assignment_stmt : assignment_target \
                                    ASSIGN \
                                    chained_assignment_stmt
        '''
        p[3].lineno += (p.lineno(2),)
        p[3].lexpos += (p.lexpos(2),)
        p[3].targets += (p[1],)
        p[0] = p[3]

    def p_chained_assignment_stmt_single(self, p):
        '''
        chained_assignment_stmt : assignment_target ASSIGN expr
        '''
        p[0] = ast.ChainedAssignmentStmt((p.lineno(2),),
                                         (p.lexpos(2),),
                                         targets = (p[1],),
                                         value = p[3])

    def p_augmented_assignment_stmt(self, p):
        '''
        augmented_assignment_stmt : assignment_target AUGASSIGN expr
        '''
        p[0] = ast.AugmentedAssignmentStmt(p.lineno(2),
                                           p.lexpos(2),
                                           target = p[1],
                                           op = p[2],
                                           value = p[3])

    def p_assignment_target(self, p):
        '''
        assignment_target : subscript_expr
                          | attribute_expr
                          | identifier_expr
        '''
        self.same(p)

    def p_local_stmt(self, p):
        '''
        local_stmt : LOCAL identifier_expr ASSIGN expr
        '''
        p[0] = ast.LocalStmt(p.lineno(1),
                             p.lexpos(1),
                             name = p[2].value,
                             value = p[4])

    def p_call_stmt(self, p):
        '''
        call_stmt : simple_call_stmt
                  | compound_call_stmt
        '''
        self.same(p)

    def p_simple_call_stmt(self, p):
        '''
        simple_call_stmt : call_expr
        '''
        p[0] = ast.SimpleCallStmt(p[1].lineno, p[1].lexpos, call_expr=p[1])

    def p_compound_call_stmt(self, p):
        '''
        compound_call_stmt : simple_call_stmt \
                               call_stmt_local_names \
                               call_stmt_body \
                               call_stmt_tail
        '''
        assert isinstance(p[1].call_expr.target, ast.IdentifierExpr)

        function_name = p[1].call_expr.target.value + ':'
        clauses = (ast.CompoundCallStmtClause(args = p[1].call_expr.args,
                                              local_names = p[2],
                                              body = p[3]),)

        if p[4] is not None:
            function_name += p[4].function_name
            clauses += p[4].clauses

        p[0] = ast.CompoundCallStmt(p[1].lineno,
                                    p[1].lexpos,
                                    function_name = function_name,
                                    clauses = clauses)

    def p_call_stmt_local_names(self, p):
        '''
        call_stmt_local_names : RARROW call_stmt_local_name_list
                              | empty
        '''
        p[0] = (p[2] if len(p) > 2 else ())

    def p_call_stmt_local_name_list(self, p):
        '''
        call_stmt_local_name_list : identifier_expr \
                                      COMMA \
                                      call_stmt_local_name_list
                                  | identifier_expr
        '''
        p[0] = (p[1].value,) + (p[3] if len(p) == 4 else ())

    def p_call_stmt_body(self, p):
        '''
        call_stmt_body : COLON newline stmt_list
        '''
        p[0] = p[3]

    def p_call_stmt_tail(self, p):
        '''
        call_stmt_tail : ELSE compound_call_stmt
        '''
        p[0] = p[2]

    def p_call_stmt_tail_bare_else(self, p):
        '''
        call_stmt_tail : ELSE call_stmt_body END
        '''
        clause = ast.CompoundCallStmtClause(args = (),
                                            local_names = (),
                                            body = p[2])
        p[0] = ast.CompoundCallStmt(function_name=':', clauses=(clause,))

    def p_call_stmt_tail_empty(self, p):
        '''
        call_stmt_tail : END
        '''
        p[0] = None

    def p_function_stmt(self, p):
        '''
        function_stmt : LOCAL function_def
                      | function_def
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[2].local = True
            p[0] = p[2]

    def p_function_def(self, p):
        '''
        function_def : FUNCTION \
                         identifier_expr \
                         function_args \
                         COLON \
                         newline \
                         stmt_list \
                         END
        '''
        p[0] = ast.FunctionStmt(p.lineno(1),
                                p.lexpos(1),
                                name = p[2].value,
                                args = p[3],
                                body = p[6],
                                local = False)

    def p_newline(self, p):
        '''
        newline : NEWLINE newline
                | NEWLINE
        '''
        pass

    def p_return_stmt(self, p):
        '''
        return_stmt : RETURN expr
                    | RETURN
        '''
        p[0] = ast.ReturnStmt(p.lineno(1),
                              p.lexpos(1),
                              value = (p[2] if len(p) == 3 else None))

    def p_call_arg_list_named(self, p):
        '''
        call_arg_list : named_expr_list
        '''
        p[0] = collections.OrderedDict(p[1])

    def p_named_expr_list(self, p):
        '''
        named_expr_list : named_expr_list_item COMMA named_expr_list
                        | named_expr_list_item COMMA
                        | named_expr_list_item
        '''
        p[0] = (p[1],) + (p[3] if len(p) == 4 else ())

    def p_named_expr_list_item(self, p):
        '''
        named_expr_list_item : identifier_expr ASSIGN expr
        '''
        p[0] = (p[1].value, p[3])

    def p_named_expr_list_item_attribute_ref(self, p):
        '''
        named_expr_list_item : identifier_expr LARROW attribute_expr
        '''
        p[0] = (p[1].value,
                ast.AttributeReferenceExpr(p[3].lineno,
                                           p[3].lexpos,
                                           target = p[3].target,
                                           name = p[3].name))

    def p_primary_expr_function_expr(self, p):
        '''
        primary_expr : function_expr
        '''
        self.same(p)

    def p_function_expr(self, p):
        '''
        function_expr : FUNCTION function_args expr END
        '''
        p[0] = ast.FunctionExpr(p.lineno(1), p.lexpos(1), args=p[2], body=p[3])

    def p_function_args(self, p):
        '''
        function_args : LPAREN function_arg_list RPAREN
        '''
        p[0] = p[2]

    def p_function_arg_list(self, p):
        '''
        function_arg_list : function_arg_list_item COMMA function_arg_list
                          | function_arg_list_item
                          | empty
        '''
        self.item_list(p)

    def p_function_arg_list_item(self, p):
        '''
        function_arg_list_item : identifier_expr
        '''
        p[0] = p[1].value

    def p_array_item_range_expr(self, p):
        '''
        array_item : expr COLON expr COLON expr
                   | expr COLON expr
        '''
        p[0] = ast.ArrayItemRange(p.lineno(2),
                                  p.lexpos(2),
                                  start = p[1],
                                  stop = p[3],
                                  step = (p[5] if len(p) == 6 else None))
