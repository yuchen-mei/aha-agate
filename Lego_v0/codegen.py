import math

class Operation(object):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def __repr__(self):
        return self.__str__()

def merge_intersect(lattice1, lattice2):
    lattice = []

    if(len(lattice1) == 0):
        return lattice2
    
    elif(len(lattice2) == 0):
        return lattice1
    
    else: 
        for point1 in lattice1:
            for point2 in lattice2:    
                if(point1 != [] and point2 != []):  
                    lattice.append(point2 + point1)

    return lattice

def merge_union(lattice1, lattice2):
    lattice = []

    for point1 in lattice1:
        if point1 != []:
            lattice.append(point1)
    
    for point2 in lattice2:
        if point2 != []:
            lattice.append(point2)
    
    if(lattice1 != [] and lattice2 != []):
        lattice.extend(merge_intersect(lattice1, lattice2))

    return lattice

def ispresent(stmt, id_dict, id):
    for i in id_dict[stmt]:
        if i == id:
            return True

def sort_lattice(lattice):
    return sorted(lattice, key=lambda i: len(i), reverse=True)

def get_lattice(stmt, id_dict, id):
    # When the input stmt is a identity expression
    # stmt.right stores the variable
    # stmt.left and stmt.op are both None
    lattice = []

    if not isinstance(stmt.left, str) and not isinstance(stmt.right, str) and stmt.left is not None and stmt.right is not None:
        left = get_lattice(stmt.left, id_dict, id)
        right = get_lattice(stmt.right, id_dict, id)
        if(stmt.op == '+'):
            lattice = merge_union(left, right)
            return sort_lattice(lattice)
        if(stmt.op == '*'):
            lattice = merge_intersect(left, right)
            return sort_lattice(lattice)

    elif not isinstance(stmt.left, str) and stmt.left is not None and stmt.right is not None:
        left = get_lattice(stmt.left, id_dict, id)
        if(ispresent(stmt.right, id_dict, id)):
            right = [[id + stmt.right]]
        else:
            right = []
        if(stmt.op == '+'):
            lattice = merge_union(left, right)
            return sort_lattice(lattice)
        if(stmt.op == '*'):  
            lattice = merge_intersect(left, right)
            return sort_lattice(lattice)

    elif not isinstance(stmt.right, str) and stmt.left is not None and stmt.right is not None:
        right = get_lattice(stmt.right, id_dict, id)
        if(ispresent(stmt.left, id_dict, id)):
            left = [[id + stmt.left]]
        else:
            left =  []
        if(stmt.op == '+'):
            lattice = merge_union(left, right)
            return sort_lattice(lattice)
        if(stmt.op == '*'):
            lattice = merge_intersect(left, right)
            return sort_lattice(lattice)

    else:
        if stmt.left is not None and (ispresent(stmt.left, id_dict, id)):
            left = [[id + stmt.left]]
        else:
            left = []
        if stmt.right is not None and (ispresent(stmt.right, id_dict, id)):
            right = [[id + stmt.right]]
        else:
            right = []
        if(stmt.op == '+'):
            lattice = merge_union(left, right)
            return sort_lattice(lattice)
        if(stmt.op == '*'):
            lattice = merge_intersect(left, right)
            return sort_lattice(lattice)
        if stmt.op is None:
            assert stmt.left is None
            assert stmt.right is not None
            return sort_lattice(right)

def expr_to_stmt(expr):
    
    stack = []
    for c in expr:
        if c == ' ':
            continue
        if c == ')':
            right = stack.pop()
            # in a case where the expression is identity, after the first pop
            # the only element left in the stack is a '('
            op = None
            left = None
            if len(stack) > 2:
                op = stack.pop()
                left = stack.pop()
            # popping the '('
            stack.pop()
            stack.append(Operation(op, left, right))
        else:
            stack.append(c)

    stmt = stack[0]

    if isinstance(stmt, str):
        stmt = Operation(None, None, stmt)

    return stmt

def expr_to_lattice(expr, id_dict, id):
    stack = []
    for c in expr:
        if c == ' ':
            continue
        if c == ')':
            right = stack.pop()
            # in a case where the expression is identity, after the first pop
            # the only element left in the stack is a '('
            op = None
            left = None
            if len(stack) > 2:
                op = stack.pop()
                left = stack.pop()
            # popping the '('
            stack.pop()
            stack.append(Operation(op, left, right))
        else:
            stack.append(c)

    stmt = stack[0]
    
    if isinstance(stmt, str):
        stmt = Operation(None, None, stmt)

    lattice = get_lattice(stmt, id_dict, id)
    return lattice

