from __future__ import division, print_function, unicode_literals

from jel.parser import Parser as JELParser


class Parser(JELParser):

    # In Python 2.7, PLY insists that 'start' be str, not unicode
    start = str('module')

    def p_module(self, p):
        '''
        module : newline stmt_list
               | stmt_list
        '''
        pass

    def p_stmt_list(self, p):
        '''
        stmt_list : stmt newline stmt_list
                  | stmt
                  | empty
        '''
        pass

    def p_stmt(self, p):
        '''
        stmt : assignment_stmt
             | local_stmt
             | call_stmt
             | function_stmt
        '''
        pass

    def p_assignment_stmt(self, p):
        '''
        assignment_stmt : assignment_target ASSIGN expr
        '''
        pass

    def p_assignment_target(self, p):
        '''
        assignment_target : subscript_expr
                          | attribute_expr
                          | identifier_expr
        '''
        pass

    def p_local_stmt(self, p):
        '''
        local_stmt : LOCAL identifier_expr ASSIGN expr
        '''
        pass

    def p_call_stmt(self, p):
        '''
        call_stmt : call_expr call_stmt_body
        '''
        pass

    def p_call_stmt_body(self, p):
        '''
        call_stmt_body : COLON newline stmt_list call_stmt_tail
                       | empty
        '''
        pass

    def p_call_stmt_tail(self, p):
        '''
        call_stmt_tail : ELSE call_stmt
                       | ELSE call_stmt_body
                       | END
        '''
        pass

    def p_function_stmt(self, p):
        '''
        function_stmt : FUNCTION identifier_expr LPAREN RPAREN COLON newline stmt_list END
        '''
        pass

    def p_newline(self, p):
        '''
        newline : NEWLINE newline
                | NEWLINE
        '''
        pass

    def p_call_args_named(self, p):
        '''
        call_args : LPAREN named_expr_list RPAREN
        '''
        pass

    def p_named_expr_list(self, p):
        '''
        named_expr_list : named_expr_list_item COMMA named_expr_list
                        | named_expr_list_item COMMA
                        | named_expr_list_item
        '''
        pass

    def p_named_expr_list_item(self, p):
        '''
        named_expr_list_item : identifier_expr ASSIGN expr
        '''
        pass

    def p_array_item_range_expr(self, p):
        '''
        array_item : expr COLON expr COLON expr
                   | expr COLON expr
        '''
        pass
