import codegen

def einsum_expr(sub_stmt, op_list, op_dict, dest_dict):

    sub_op_list = []
    for char in sub_stmt: 
        if(char in op_list):
            sub_op_list.append(char)

    if(len(sub_op_list) > 1):
        stmt = []
        stmt.extend("np.einsum('")

        for char in sub_op_list:
            stmt.extend("".join(op_dict[char]))
            stmt.extend(",")
        stmt = stmt[:-1]

        

        dest_keys = list(dest_dict.keys())
        dest_list = dest_dict[dest_keys[0]]

        if(dest_list != ['0']):
            stmt.extend("->")
            stmt.extend("".join(dest_list))

        stmt.extend("'")
        stmt.extend(",")

        for char in sub_op_list:
            stmt.extend(char)
            stmt.extend(",")

        stmt = stmt[:-1]
        stmt.extend(")")
        stmt = "".join(stmt)
    else:
        stmt = sub_op_list[0]

    return stmt


def dense(expr, op_list, op_dict, dest_dict, output_dir_path):
    
    stmt = []
    stmt.append("import numpy as np")
    stmt.append("\n")

    for op in op_list:
        stmt.append("\n")
        stmt.append(op + " = np.load(\"" + output_dir_path + "tensor_" + op + "/numpy_array.npz\")['array1']")

    stmt.append("\n")
    stmt.append("\n")

    if("+" in expr):
        sub_stmts = expr.split("+")
    else:
        sub_stmts = [expr]

    sub_stmt1 = sub_stmts[0]

    np_einsum_expr = einsum_expr(sub_stmt1, op_list, op_dict, dest_dict)
    stmt.append("out = " + np_einsum_expr)

    for sub_stmt in sub_stmts[1:]:
        stmt.append("\n")
        stmt.append("temp = " + einsum_expr(sub_stmt, op_list, op_dict, dest_dict))
        stmt.append("\n")
        stmt.append("out = np.add(out, temp)")  
        
    stmt.append("\n")
    stmt.append("\n")

    stmt.append("out = out.reshape(-1)") 
    stmt.append("\n")
    stmt.append("out_path = \"" + output_dir_path + "gold_output.npz\"")
    stmt.append("\n")
    stmt.append("np.savez(out_path, array1 = out)")
    stmt.append("\n")

    return stmt


def gold_tensor_declerations(op_list, output_dir_path):
    stmt = []
    stmt.append("import numpy as np")
    stmt.append("\n")

    for op in op_list:
        stmt.append("\n")
        stmt.append(op + " = np.load(\"" + output_dir_path + "tensor_" + op + "/numpy_array.npz\")['array1']")

    return stmt

def gold_tensor_decleration(gold_file, op_dict, dest_dict, split_factor, scalar):

    for key, value in op_dict.items(): 
        tensor_dim = len(value)
        gold_file.write("\n")

        for i in range(0, tensor_dim): 
            gold_file.write("    " + "std::vector<int> " + key + str(i + 1) + "_pos"  + ";\n")
            gold_file.write("    " + "std::vector<int> " + key + str(i + 1) + "_crd"  + ";\n")
        
        gold_file.write("    " + "std::vector<float> " + key + "_vals;\n")
        gold_file.write("\n")

        for i in range(0, tensor_dim): 
            gold_file.write("    " + "build_vec(" + key + str(i + 1) +  "_pos, " + "\"lego_scratch/tensor_" + key + "/csf_pos" + str(i + 1) + ".txt\");\n")
            gold_file.write("    " + "build_vec(" + key + str(i + 1) +  "_crd, " + "\"lego_scratch/tensor_" + key + "/csf_crd" + str(i + 1) + ".txt\");\n")

        gold_file.write("    " + "build_vec_val(" + key + "_vals, " + "\"lego_scratch/tensor_" + key + "/csf_vals.txt\");\n")
        gold_file.write("\n")

    outsize = 1
    for key, value in dest_dict.items():
        if(scalar != 1):
            for id in value: 
                outsize *= int(split_factor[id][1])
        else:
            outsize = 1
        
        gold_file.write("    " + "int output_size = " + str(outsize) + ";\n")
        gold_file.write("\n")

        gold_file.write("    " + "float *" + key + "_vals = (float*)malloc(sizeof(float) * output_size);\n")
        gold_file.write("\n")

        gold_file.write("    " + "for (int p" + key + " = 0; p" + key + " < output_size; p" + key + "++) {\n")
        gold_file.write("        " + key + "_vals[p" + key + "] = 0;\n")
        gold_file.write("    }\n")

        gold_file.write("\n")
        gold_file.write("    " + "int p" + key + ";\n")
    
    return outsize