def get_stmt(stmt, id_dict, dtype):
    # When the input stmt is a identity expression
    # stmt.right stores the variable
    # stmt.left and stmt.op are both None
    lower_stmts = []

    if not isinstance(stmt.left, str) and not isinstance(stmt.right, str) and stmt.left is not None and stmt.right is not None:
        left, left_op_cnt = get_stmt(stmt.left, id_dict, dtype)
        right, right_op_cnt = get_stmt(stmt.right, id_dict, dtype)
        op_cnt = left_op_cnt + right_op_cnt + 1
        if(dtype == "bf16"):
            if(stmt.op == '+'):
                lower_stmts = "bf16_add(" + left + ", " + right + ")"
                return lower_stmts, op_cnt
            if(stmt.op == '*'):
                lower_stmts = "bf16_mul(" + left + ", " + right + ")"
                return lower_stmts, op_cnt
        else:
            if(stmt.op == '+'):
                lower_stmts = "(" + left + "+" + right + ")"
                return lower_stmts, op_cnt
            if(stmt.op == '*'):
                lower_stmts = "(" + left + "*" + right + ")"
                return lower_stmts, op_cnt
  
    elif not isinstance(stmt.left, str) and stmt.left is not None and stmt.right is not None:
        left, left_op_cnt = get_stmt(stmt.left, id_dict, dtype)
        op_cnt = left_op_cnt + 1
        if(id_dict[stmt.right] == ['-']):
            right = "0"
        elif(id_dict[stmt.right] == ['0']):
            right = stmt.right + "_vals[" + id_dict[stmt.right][-1] + "]"
        else:
            right = stmt.right + "_vals[" + id_dict[stmt.right][-1] + stmt.right + "]"  
        if(dtype == "bf16"):
            if(stmt.op == '+'):
                lower_stmts = "bf16_add(" + left + ", " + right + ")"
                return lower_stmts, op_cnt
            if(stmt.op == '*'):
                lower_stmts = "bf16_mul(" + left + ", " + right + ")"
                return lower_stmts, op_cnt
        else:
            if(stmt.op == '+'):
                lower_stmts = "(" + left + "+" + right + ")"
                return lower_stmts, op_cnt
            if(stmt.op == '*'):
                lower_stmts = "(" + left + "*" + right + ")"
                return lower_stmts, op_cnt
        

    elif not isinstance(stmt.right, str) and stmt.left is not None and stmt.right is not None:
        right, right_op_cnt = get_stmt(stmt.right, id_dict, dtype)
        op_cnt = right_op_cnt + 1
        if(id_dict[stmt.left] == ['-']):
            left = "0"
        elif(id_dict[stmt.left] == ['0']):
            left = stmt.left + "_vals[" + id_dict[stmt.left][-1] + "]"
        else:
            left =  stmt.left + "_vals[" + id_dict[stmt.left][-1] + stmt.left + "]"
        if(dtype == "bf16"):
            if(stmt.op == '+'):
                lower_stmts = "bf16_add(" + left + ", " + right + ")"
                return lower_stmts, op_cnt
            if(stmt.op == '*'):
                lower_stmts = "bf16_mul(" + left + ", " + right + ")"
                return lower_stmts, op_cnt
        else:
            if(stmt.op == '+'):
                lower_stmts = "(" + left + "+" + right + ")"
                return lower_stmts, op_cnt
            if(stmt.op == '*'):
                lower_stmts = "(" + left + "*" + right + ")"
                return lower_stmts, op_cnt
            

    else:
        if stmt.left is not None and (id_dict[stmt.left] == ['-']):
            left = "0"
        elif stmt.left is not None and (id_dict[stmt.left] == ['0']):
            left = stmt.left + "_vals[" + id_dict[stmt.left][-1] + "]"
        elif stmt.left is not None:
            left = stmt.left + "_vals[" + id_dict[stmt.left][-1] + stmt.left + "]"

        if(id_dict[stmt.right] == ['-']):
            right = "0"
        elif(id_dict[stmt.right] == ['0']):
            right = stmt.right + "_vals[" + id_dict[stmt.right][-1] + "]"
        else:
            right = stmt.right + "_vals[" + id_dict[stmt.right][-1] + stmt.right + "]"
        if(dtype == "bf16"):
            if(stmt.op == '+'):
                lower_stmts = "bf16_add(" + left + ", " + right + ")"
                return lower_stmts, 1
            if(stmt.op == '*'):
                lower_stmts = "bf16_mul(" + left + ", " + right + ")"
                return lower_stmts, 1
        else:
            if(stmt.op == '+'):
                lower_stmts = "(" + left + "+" + right + ")"
                return lower_stmts, 1
            if(stmt.op == '*'):
                lower_stmts = "(" + left + "*" + right + ")"
                return lower_stmts, 1

        if stmt.op is None:
            assert stmt.right is not None
            assert stmt.left is None
            return "(" + right + ")", 0

def pos_read(curr_id, op_list, id_dict, level):
    
    stmt = ""
    loop_counter = 0 

    for op in op_list:
        if curr_id in id_dict[op]:
            curr_id_pos = id_dict[op].index(curr_id) + 1
            if curr_id_pos == 1:
                prev_id = "0"
                next_id = "1"
            else: 
                prev_id = id_dict[op][curr_id_pos - 2] + op
                next_id = prev_id + " + 1"
            if loop_counter != 0:
                stmt = stmt + "\n"
            stmt = stmt + "    " * level
            stmt = stmt + "int " + curr_id + op
            stmt = stmt + " = " + op + str(curr_id_pos) + "_pos[" + prev_id + "];"
            stmt = stmt + "\n"
            stmt = stmt + "    " * level
            stmt = stmt + "int p" + op + str(curr_id_pos) + "_end" 
            stmt = stmt + " = " + op + str(curr_id_pos) + "_pos[" + next_id + "];"
            loop_counter += 1

    return [stmt]

def while_stmt_open(point, id_dict, level):

    stmt = "    " * level
    stmt += "while("

    if len(point) != 0:
        arr_read = point[0][1]
        arr_idx  = point[0][0] 
        arr_idx_pos = id_dict[arr_read].index(arr_idx)
        stmt = stmt + point[0]
        stmt = stmt + (" < p") + arr_read + str(arr_idx_pos + 1) + ("_end") 
        point = point[1:]
    
        for id in point:
            arr_read = id[1]
            arr_idx  = id[0] 
            arr_idx_pos = id_dict[arr_read].index(arr_idx)
            stmt = stmt + " && "
            stmt = stmt + id
            stmt = stmt + (" < p") + arr_read + str(arr_idx_pos + 1) + ("_end") 


    stmt = stmt + "){" 

    return [stmt]

def while_stmt_close(point, id_dict, level):
    return ["    " * level + "}"]

def id_init(point, id_dict, level):

    stmt = "    " * (level + 1)   
    if(len(point) != 0):
        arr_idx = point[0][0]
        arr_read = point[0][1]
        arr_idx_pos = id_dict[arr_read].index(arr_idx) + 1
        stmt = stmt + "int " + point[0] + "0 = " 
        stmt = stmt + arr_read +  str(arr_idx_pos) + "_crd[" + point[0] + "];"
        point = point[1:] 

        for id in point:
            stmt = stmt + "\n"
            stmt += "    " * (level + 1)
            arr_idx = id[0]
            arr_read = id[1]
            arr_idx_pos = id_dict[arr_read].index(arr_idx) + 1
            stmt = stmt + "int " + id + "0 = " 
            stmt = stmt + arr_read +  str(arr_idx_pos) + "_crd[" + id + "];"

    return [stmt]

