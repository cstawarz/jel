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
        p[0] = ast.Module(statements=(p[2] if len(p) == 3 else p[1]))

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
        p[3].targets += (p[1],)
        p[0] = p[3]

    def p_chained_assignment_stmt_single(self, p):
        '''
        chained_assignment_stmt : assignment_target ASSIGN expr
        '''
        p[0] = ast.ChainedAssignmentStmt(targets=(p[1],), value=p[3])

    def p_augmented_assignment_stmt(self, p):
        '''
        augmented_assignment_stmt : assignment_target \
                                      augmented_assignment_op \
                                      expr
        '''
        p[0] = ast.AugmentedAssignmentStmt(target = p[1],
                                           op = p[2],
                                           value = p[3])

    def p_assignment_target(self, p):
        '''
        assignment_target : subscript_expr
                          | attribute_expr
                          | identifier_expr
        '''
        self.same(p)

    def p_augmented_assignment_op(self, p):
        '''
        augmented_assignment_op : PLUSASSIGN
                                | MINUSASSIGN
        '''
        self.same(p)

    def p_local_stmt(self, p):
        '''
        local_stmt : LOCAL identifier_expr ASSIGN expr
        '''
        p[0] = ast.LocalStmt(name=p[2].value, value=p[4])

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
        p[0] = ast.CallStmt(head=p[1], body=None, tail=None)

    def p_compound_call_stmt(self, p):
        '''
        compound_call_stmt : simple_call_stmt call_stmt_body call_stmt_tail
        '''
        p[1].body = p[2]
        p[1].tail = p[3]
        p[0] = p[1]

    def p_call_stmt_body(self, p):
        '''
        call_stmt_body : COLON newline stmt_list
        '''
        p[0] = p[3]

    def p_call_stmt_tail(self, p):
        '''
        call_stmt_tail : ELSE compound_call_stmt
                       | ELSE call_stmt_body END
                       | END
        '''
        p[0] = (p[2] if len(p) > 2 else None)

    def p_function_stmt(self, p):
        '''
        function_stmt : FUNCTION identifier_expr function_args function_body
        '''
        pass

    def p_function_body(self, p):
        '''
        function_body : COLON newline stmt_list END
        '''
        pass

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
        p[0] = ast.ReturnStmt(value=(p[2] if len(p) == 3 else None))

    def p_call_args_named(self, p):
        '''
        call_args : LPAREN named_expr_list RPAREN
        '''
        p[0] = collections.OrderedDict(p[2])

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

    def p_primary_expr_function_expr(self, p):
        '''
        primary_expr : function_expr
        '''
        pass

    def p_function_expr(self, p):
        '''
        function_expr : FUNCTION function_args expr END
        '''
        pass

    def p_function_args(self, p):
        '''
        function_args : LPAREN function_arg_list RPAREN
        '''
        pass

    def p_function_arg_list(self, p):
        '''
        function_arg_list : function_arg_list_item COMMA function_arg_list
                          | function_arg_list_item
                          | empty
        '''
        pass

    def p_function_arg_list_item(self, p):
        '''
        function_arg_list_item : identifier_expr
        '''
        pass

    def p_array_item_range_expr(self, p):
        '''
        array_item : expr COLON expr COLON expr
                   | expr COLON expr
        '''
        pass
