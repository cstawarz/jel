from __future__ import division, print_function, unicode_literals

from jel.parser import Parser as JELParser


class Parser(JELParser):

    # In Python 2.7, PLY insists that 'start' be str, not unicode
    start = str('experiment')

    def p_experiment(self, p):
        '''
        experiment : newline stmt_list
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
        stmt : component_def
             | variable_stmt
        '''
        pass

    def p_component_def(self, p):
        '''
        component_def : component_type_id component_instance_id component_attributes component_body
        '''
        pass

    def p_component_type_id(self, p):
        '''
        component_type_id : identifier_expr DOT component_type_id
                          | identifier_expr
        '''
        pass

    def p_component_instance_id(self, p):
        '''
        component_instance_id : identifier_expr
                              | string_literal_expr
                              | empty
        '''
        pass

    def p_component_attributes(self, p):
        '''
        component_attributes : dict_literal_expr
                             | parenthetic_expr
                             | empty
        '''
        pass

    def p_component_body(self, p):
        '''
        component_body : COLON newline stmt_list component_tail
                       | empty
        '''
        pass

    def p_component_tail(self, p):
        '''
        component_tail : ELSE component_def
                       | ELSE component_body
                       | END component_type_id component_instance_id
                       | END
        '''
        pass

    def p_variable_stmt(self, p):
        '''
        variable_stmt : variable_declarator identifier_expr
                      | variable_declarator identifier_expr assignment_op expr
                      | identifier_expr assignment_op expr
        '''
        pass

    def p_variable_declarator(self, p):
        '''
        variable_declarator : VAR
                            | LOCAL
        '''
        pass

    def p_assignment_op(self, p):
        '''
        assignment_op : ASSIGN
                      | PLUSASSIGN
        '''
        pass

    def p_newline(self, p):
        '''
        newline : NEWLINE newline
                | NEWLINE
        '''
        pass