def id_merge(point, id_dict, level):

    stmt = ""
    if(len(point) != 0):
        if(len(point) == 1):
            arr_idx = point[0][0]
            stmt = stmt + "int " + arr_idx + " = " + point[0] + "0;"
        else:
            arr_idx = point[0][0]
            stmt = stmt + "int " + arr_idx + " = " 
            stmt = stmt + "min(" + point[0] + "0"
            num_point = len(point)
            point = point[1:]
            while(len(point) != 0):
                id = point[0]
                if(len(point) != 1):
                    stmt += ", min(" + id + "0"
                else:           
                    stmt = stmt + ", " + id + "0"
                point = point[1:]

            for i in range(num_point - 1):
                stmt = stmt + ")"   

            stmt = stmt + ";"

    return ["    " * (level + 1) + stmt]

def if_stmt_open(sub_point, id_dict, level):

    if(sub_point != []):
        stmt = "if("

        stmt = stmt + sub_point[0] + "0"
        stmt = stmt + (" == ")
        stmt = stmt + sub_point[0][0]
        sub_point = sub_point[1:]

        for id in sub_point:
            stmt = stmt + " && "
            stmt = stmt + id + "0"
            stmt = stmt + (" == ")
            stmt = stmt + id[0]

        stmt = stmt + "){"

    return ["    " * (level + 1) + stmt]

def elif_stmt_open(sub_point, id_dict, level):

    if(sub_point != []):
        stmt = "else if("

        stmt = stmt + sub_point[0] + "0"
        stmt = stmt + (" == ")
        stmt = stmt + sub_point[0][0]
        sub_point = sub_point[1:]

        for id in sub_point:
            stmt = stmt + " && "
            stmt = stmt + id + "0"
            stmt = stmt + (" == ")
            stmt = stmt + id[0]

        stmt = stmt + "){"

    return ["    " * (level + 1) + stmt]

def if_stmt_close(sub_point, id_dict, level):
    return ["    " * (level + 1) + "}"]

def id_increment(point, id_dict, level):
    stmt = ""
    stmt = "    " * (level + 1)
    
    if(len(point) != 0):
        arr_idx = point[0][0]
        stmt = stmt + point[0] + " += (int)"
        stmt = stmt + "(" + point[0] + "0 == " + arr_idx  + ");" 
        point = point[1:]
        for id in point:
            stmt = stmt + "\n"
            stmt += "    " * (level + 1)
            stmt = stmt + id + " += (int)"
            stmt = stmt + "(" + id + "0 == " + id[0] + ");"

    return [stmt]

def get_sub_lattice(point, lattice):

    sub_lattice = []

    for every_point in lattice: 
        ctr1 = 0
        ctr2 = 0
        for id1 in every_point: 
            for id2 in point: 
                if id1 == id2: 
                    ctr2 += 1; 
            ctr1 += 1; 
        if ctr1 == ctr2:
            sub_lattice.append(every_point)

    return sub_lattice

def get_sub_point_dict(sub_point, id_dict, op_list):

    idx = sub_point[0][0]
    
    sub_point_id_dict = {}
    sub_point_op_list = []

    for id in sub_point: 
        arr_read = id[1]
        sub_point_op_list.append(arr_read)

    not_in_sub_point = []

    for element in op_list: 
        if element not in sub_point_op_list: 
            not_in_sub_point.append(element)
    
    for element in sub_point_op_list: 
        sub_point_id_dict[element] = id_dict[element]

    for element in not_in_sub_point:
        if(idx in id_dict[element]):    
            sub_point_id_dict[element] = ['-']    
        else: 
            sub_point_id_dict[element] = id_dict[element]

    return sub_point_id_dict

def get_sub_point_schedule(sub_point, schedule):
    return schedule[1:]

def ap_mem_stmt(sub_point, id_dict, level, curr_id):

    stmt = ""
    loop_counter = 0
    for id in sub_point:
        arr_read = id[1]
        arr_idx  = id[0]
        if(arr_idx in id_dict[arr_read]):
            if(id_dict[arr_read][-1] == arr_idx):
                if(loop_counter != 0):  
                    stmt = stmt + "\n"  
                stmt = stmt + "    " * (level + 2)
                stmt = stmt + "tile_" + arr_read + " = " + "tensor_mem_op_" + str(len(id_dict[arr_read])) + "(" + "tensor_" + arr_read + ", " + id + ");"
                loop_counter += 1

    return [stmt]

def cp_mem_stmt(op_list, sub_point, id_dict, level, curr_id, split_dict, mode, process_csf):


        valid_op_list = [] 
    
        for op in op_list: 
            if not (curr_id in id_dict[op]): 
                if(id_dict[op] != ['-']):
                    valid_op_list.append(op)
             
        for id in sub_point:
            arr_read = id[1]
            arr_idx  = id[0]
            if(arr_idx in id_dict[arr_read]):
                if(id_dict[arr_read][-1] == arr_idx):
                    valid_op_list.append(arr_read)

        valid_op_list = [x for x in op_list if x in valid_op_list]
    
        stmt = ""
        loop_counter = 0
        for id in sub_point:
            arr_read = id[1]
            arr_idx  = id[0]
            if(arr_idx in id_dict[arr_read]):
                if(id_dict[arr_read][-1] == arr_idx):

                    if(loop_counter != 0):  
                        stmt = stmt + "\n" 

                    if((mode == "rtl") or (len(sub_point) != 1) or (len(valid_op_list) != 1)):
                        stmt = stmt + "    " * (level + 2)
                        stmt = stmt + "subtile_" + arr_read + " = " + "tile_mem_op_" + str(len(id_dict[arr_read])) + "(" + "tile_" + arr_read + ", " + id + ");"
                        stmt = stmt + "\n"
                        if(process_csf):
                            stmt = stmt + "    " * (level + 2)
                            stmt = stmt + "subtile_" + arr_read + " = " + "process_csf_" + str(len(id_dict[arr_read])) + "(" + "subtile_" + arr_read
                            for id1 in id_dict[arr_read]:
                                stmt = stmt + ", " + str(int(split_dict[id1][1]) - 1)
                            stmt = stmt + ");"

                    if(mode != "rtl"):
                        if(len(sub_point) != 1 or len(valid_op_list) != 1):
                        
                            stmt = stmt + "    " * (level + 2)
                            stmt = stmt + "id_store_" + arr_read + " = "

                            cprod = 1
                            for id1 in id_dict[arr_read][::-1]:
                                stmt += " + " + id1 + " * " + str(cprod)
                                cprod *= int(math.ceil(split_dict[id1][0]/split_dict[id1][1]))
                            
                            stmt += ";"
                            stmt += "\n"                            
                    
                    loop_counter += 1
    
        return [stmt]