def custom_sort(list1, list2):
    # Create a set for quick lookup of elements in list2
    list2_set = set(list2)
    # Separate elements that are in list2 and those that are not
    not_in_list2 = [x for x in list1 if x not in list2_set]
    # Create a sorted list by maintaining order from list2 first and then the rest
    sorted_list1 = not_in_list2[:1] + list2 + not_in_list2[1:]
    return sorted_list1

def get_schedule(op_dict):
    schedule = []
    for key, value in op_dict.items():
        for element in value: 
            if element not in schedule:
                schedule.append(element)

    for key, value in op_dict.items():
        new_schedule = custom_sort(schedule, value)

    while(schedule != new_schedule):
        schedule = new_schedule
        for key, value in op_dict.items():
            new_schedule = custom_sort(schedule, value)

    return schedule

def get_op_map(op_dict):
    op_map = {}
    for key, value in op_dict.items():
        op_map[key] = []
        for element in value:
            op_map[key].append(value.index(element))

    return op_map

def get_split_factor(split_dict):
    split_factor = {}
    for key, value in split_dict.items():
        split_factor[key] = [0, split_dict[key][0]]
    
    return split_factor


def sparse(expr, op_list, op_dict, dest_dict, split_dict, output_dir_path, scalar, workspace):
   
    schedule = get_schedule(op_dict)
    op_map = get_op_map(op_dict)
    split_factor = get_split_factor(split_dict)
    gold_file = open("gold.cpp", "w+")

    gold_file.write("#include <stdlib.h>\n")   
    gold_file.write("#include <stdio.h>\n")
    gold_file.write("#include <cstring>\n")
    gold_file.write("#include <iostream>\n")
    gold_file.write("#include <fstream>\n")
    gold_file.write("#include <vector>\n")
    gold_file.write("#include <string>\n")
    gold_file.write("#include <sys/types.h>\n")
    gold_file.write("#include <sys/stat.h>\n")
    gold_file.write("using namespace std;\n")
    gold_file.write("\n")
    gold_file.write("#include \"src/data_parser.h\"")
    gold_file.write("\n")
    gold_file.write("#include \"src/mem_op.h\"")
    gold_file.write("\n")
    gold_file.write("\n")

    gold_file.write("int main() {\n")
    gold_file.write("\n")
    outsize = gold_tensor_decleration(gold_file, op_dict, dest_dict, split_factor, scalar)
    gold_file.write("\n")
    
    for element in codegen.lower(expr, op_dict, op_dict, op_list, schedule, 1, "cg", split_factor, dest_dict, "rtl", op_dict, op_map, scalar, workspace, False, 0,  False, False, 0):
        if element != [""]:
            gold_file.write(element[0])
            gold_file.write("\n")

    for key in dest_dict.keys():
        dest = key

    gold_file.write("\n")  
    gold_file.write("    std::string output_path = \"lego_scratch/gold_output.txt\";")
    gold_file.write("\n")
    gold_file.write("    std::ofstream output_file;")
    gold_file.write("\n")
    gold_file.write("    output_file.open(output_path, std::ios::app);")
    gold_file.write("\n")
    gold_file.write("    rtl_output_subtile_printer(" + dest + "_vals, " + str(outsize) + ", 0, output_file);")
    gold_file.write("\n")
    gold_file.write("    output_file.close();")
    gold_file.write("\n")
    gold_file.write("\n")
    gold_file.write("    return 0;")
    gold_file.write("\n")
    gold_file.write("}\n")
    gold_file.close()



if __name__ == "__main__":
    expr = "(B * C)"
    op_list = ["B", "C"]
    op_dict = {"B": ['i', 'k'], "C": ['k', 'j']}
    dest_dict = {"A": ['i', 'j']}

    split_dict = {"i": [20, 10, 5], "k": [12, 6, 3], "j": [30, 15, 5]}
    output_dir_path = "lego_scratch/"

    sparse(expr, op_list, op_dict, dest_dict, split_dict, output_dir_path, 0)
