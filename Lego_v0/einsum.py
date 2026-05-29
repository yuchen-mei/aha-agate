from lark import Lark, Tree, Transformer, Visitor, v_args

grammar = """
?start: assignment

assignment: access "=" expr        -> assign

access: IDENTIFIER "(" indices ")" -> access_tensor
      | IDENTIFIER                 -> access_variable

indices: index_expr ("," index_expr)*

expr: NUMBER                         -> literal
    | access                         -> expr_access
    | "(" expr ")"                   -> group
    | expr "+" expr                  -> add
    | expr "*" expr                    -> multiply

index_expr: index_expr "+" index_expr -> index_add
    | index_expr "*" index_expr       -> index_multiply
    | "(" index_expr ")"              -> index_group
    | INDEX                           -> index_literal
    | NUMBER                          -> index_number

NUMBER: /[0-9]+/
INDEX: /[a-zA-Z_][0-9a-zA-Z_]*/
IDENTIFIER: /[a-zA-Z_][0-9a-zA-Z_]*/
%ignore /\\s+/
%ignore /#.*/
"""

class IndexSetBuilder(Visitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs);
        self.index_set = set()
        self.tensor_dict = {}

    def access(self, tree):
        tensor, index_list = tree.children
        n_dims = len(index_list.children)

        if tensor not in self.tensor_dict:
            self.tensor_dict[tensor] = Tensor(tensor, n_dims)

        for idx, index in enumerate(index_list.children):
            if index not in self.index_set:
                self.index_set.add(index)
            self.tensor_dict[tensor].register_index_access(idx, index)

    def visit(self,tree):
        super().visit(tree)

    def __default__(self, tree):
        pass 

parser = Lark(grammar, parser='lalr')


def build_dict(parsed_code, is_dest, dest_dict, op_dict):
    if(parsed_code.data == "assign"):
        dest_dict, op_dict = build_dict(parsed_code.children[0], 1, dest_dict, op_dict)
        dest_dict, op_dict = build_dict(parsed_code.children[1], 0, dest_dict, op_dict)
        return dest_dict, op_dict
    elif(parsed_code.data == "access_tensor"):
        key = parsed_code.children[0]
        n_dims = len(parsed_code.children[1].children)
        id_list = []
        for idx in parsed_code.children[1].children:
            id_list.append(idx.children[0][0])
        if(is_dest):
            dest_dict[key[0]] = id_list
        else:
            op_dict[key[0]] = id_list 
        return dest_dict, op_dict
    elif (parsed_code.data == "access_variable"):
        key = parsed_code.children[0]
        if(is_dest):
            dest_dict[key[0]] = ['0']
        else:
            op_dict[key[0]] = ['0']

        return dest_dict, op_dict
    elif(parsed_code.data == "expr_access"):
        dest_dict, op_dict = build_dict(parsed_code.children[0], 0, dest_dict, op_dict)
        return dest_dict, op_dict
    elif(parsed_code.data == "multiply"):
        dest_dict, op_dict = build_dict(parsed_code.children[0], 0, dest_dict, op_dict)
        dest_dict, op_dict = build_dict(parsed_code.children[1], 0, dest_dict, op_dict)
        return dest_dict, op_dict
    elif(parsed_code.data == "add"):
        dest_dict, op_dict = build_dict(parsed_code.children[0], 0, dest_dict, op_dict)
        dest_dict, op_dict = build_dict(parsed_code.children[1], 0, dest_dict, op_dict)
        return dest_dict, op_dict
    elif(parsed_code.data == "group"):
        dest_dict, op_dict = build_dict(parsed_code.children[0], 0, dest_dict, op_dict)
        return dest_dict, op_dict

def build_expr(parsed_code): 
    if(parsed_code.data == "assign"):
        stmt_left = build_expr(parsed_code.children[0]) 
        stmt_right = build_expr(parsed_code.children[1])
        return stmt_left + "=" + stmt_right
    elif(parsed_code.data == "access_tensor"):
        return parsed_code.children[0][0] 
    elif (parsed_code.data == "access_variable"):
        return parsed_code.children[0][0]
    elif(parsed_code.data == "expr_access"):
        return  build_expr(parsed_code.children[0])
    elif(parsed_code.data == "multiply"):
        stmt_left = build_expr(parsed_code.children[0])
        stmt_right = build_expr(parsed_code.children[1])
        return "(" + stmt_left + "*" + stmt_right + ")"
    elif(parsed_code.data == "add"):
        stmt_left = build_expr(parsed_code.children[0])
        stmt_right = build_expr(parsed_code.children[1])
        return "(" + stmt_left + "+" + stmt_right + ")"
    elif(parsed_code.data == "group"):
        return build_expr(parsed_code.children[0]) 