def ap_op_stmt(op_list, sub_point, id_dict, id_dict_true, level, curr_id, dest, split_dict, mode, workspace):

    stmt = ""

    valid_op_list = [] 
    
    for op in op_list: 
        if not (curr_id in id_dict[op]): 
            if(id_dict[op] != ['-']):
                valid_op_list.append(op)
             
    for id in sub_point:
        arr_read = id[1]
        arr_idx  = id[0]
        if(arr_idx in id_dict[arr_read]):
            if(id_dict[arr_read][-1] == arr_idx):
                valid_op_list.append(arr_read)

    valid_op_list = [x for x in op_list if x in valid_op_list]

    if(len(valid_op_list) == 1):
        if(mode == "onyx" or mode == "opal"):
            stmt = "    " * (level + 2) + "/* Reserved operation */"

    for op in op_list: 
        if op not in valid_op_list: 
            if(len(valid_op_list) != 1 or mode == "rtl"): 
                stmt = stmt + "    " * (level + 2)
                stmt += "tile_" + op + " = " 
                stmt += "tensor_zero_op_" + str(len(id_dict_true[op])) + "(" + "tile_" + op  + ");"
                stmt += "\n"
    
    if(len(valid_op_list) != 1 or mode == "rtl"):    
        stmt += "    " * (level + 2)
        stmt += "tile_name = \"tile\";" 
        for key in id_dict_true.keys():
            for id in id_dict_true[key]:
                stmt += "\n"
                stmt += "    " * (level + 2)
                stmt += "tile_name += " + "\"_" + id + key + "_\"" + " + std::to_string(" + id + ");"  

    stmt += "\n"           

    if(valid_op_list != []):
        if(len(valid_op_list) != 1 or mode == "rtl"):
            stmt += "    " * (level + 2)
            stmt += "float* partial = tile_operate" + "(" + "tile_" + op_list[0]
            op_list = op_list[1:]

            for op in op_list:
                stmt += ", " + "tile_" + op 

            stmt += ", tile_name"
            
            if mode == "rtl":
                stmt += ", subtile_paths, mode"  

            stmt += ");\n"
        for name in dest: 
            dest_name = name

        if(workspace):
            stmt += "    " * (level + 2)
            stmt += "subtile_workspace[" + dest[dest_name][0]
            for dim_count, id in enumerate(dest[dest_name][1:]):
                for i in range(dim_count + 1, len(dest[dest_name])):
                    stmt += " * " + str(int(math.ceil(split_dict[dest[dest_name][i]][0] / split_dict[dest[dest_name][i]][1])))
                stmt += " + " + id
            stmt += "].push_back(partial);"       

    return [stmt]

def cp_op_stmt(op_list, sub_point, id_dict, id_dict_true, level, curr_id, mode, split_dict, cg_source_id, dest, cg_source_map, workspace, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict):
    
        stmt = ""
    
        valid_op_list = [] 

        for keys in dest.keys():
            dest_read = keys
        
        for op in op_list: 
            if not (curr_id in id_dict[op]): 
                if(id_dict[op] != ['-']):
                    valid_op_list.append(op)
                
        for id in sub_point:
            arr_read = id[1]
            arr_idx  = id[0]
            if(arr_idx in id_dict[arr_read]):
                if(id_dict[arr_read][-1] == arr_idx):
                    valid_op_list.append(arr_read)
    
        valid_op_list = [x for x in op_list if x in valid_op_list]
    
        if(len(valid_op_list) == 1):
            if(mode == "onyx" or mode == "opal"):
                stmt = "    " * (level + 2) + "/* Reserved operation */"

        if(unroll != "0"): 
            unroll_factor = 2
        else: 
            unroll_factor = 1
    
        for op in op_list: 
            if op in valid_op_list: 
                if(len(valid_op_list) != 1):
                    if(mode == "onyx" or mode == "opal"): 
                        stmt = stmt + "    " * (level + 2)
                        stmt = stmt + "if(!store_" + op + "1[id_store_" + op + "]){"
                        stmt = stmt + "\n"
                        stmt = stmt + "    " * (level + 3)
                        stmt = stmt + "store_" + op + "1[id_store_" + op + "] = 1;"
                        stmt = stmt + "\n"
                        stmt = stmt + "    " * (level + 3)
                        stmt = stmt + "cg_subtile_" + op + "1 = " + "cg_tile_mem_op_" + str(len(id_dict_true[op])) + "(" + "cg_subtile_" + op + "1, store_subtile_" + op + "1, " + "subtile_" + op +  ", " + "id_store_" + op + ");"    
                        stmt = stmt + "\n"
                        stmt = stmt + "    " * (level + 2)
                        stmt = stmt + "}"
                        stmt = stmt + "\n" 

                        """"
                        if(unroll):   
                            stmt = stmt + "    " * (level + 2)
                            stmt = stmt + "if(!store_" + op + "2[id_store_" + op + "] && ((curr_subtile_num % " + str(unroll_factor) + ") == 1)){"
                            stmt = stmt + "\n"
                            stmt = stmt + "    " * (level + 3)
                            stmt = stmt + "store_" + op + "2[id_store_" + op + "] = 1;"
                            stmt = stmt + "\n"
                            stmt = stmt + "    " * (level + 3)
                            stmt = stmt + "cg_subtile_" + op + "2 = " + "cg_tile_mem_op_" + str(len(id_dict_true[op])) + "(" + "cg_subtile_" + op + "2, store_subtile_" + op + "2, " + "subtile_" + op +  ", " + "id_store_" + op + ");"    
                            stmt = stmt + "\n"
                            stmt = stmt + "    " * (level + 2)
                            stmt = stmt + "}"
                            stmt = stmt + "\n"   
                        """                   

            if op not in valid_op_list: 
                if(len(valid_op_list) != 1 or mode == "rtl"):    
                    if(mode == "onyx" or mode == "opal"):
                        stmt = stmt + "    " * (level + 2)
                        stmt += "id_store_" + op + " = " + "store_size_" + op + ";"
                        stmt += "\n"
                        stmt += "    " * (level + 2)
                        stmt += "if(!store_" + op + "1[id_store_" + op + "]){"
                        stmt += "\n"
                        stmt += "    " * (level + 3)
                        stmt += "store_" + op + "1[id_store_" + op + "] = 1;"
                        stmt += "\n"
                        stmt += "    " * (level + 3)
                        stmt += "cg_subtile_" + op + "1 = cg_tile_zero_op_" + str(len(id_dict_true[op])) + "(" + "store_subtile_" + op + "1, cg_subtile_" + op + "1, id_store_" + op + ");"
                        stmt += "\n"
                        stmt += "    " * (level + 2)
                        stmt += "}"
                        stmt += "\n"
                        stmt = stmt + "    " * (level + 2)
                        stmt += "subtile_" + op + " = " 
                        stmt += "tile_zero_op_" + str(len(id_dict_true[op])) + "(" + "subtile_" + op  + ");"
                        stmt += "\n" 
                    elif(mode == "rtl"): 
                        stmt = stmt + "    " * (level + 2)
                        stmt += "subtile_" + op + " = " 
                        stmt += "tile_zero_op_" + str(len(id_dict_true[op])) + "(" + "subtile_" + op  + ");"
                        stmt += "\n" 
    
        if(valid_op_list != []):
            if(len(valid_op_list) != 1 or mode == "rtl"):

                if(mode == "onyx" or mode == "opal"):
                    # stmt += "    " * (level + 2)  + "if((curr_subtile_num % " + str(unroll_factor) + ") == 0){\n"
                    for op in op_list:
                        stmt += "    " * (level + 2)                        
                        stmt += "cg_extents_" + op + "1 = "
                        stmt += "build_extents_" + str(len(id_dict_true[op])) + "(" + "cg_extents_" + op + "1, store_subtile_" + op + "1, id_store_" + op + ");"
                        stmt += "\n"
                    # stmt += "    " * (level + 2)  + "}\n"
                    """
                    if(unroll):
                        stmt += "    " * (level + 2)  + "if((curr_subtile_num % " + str(unroll_factor) + ") == 1){\n"
                        for op in op_list:
                            stmt += "    " * (level + 3)                        
                            stmt += "cg_extents_" + op + "2 = "
                            stmt += "build_extents_" + str(len(id_dict_true[op])) + "(" + "cg_extents_" + op + "2, store_subtile_" + op + "2, id_store_" + op + ");"
                            stmt += "\n"
                        stmt += "    " * (level + 2)  + "}\n"
                    """

                stmt += "    " * (level + 2)
                stmt += "mkdir(data_path, 0777);"
                stmt += "\n"
                stmt += "\n"

                if(mode == "rtl"):
                    stmt += "    " * (level + 2)
                    stmt += "subtile_path = out_dir + \"/set_" + dest[dest_read][0] + "_\" + std::to_string(" + dest[dest_read][0] + ");"
                    stmt += "\n"
                    for id in dest[dest_read][1:]:
                        stmt += "    " * (level + 2)
                        stmt += "subtile_path += \"_" + id + "_\" + std::to_string(" + id + ");"
                        stmt += "\n"
                    stmt += "    " * (level + 2)
                    stmt += "mkdir(subtile_path.c_str(), 0777);"
                    stmt += "\n"
                    stmt += "\n"
                    stmt += "    " * (level + 2)
                    stmt += "subtile_path += \"/subtile_pair_\" + std::to_string(curr_subtile_num);"
                    stmt += "\n"
                    stmt += "    " * (level + 2)
                    stmt += "const char *subtile_path_str = subtile_path.c_str();"
                    stmt += "\n"
                    stmt += "    " * (level + 2)
                    stmt += "mkdir(subtile_path_str, 0777);"
                    stmt += "\n"
                    stmt += "    " * (level + 2)
                    stmt += "output_gold_path = subtile_path + \"/output_gold.h\";"
                    stmt += "\n"   
                         
                stmt += "    " * (level + 2)
                if(ap_gcheck and (mode == "onyx" or mode == "opal")): 
                    stmt += "output_gold_file.open(output_gold_path + \"/\" + std::to_string(curr_subtile_num)  + \".txt\");\n"
                else:
                    stmt += "output_gold_file.open(output_gold_path, std::ios_base::app);"
                stmt += "\n"
                stmt += "    " * (level + 2)

                stmt += "float *partial = nullptr;\n"

                if(mode == "rtl"): 
                    stmt += "if (mode == \"tiling\")\n"
                    stmt += "    " * (level + 3)
                    stmt += "partial = subtile_gold" + "(" + "subtile_" + op_list[0]

                    for op in op_list[1:]:
                        stmt += ", " + "subtile_" + op 
                    
                    if(nnz_ctr):
                        stmt += ", curr_subtile_num, output_gold_file, nnz_check_file);"   
                    else: 
                        stmt += ", curr_subtile_num, output_gold_file);"  

                    stmt += "\n"
                    stmt += "    " * (level + 2)
                    stmt += "else if (mode == \"reduce\")\n"
                    stmt += "    " * (level + 3)
                    stmt += "partial = read_subtile_output(subtile_path);\n"
                    stmt += "    " * (level + 2)
                    stmt += "else\n"
                    stmt += "    " * (level + 3)
                    stmt += "assert(0 && \"mode must be \'reduce\' or \'tiling\'\");\n"
                elif(mode == "onyx" or mode == "opal"):
                    if(gcheck or nnz_ctr): 
                        stmt += "    " * (level + 2)
                        stmt += "partial = subtile_gold" + "(" + "subtile_" + op_list[0]
                        for op in op_list[1:]:  
                            stmt += ", " + "subtile_" + op
                        if(nnz_ctr):
                            stmt += ", curr_subtile_num, output_gold_file, nnz_check_file);"
                        else: 
                            stmt += ", curr_subtile_num, output_gold_file);"
                        stmt += "\n"

                if(workspace):
                    stmt += "    " * (level + 2)
                    stmt += "subtile_workspace[" + dest[dest_read][0]
                    for dim_count, id in enumerate(dest[dest_read][1:]):
                        for i in range(dim_count + 1, len(dest[dest_read])):
                            stmt += " * " + str(int(math.ceil(split_dict[dest[dest_read][i]][0] / split_dict[dest[dest_read][i]][1])))
                        stmt += " + " + id
                    stmt += "].push_back(partial);"       
                    stmt += "\n"
                    stmt += "\n"

                if(mode == "rtl"):
                    stmt += "    " * (level + 2)
                    stmt += "if (mode == \"tiling\") {\n"
                    for op in op_list:
                        
                        if id_dict_true[op] != ['0']:
                            tensor_dim = len(id_dict_true[op])
                        else:
                            tensor_dim = 0

                        is_dense = "false"
                        if (tensor_format_dict[op] == "d"):
                            is_dense = "true"

                        for i in range(tensor_dim):
                            stmt += "    " * (level + 3)
                            stmt += "rtl_mode_data_printer(subtile_" + op + ".pos" + str(i + 1) + ", subtile_path, "
                            stmt += "\"" + op +  "\", " + "\"seg\", " + "\"" + str(cg_source_map[op][i]) + "\"," +  is_dense + ");"
                            stmt += "\n"    
                            stmt += "    " * (level + 3)
                            stmt += "rtl_mode_data_printer(subtile_" + op + ".crd" + str(i + 1) + ", subtile_path, "
                            stmt += "\"" + op + "\", " + "\"crd\", " + "\"" + str(cg_source_map[op][i]) + "\"," +  is_dense + ");"
                            stmt += "\n"

                        if tensor_dim == 0:
                            stmt += "    " * (level + 3)
                            stmt += "rtl_mode_data_printer(subtile_" + op + ".pos" + str(1) + ", subtile_path, "
                            stmt += "\"" + op +  "\", " + "\"seg\", " + "\"" + "0" + "\"," +  is_dense + ");"
                            stmt += "\n"    
                            stmt += "    " * (level + 3)
                            stmt += "rtl_mode_data_printer(subtile_" + op + ".crd" + str(1) + ", subtile_path, "
                            stmt += "\"" + op + "\", " + "\"crd\", " + "\"" + "0" + "\"," +  is_dense + ");"
                            stmt += "\n"
                        
                        stmt += "    " * (level + 3)
                        stmt += "rtl_vals_data_printer(subtile_" + op + ".vals, subtile_path, " + "\"" + op + "\"" + ");"
                        stmt += "\n"
                        
                        stmt += "    " * (level + 3)
                        stmt += "rtl_size_data_printer_" + str(len(id_dict_true[op])) + "(subtile_path" + ", " + "\"" + op + "\""

                        
                        if id_dict_true[op] == ['0']:
                            stmt += ", 1);\n"
                        else:
                            for idx in cg_source_map[op]:
                                id = cg_source_id[op][idx]
                                stmt += ", " + str(split_dict[id][1]) 
                            stmt += ");"
                            stmt += "\n"

                        for dest_name, ids in dest.items():
                            stmt += "    " * (level + 3)
                            stmt += "rtl_size_data_printer_" + str(len(ids)) + "(subtile_path" + ", " + "\"" + "out" + "\""
                            for idx in ids:
                                if(idx == '0'): 
                                    stmt += ", " + str(1)
                                else:
                                    stmt += ", " + str(split_dict[idx][1])
                        stmt += ");"
                        stmt += "\n"
                        stmt += "\n"

                        if lut_tensor is not None:
                            for lut in lut_tensor:
                                stmt += "        " + "rtl_lut_data_printer(subtile_path, \"" + lut + "\");\n"
                        
                        stmt += "         " + "rtl_dump_dtype(subtile_path, \"" + dtype + "\");\n"
                        stmt += "\n"

                    stmt += "    " * (level + 2) + "}\n"

                    stmt += "    " * (level + 2)
                    stmt += "subtile_paths.push_back(subtile_path);\n"
                    stmt += "\n"

                """ 
                stmt += "    " * (level + 2)
                stmt += "curr_subtile_num1 = ((curr_subtile_num % " + str(unroll_factor)  + ") == 0) ?  curr_subtile_num1 + 1 : curr_subtile_num1;\n"
                if(unroll): 
                    stmt += "    " * (level + 2)
                    stmt += "curr_subtile_num2 = ((curr_subtile_num % " + str(unroll_factor)  + ") == 1) ?  curr_subtile_num2 + 1 : curr_subtile_num2;\n"  
                """    
                stmt += "    " * (level + 2)
                stmt += "curr_subtile_num++;\n"    

                if(gcheck):                                  
                    stmt += "    " * (level + 2)
                    stmt += "output_gold_file.close();"   
    
        return [stmt]

def cg_op_stmt(op_list, sub_point, id_dict, id_dict_true, level, curr_id, expr, dest, split_dict, scalar, dtype, nnz_ctr):

        stmt = ""
    
        valid_op_list = [] 
        invalid_op_list = []
        
        for op in op_list: 
            if not (curr_id in id_dict[op]): 
                if(id_dict[op] != ['-']):
                    valid_op_list.append(op)
                
        for id in sub_point:
            arr_read = id[1]
            arr_idx  = id[0]
            if(arr_idx in id_dict[arr_read]):
                if(id_dict[arr_read][-1] == arr_idx):
                    valid_op_list.append(arr_read)
    
        valid_op_list = [x for x in op_list if x in valid_op_list]

        temp_id_dict = {}   

        for op in valid_op_list:
            temp_id_dict[op] = id_dict_true[op]
        
        for op in op_list:
            if op not in valid_op_list: 
                temp_id_dict[op] = ['-']

        op_stmt, op_cnt = get_stmt(expr_to_stmt(expr), temp_id_dict, dtype)

        for keys in dest.keys():
            dest_read = keys

        if(scalar != 1):
            stmt += "    " * (level + 2)
            stmt += "p" + dest_read + " = "
            cprod = 1
            for id in dest[dest_read][::-1]:
                stmt += " + " + id + " * " + str(cprod)
                cprod *= split_dict[id][1]

        stmt += ";"
        stmt += "\n"
        if(nnz_ctr):
            stmt += "    " * (level + 2)
            stmt += "int cnt = count(out_nnz_id.begin(), out_nnz_id.end(), p" + dest_read + ");\n"
            stmt += "    " * (level + 2)
            stmt += "if(cnt == 0) out_nnz_id.push_back(p" + dest_read + ");"
            stmt += "\n"

        if(dtype == "bf16"):
            if (scalar != 1):
                stmt += "    " * (level + 2) + dest_read + "_vals[p" + dest_read + "] = bf16_add(" + dest_read + "_vals[p" + dest_read + "], " + op_stmt + ");"
            else:
                stmt += "    " * (level + 2) + dest_read + "vals[0] = bf16_add(" + dest_read + "_vals[0], " + op_stmt + ");"
        else:
            if(scalar != 1):
                stmt += "    " * (level + 2) + dest_read + "_vals[p" + dest_read + "] += " + op_stmt + ";"    
            else: 
                stmt += "    " * (level + 2) + dest_read + "_vals[0] += " + op_stmt + ";"   
        stmt += "\n"
        stmt += "    " * (level + 2) + "op_cnt += " + str(op_cnt + 1) + ";\n"
  
        return [stmt]

def lower(stmt, id_dict, id_dict_true, op_list, schedule, level, target, split_dict, dest, mode, next_id_dict, next_id_map, scalar, workspace, process_csf, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict):
    
    curr_id = schedule[0]
    stmt_list = []
    lattice = expr_to_lattice(stmt, id_dict, curr_id)

    # initialize sparse pos variables
    stmt_list.append(pos_read(curr_id, op_list, id_dict, level))

    for point in lattice:

        # while all merged dimensions have more values
        stmt_list.append(while_stmt_open(point, id_dict, level))

        # initialize sparse idx variables
        stmt_list.append(id_init(point, id_dict, level))

        # merge sparse idx variables
        stmt_list.append(id_merge(point, id_dict, level))
        
        # one case per sub-lattice point
        sub_points = get_sub_lattice(point, lattice) 

        loop_counter = 0
        for sub_point in sub_points:
            if(loop_counter == 0):    
                stmt_list.append(if_stmt_open(sub_point, id_dict, level))
            else:
                stmt_list.append(elif_stmt_open(sub_point, id_dict, level))
            sub_point_id_dict = get_sub_point_dict(sub_point, id_dict, op_list)
            sub_point_schedule = get_sub_point_schedule(sub_point, schedule)     
 
            if(target == "ap"):
                stmt_list.append(ap_mem_stmt(sub_point, id_dict, level, curr_id))
            elif(target == "cp"):
                stmt_list.append(cp_mem_stmt(op_list, sub_point, id_dict, level, curr_id, split_dict, mode, process_csf))

            if(len(schedule) == 1):
                if(target == "ap"):
                    stmt_list.append(ap_op_stmt(op_list, sub_point, id_dict, id_dict_true, level, curr_id, dest, split_dict, mode, workspace))
                elif(target == "cp"):
                    stmt_list.append(cp_op_stmt(op_list, sub_point, id_dict, id_dict_true, level, curr_id, mode, split_dict, next_id_dict, dest, next_id_map, workspace, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict))
                elif(target == "cg"):
                    stmt_list.append(cg_op_stmt(op_list, sub_point, id_dict, id_dict_true, level, curr_id, stmt, dest, split_dict, scalar, dtype, nnz_ctr))
            else:     
                stmt_list.extend(lower(stmt, sub_point_id_dict, id_dict_true, op_list, sub_point_schedule, level + 2, target, split_dict, dest, mode, next_id_dict, next_id_map, scalar, workspace, process_csf, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict))
            stmt_list.append(if_stmt_close(sub_point, id_dict, level))
            loop_counter += 1
        
        # increment sparse idx variables
        stmt_list.append(id_increment(point, id_dict, level))
        
        stmt_list.append(while_stmt_close(point, id_dict, level))   

    return stmt_list

def workspace_declaration(split_factor, dest_id, scalar):
    # calcualate the number of subtiles that constitute the next level tile
    # this determines the number of slots in the workspace
    n_subtiles = 0
    for name, id in dest_id.items():
        for i in id:
            if(scalar != 1): 
                if n_subtiles == 0:
                    n_subtiles = math.ceil(split_factor[i][0] / split_factor[i][1])
                else: 
                    n_subtiles *= math.ceil(split_factor[i][0] / split_factor[i][1])
            else:
                n_subtiles = 1
    return "    std::vector<std::vector<float *>>subtile_workspace(" + str(int(n_subtiles)) + " , std::vector<float *>());\n"

def workspace_reduction(split_factor, target, dest_id, scalar):
    # allcoate the array that is going to store the recombined tile
    # determine the size of the tile first
    stmt = []
    output_tile_size = 0
    dest_name = None
    for name, id in dest_id.items():
        dest_name = name
        for i in id:
            if(scalar != 1): 
                if output_tile_size == 0:
                    output_tile_size = split_factor[i][0]
                else:
                    output_tile_size *= split_factor[i][0]
            else:
                output_tile_size = 1
    stmt.append("    float* " + dest_name + "_vals = (float*)malloc(sizeof(float) * " + str(output_tile_size) + ");\n")
    stmt.append("\n")
    # initialize the recombined tile to zero 
    stmt.append("    for (int p" + dest_name + " = 0; p" + dest_name + " < " + str(output_tile_size) + "; " + "p" + dest_name + " ++) {\n")
    stmt.append("        " + dest_name + "_vals[p" + dest_name + "] = 0;\n")
    stmt.append("    }\n")
    stmt.append("\n")

    if(scalar == 1):
        stmt.append("    " + "for (int i = 0; i < subtile_workspace.size(); i++) {")
        stmt.append("        " + "for (int j = 0; j < subtile_workspace[i].size(); j++) {")
        stmt.append("            " + dest_name + "_vals[0] += subtile_workspace[i][j][0];")
        stmt.append("        " + "}")
        stmt.append("    " + "}")
        return stmt 
    
    level = 1
    dim_n_subtile = {}
    subtile_size = {}
    tile_size = {}
    for id in dest_id[dest_name]:
        dim_n_subtile[id] = int(math.ceil(split_factor[id][0] / split_factor[id][1]))
        loop_index = "subtile_" + id
        stmt.append(("    " * level) + "for (int " + loop_index + "= 0; " + loop_index + " < " + str(dim_n_subtile[id]) + "; " + loop_index + " ++) {\n")
        level = level + 1
    for id in dest_id[dest_name]:
        subtile_size[id] = split_factor[id][1]
        tile_size[id] = split_factor[id][0]
        stmt.append(("    " * level) + "int base_" + id + " = " + "subtile_" + id + " * " + str(subtile_size[id]) + ";\n")
    workspace_index_str = ""
    workspace_index_str += "subtile_" + dest_id[dest_name][0]
    for dim_count, id in enumerate(dest_id[dest_name][1:]):
        for i in range(dim_count + 1, len(dest_id[dest_name])):
            offset_id = dest_id[dest_name][i]
            workspace_index_str += " * " + str(dim_n_subtile[offset_id])
        workspace_index_str += " +  subtile_" + id
    stmt.append(("    " * level) + "for (std::vector<float*>::iterator it = subtile_workspace[" + workspace_index_str + "].begin(); it != subtile_workspace[" + workspace_index_str + "].end(); it++) {\n")
    level = level + 1
    for id in dest_id[dest_name]:
        stmt.append(("    " * level) + "for (int " + id + " = 0; "  + id + " < " + str(subtile_size[id]) + "; " + id + " ++) {\n")
        level = level + 1
    
    # generate the index that store the reduced value in to A_Vals
    output_index_str = ""
    output_index_str += "(base_" + dest_id[dest_name][0] + " + " +  dest_id[dest_name][0] + ")"
    for dim_count, id in enumerate(dest_id[dest_name][1:]):
        for i in range(dim_count + 1, len(dest_id[dest_name])):
            offset_id = dest_id[dest_name][i]
            output_index_str += " * " + str(tile_size[offset_id])
        output_index_str += " + (base_" + id + " + " + id + ")"

    # generate the index that is used to access the partial product in the workspace
    partial_index_str = ""
    partial_index_str += dest_id[dest_name][0]
    for dim_count, id in enumerate(dest_id[dest_name][1:]):
        for i in range(dim_count + 1, len(dest_id[dest_name])):
            offset_id = dest_id[dest_name][i]
            partial_index_str += " * " + str(subtile_size[offset_id])
        partial_index_str += " + " + id
    # For ap, the tile size may not perfectly align with the actual output tensor size
    # Need to put guard here so padded values in the tiles are not written to the output matrix
    if target == "ap" or "cp":
        stmt.append("    " * level + "if (" + output_index_str + " < " + str(output_tile_size) + ")\n")
        level = level + 1
    stmt.append(("    " * level) + dest_name + "_vals[" + output_index_str + "] += (*it)[" + partial_index_str + "];\n")
    if target == "ap":
        level = level - 1
    # close the subtile partial product loop
    for id in dest_id[dest_name]:
        level = level - 1
        stmt.append(("    " * level + "}\n"))
    stmt.append(("    " * level) + "free(*it);\n")
    # close the iterator loop
    level = level - 1
    stmt.append(("    " * level + "}\n"))

    # close the workspace loop
    for id in dest_id[dest_name]:
        level = level - 1
        stmt.append(("    " * level + "}\n"))

    return stmt


    """
    if __name__ == '__main__':

        stmt = "(B * C)"
        id_dict = {}

        id_dict['B'] = ['i', 'k']
        id_dict['C'] = ['j', 'k']

        op_list = ['B', 'C']

        schedule = ['i', 'j', 'k']

        split_dict = {}
        split_dict['i'] = [240, 30]
        split_dict['j'] = [240, 30]
        split_dict['k'] = [240, 30]

        for element in lower(stmt, id_dict, id_dict, op_list, schedule, 0, "cp", split_dict): 
            if element != [""]:
                print(element[0])
    """
    
    """

    stmt = "((B + C) + D)"
    id_dict = {}

    id_dict['B'] = ['i', 'k']
    id_dict['C'] = ['j', 'k']

    op_list = ['B', 'C']

    schedule = ['i', 'j', 'k']

    for element in lower(stmt, id_dict, op_list, schedule, 0): 
        if element != [""]:
            print(element[0])
    """