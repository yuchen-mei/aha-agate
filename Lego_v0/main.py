import pre_process
import codegen
import sys
import argparse
import einsum
import gold_cgen
import shutil
import os
import copy
import math

from onyx_codegen.meta import *
from onyx_codegen.main_codegen import *
from onyx_codegen.io_placement import *
from onyx_codegen.raw_to_h_16 import *
from onyx_codegen.bs_to_h import *
from onyx_codegen.generate_linker import *
from onyx_codegen.generate_reg_write import *



sys.path.insert(0, './')
sys.path.insert(0, './sam')

from pyparsing import Word, alphas, one_of, alphanums, OneOrMore, Suppress

def tensor_path_type_dict(tensor_path_input):

    tensor_path_dict = {}
    tensor_type_dict = {}
    tensor_transpose_dict = {}
    tensor_format_dict = {}
    tensor_density_dict = {} 
    tensor_dtype_dict = {}

    tensor_path_dict_keys = [] 

    with open(tensor_path_input, 'r') as f:
        data = f.read().splitlines()    
    
    data = [i for i in data]
    data = [i.replace(" ", "") for i in data]


    data = [i for i in data]
    data = [i.replace(" ", "") for i in data]

    for i in range(0, len(data)):
        parsed_data = data[i].split(":")
        tensor_type_dict[parsed_data[0]] = parsed_data[1]
        tensor_path_dict[parsed_data[0]] = parsed_data[2]   
        tensor_format_dict[parsed_data[0]] = parsed_data[3]
        tensor_transpose_dict[parsed_data[0]] = parsed_data[4]
        tensor_density_dict[parsed_data[0]] = float(parsed_data[5])
        tensor_dtype_dict[parsed_data[0]] = parsed_data[6]

    return tensor_path_dict, tensor_type_dict, tensor_format_dict, tensor_transpose_dict, tensor_density_dict, tensor_dtype_dict

def data_parser(data):

    data = [i.replace(" ", "") for i in data]

    stmt = data[0].split(":")
    app_name = stmt[1]

    data = data[1:]

    stmt = data[0].split(":")
    stmt = stmt[1]

    arith_op = one_of("+ - * /")

    parsed_stmt = einsum.parser.parse(stmt)
    expr = einsum.build_expr(parsed_stmt)
    dest, op = einsum.build_dict(parsed_stmt, 1, {}, {})
    op_list = list(op.keys()) 

    schedule_rule = Word(alphanums) + "_" + Word(alphanums) + ':' + '[' + Word(alphas) + ']'

    schedule_1 = list((schedule_rule.parseString(data[1]))[5])
    schedule_2 = list((schedule_rule.parseString(data[2]))[5])
    schedule_3 = list((schedule_rule.parseString(data[3]))[5])

    num_ids = len(schedule_1)

    split_factor_rule = Word(alphas) + ':split:' + Word(alphanums) + ':' + Word(alphanums) + ':' + Word(alphanums)

    split_factor = {}

    for i in range(num_ids):
        parsed_split = split_factor_rule.parseString(data[4 + i])
        split_factor[parsed_split[0]] = [int(parsed_split[2]), int(parsed_split[4]), int(parsed_split[6])]

    activation_rule = "activation_" + Word(alphas) + ":" + OneOrMore(Word(alphas) + Suppress("+") | Word(alphas))
    activation = {}
    activation["ap"] = []
    activation["cp"] = []
    activation["cg"] = []

    activation["ap"].extend(list(activation_rule.parseString(data[4 + num_ids]))[3:])
    activation["cp"].extend(list(activation_rule.parseString(data[5 + num_ids]))[3:])
    activation["cg"].extend(list(activation_rule.parseString(data[6 + num_ids]))[3:])

    return app_name, dest, op, op_list, schedule_1, schedule_2, schedule_3, split_factor, expr, activation

def parse(input_file, level):

    with open(input_file, 'r') as f:
        data = f.read().splitlines()
    app_name, dest, op, op_list, schedule_1, schedule_2, schedule_3, split_factor, expr, activation = data_parser(data)

    expr = expr.split("=")
    expr = expr[1]

    if(level == "ap"): 
        schedule = schedule_1
        for id in split_factor:
            split_factor[id].pop()
    elif(level == "cp"):
        schedule = schedule_2
        for id in split_factor:
            split_factor[id].pop(0)
    else:
        schedule = schedule_3
        for id in split_factor:
            split_factor[id].pop(0)

    activation = activation[level]

    dest_id = {}
    dest_map = {}

    source_id = {}
    source_map = {}

    for tensor in op:
        source_id[tensor] = []
        source_map[tensor] = []

    for tensor in dest:
        dest_id[tensor] = []
        dest_map[tensor] = []

    for tensor in op:
        for id in schedule: 
            if id in op[tensor]:
                source_id[tensor].append(id)
                source_map[tensor].append(op[tensor].index(id)) 
    
    for tensor in op:
        for id in op[tensor]: 
            if(id == '0'): 
                source_id[tensor].append(id)
    

    for tensor in dest:
        for id in dest[tensor]: 
            if(id == '0'): 
                scalar = 1
            else: 
                scalar = 0

    if(scalar != 1):
        for tensor in dest:
            for id in schedule:
                if id in dest[tensor]:
                    dest_id[tensor].append(id)
                    dest_map[tensor].append(dest[tensor].index(id))
    else: 
        dest_id = dest
    
    return app_name, dest, op, dest_id, dest_map, source_id, source_map, expr, split_factor, op_list, schedule, scalar, activation

def parse_lut_tensor(activation_list):
    lut_tensor = []
    lut_mapping = {
        "exp": "exp",
        "elu": "exp",
        "recip": "recip",
    }
    for activation in activation_list:
        if activation in lut_mapping:
            lut_tensor.append(lut_mapping[activation])
    return lut_tensor

def ap_tensor_decleration(main_file, ap_source_id):

    for key, value in ap_source_id.items():

        if value[0] == '0':
            tensor_dim = 0
        else:
            tensor_dim = len(value)

        main_file.write("\n")

        for i in range(0, 3 * tensor_dim):
            main_file.write("    " + "std::vector<int> " + key + str(i + 1) + "_pos"  + ";\n")
            main_file.write("    " + "std::vector<int> " + key + str(i + 1) + "_crd"  + ";\n")

        main_file.write("    " + "std::vector<float> " + key + "_vals;\n")

        main_file.write("\n")

        for i in range(0, 3 * tensor_dim):
            main_file.write("    " + "build_vec(" + key + str(i + 1) +  "_pos, " + "\"lego_scratch/tensor_" + key + "/tcsf_pos" + str(i + 1) + ".txt\");\n")
            main_file.write("    " + "build_vec(" + key + str(i + 1) +  "_crd, " + "\"lego_scratch/tensor_" + key + "/tcsf_crd" + str(i + 1) + ".txt\");\n")

        main_file.write("    " + "build_vec_val(" + key + "_vals, " + "\"lego_scratch/tensor_" + key + "/tcsf_vals.txt\");\n")
        
        main_file.write("\n")

        main_file.write("    " + "int **tensor_" + key + ";\n")
        main_file.write("    " + "tensor_" + key + " = (int**)malloc(sizeof(int*) * (" + str(6 * tensor_dim + 1) + "));\n")

        main_file.write("\n")

        for i in range(0, 3 * tensor_dim):
            main_file.write("    " + "tensor_" + key + "[" + str(2 * i) + "] = " + key + str(i + 1) + "_pos.data();\n")
            main_file.write("    " + "tensor_" + key + "[" + str(2 * i + 1) + "] = " + key + str(i + 1) + "_crd.data();\n")

        main_file.write("    " + "tensor_" + key + "[" + str(6 * tensor_dim) + "] = (int *)" + key + "_vals.data();\n")
    
        main_file.write("\n")

        main_file.write("    " + "tile" + str(tensor_dim) + " tile_" + key + ";\n"); 
        if tensor_dim == 0:
            main_file.write("    " + "tile_" + key + " = tensor_mem_op_0(tensor_" + key + ");\n")

    main_file.write("\n")  
    main_file.write("    " + "std::string tile_name;")
    main_file.write("\n")


def cp_tensor_decleration(main_file, cp_source_id, split_dict, mode, output_dir, kernel_name, unroll, gcheck, ap_gcheck):

    for key, value in cp_source_id.items():

        if value[0] == '0':
            tensor_dim = 0
        else:
            tensor_dim = len(value)

        main_file.write("\n")

        for i in range(0, 2 * tensor_dim):
            main_file.write("    " + "int *" + key + str(i + 1) + "_pos = tile_" + key + ".pos" + str(i + 1) + ".data();\n")
            main_file.write("    " + "int *" + key + str(i + 1) + "_crd = tile_" + key + ".crd" + str(i + 1) + ".data();\n")

        main_file.write("    " + "float *" + key + "_vals = tile_" + key + ".vals.data();" + "\n")
        main_file.write("\n")

        main_file.write("    " + "subtile" + str(tensor_dim) + " subtile_" + key + ";\n")

        if tensor_dim == 0:
            main_file.write("    " + "subtile_" + key + " = tile_mem_op_0(tile_" + key + ");\n")

        main_file.write("\n")

        if(mode == 'onyx' or mode == 'opal'):

            total_size = 1
            for id in cp_source_id[key]:
                total_size *= int(math.ceil(split_dict[id][0]/split_dict[id][1]))

            main_file.write("    " + "int store_size_" + key + " = " + str(total_size) + ";\n")
            main_file.write("    " + "int id_store_" + key + ";\n")
            main_file.write("\n")

            main_file.write("    " + "bool *store_" + key + "1 = (bool *) calloc((store_size_" + key + " + 1), sizeof(bool));\n")

            for i in range(0, tensor_dim):
                main_file.write("    " + "int *" + key + "_mode" + str(i) + "_start1 = (int *)malloc((store_size_" + key + " + 1) * sizeof(int));\n")
                main_file.write("    " + "int *" + key + "_mode" + str(i) + "_end1 = (int *)malloc((store_size_" + key + " + 1) * sizeof(int));\n")
            
            main_file.write("    " + "int *" + key + "_mode_vals_start1 = (int *)malloc((store_size_" + key + " + 1) * sizeof(int));\n")
            main_file.write("    " + "int *" + key + "_mode_vals_end1 = (int *)malloc((store_size_" + key + " + 1) * sizeof(int));\n")
        
            main_file.write("\n")
            main_file.write("    " + "int **store_subtile_" + key + "1;\n")
            main_file.write("    " + "store_subtile_" + key + "1 = (int**)malloc(sizeof(int*) * (" + str(2 * tensor_dim + 2) + "));\n")

            for i in range(0, tensor_dim):
                main_file.write("    " + "store_subtile_" + key + "1[" + str(2 * i) + "] = " + key + "_mode" + str(i) + "_start1;\n")
                main_file.write("    " + "store_subtile_" + key + "1[" + str(2 * i + 1) + "] = " + key + "_mode" + str(i) + "_end1;\n")

            main_file.write("    " + "store_subtile_" + key + "1[" + str(2 * tensor_dim) + "] = " + key + "_mode_vals_start1;\n")
            main_file.write("    " + "store_subtile_" + key + "1[" + str(2 * tensor_dim + 1) + "] = " + key + "_mode_vals_end1;\n")

            main_file.write("\n")

            main_file.write("    " + "cg_subtile" + str(tensor_dim) + " cg_subtile_" + key + "1;\n")
            main_file.write("    " + "cg_extents" + str(tensor_dim) + " cg_extents_" + key + "1;\n") 

    main_file.write("\n")

    main_file.write("    " + "int curr_subtile_num = 0;\n")    
    main_file.write("    " + "int curr_subtile_num1 = 0;\n")  
    if(unroll != "0"):
        main_file.write("    " + "int curr_subtile_num2 = 0;\n")  
    main_file.write("    " + "std::string out_dir = \"" + output_dir + "/" + kernel_name + "/\" + curr_tile;\n")
    main_file.write("    " + "const char *data_path = out_dir.c_str();\n")
    main_file.write("\n")

    if(mode == 'onyx' or mode == 'opal'):
        main_file.write("    " + "std::string input_data_path = out_dir + \"/" + app_name + "_input_script.h\";\n")
        main_file.write("    " + "std::ofstream input_data_file;\n")
        main_file.write("\n")
        main_file.write("    " + "std::string input_meta_data_path = out_dir + \"/" + app_name + "_extents.h\";\n")
        main_file.write("    " + "std::ofstream input_meta_data_file;\n")
        main_file.write("\n")
        main_file.write("    " + "std::string num_stile_pairs_path = \"" + output_dir + "/" + kernel_name + "/num_stile_pairs.txt\";\n")
        main_file.write("    " + "std::ofstream num_stile_pairs_file;\n")
        main_file.write("\n")
        main_file.write("    " + "std::string mode_data_len_path = \"" + output_dir + "/" + kernel_name + "/mode_data_len.txt\";\n")
        main_file.write("    " + "std::ofstream mode_data_len_file;\n")
        main_file.write("\n")
        main_file.write("    " + "std::string nnz_check_path = \"" + output_dir + "/" + kernel_name + "/nnz_check.txt\";\n")
        main_file.write("    " + "std::ofstream nnz_check_file;\n")
        main_file.write("    " + "nnz_check_file.open(nnz_check_path, std::ios::app);\n")
        main_file.write("    " + "nnz_check_file << out_dir << \"\\n\";\n")
        main_file.write("\n")

        if not ap_gcheck:
            # if ap_gold_check is not enabled, gold checking is performed on the cp, so the output file is a header
            main_file.write("    " + "std::string output_gold_path = out_dir + \"/" + app_name + "_gold.h\";\n")
        else:
            # perform gold check on the ap, output a stand alone cpp file
            main_file.write("    " + "std::string output_gold_path = out_dir;\n")
        main_file.write("    " + "std::ofstream output_gold_file;\n")
        
        if(ap_gcheck): 
            main_file.write("    " + "std::string gcheck_cpp_path = out_dir + \"/" + app_name + "_gold.cpp\";\n")
            main_file.write("    " + "std::ofstream gcheck_cpp_file;\n")
            main_file.write("\n")

    if(mode == 'rtl'): 
        main_file.write("    std::string output_gold_path = out_dir + \"/" + app_name + "_gold.h\";\n")
        main_file.write("    std::ofstream output_gold_file;\n")
        main_file.write("    std::string subtile_path;\n")

    main_file.write("\n")

def cp_closing_decleration(main_file, cg_source_id, cg_source_map, op_list, mode, dest_id, unroll, glb_tile_offset, gcheck, ap_gcheck, cg_dest_id, cg_dest_map, stile_outsize, scalar, mapping_dict=None, lut_tensor=None):

    for key, value in dest_id.items(): 
        dest_read = key   

    if(dest_id[dest_read][0] == '0'):
        out_tensor_dim = 0
    else:
        out_tensor_dim = len(dest_id[dest_read])

    if(mode == 'onyx' or mode == 'opal'):
        main_file.write("\n")
        stmt = "    "
        stmt += "if(curr_subtile_num > 0) {" 
        main_file.write(stmt + "\n")

        main_file.write("\n")
        main_file.write("        " + "input_data_file.open(input_data_path);\n")
        main_file.write("        " + "input_meta_data_file.open(input_meta_data_path);\n")
        main_file.write("\n")
        main_file.write("        " + "num_stile_pairs_file.open(num_stile_pairs_path, std::ios::app);\n")
        main_file.write("\n")
        main_file.write("        " + "mode_data_len_file.open(mode_data_len_path, std::ios::app);\n")
        main_file.write("\n")

        if(ap_gcheck):

            main_file.write("        " + "gcheck_cpp_file.open(gcheck_cpp_path, std::ios::app);\n")
            main_file.write("        " + "int output_subtile_size = " + str(stile_outsize) + ";\n")

            stmt = ""
            if(scalar != 1):
                for key in cg_dest_id.keys():
                    out_id_list = cg_dest_id[key]
                    out_id_map = cg_dest_map[key]
                for i in range(0, len(out_id_list)):
                    stmt += "        header_subtile_dim_decl(gcheck_cpp_file, " + str(out_id_map[i]) + ", " + str(cg_split_factor[out_id_list[i]][1]) + ");\n"
                
            stmt += "        header_check_gold(gcheck_cpp_file, output_subtile_size, true);\n"
            stmt += "\n"
            main_file.write(stmt)

        if(unroll == "1"):
            main_file.write("\n")
            main_file.write("        " + "std::vector<int> nnz_in;\n")
            main_file.write("        " + "for(int i = 0; i < curr_subtile_num; i++){\n")
            main_file.write("        " + "    nnz_in.push_back(0);\n")
            for key, value in cg_source_id.items():
                main_file.write("        " + "    nnz_in[i] += (cg_extents_" + key + "1.extents_mode_vals[2 * i + 1] - cg_extents_" + key + "1.extents_mode_vals[2 * i]);\n")
            main_file.write("        " + "}\n")
            main_file.write("        " + "auto [map1, map2] = partition_vec(nnz_in);\n")
            main_file.write("        " + "curr_subtile_num1 = map1.size();\n")
            main_file.write("        " + "curr_subtile_num2 = map2.size();\n")
            main_file.write("\n")
        elif(unroll == "2"):
            main_file.write("\n")
            main_file.write("        " + "auto map1 = generate_range(curr_subtile_num);\n")
            main_file.write("        " + "curr_subtile_num1 = curr_subtile_num;\n")
            main_file.write("        " + "curr_subtile_num2 = curr_subtile_num;\n")
            main_file.write("\n")
        else:
            main_file.write("\n")
            main_file.write("        " + "curr_subtile_num1 = curr_subtile_num;\n")
            main_file.write("        " + "auto map1 = generate_range(curr_subtile_num);\n")
            main_file.write("\n")
        
        main_file.write("        " + "header_meta_data(input_meta_data_file, \"\", curr_subtile_num1);\n")
        main_file.write("\n")
        main_file.write("        " + "num_stile_pairs_file << curr_subtile_num1;\n")
        main_file.write("\n")

        
        main_file.write("        " + "if(curr_subtile_num1 > 0){")
        main_file.write("\n")

        for key, value in cg_source_id.items():
            tensor_dim = len(value)
            # TODO: Introduce systematic change to replace this hack
            # this hack is to cope with the old RTL bitstream generation that 
            # always place the matrix modes in the data flow order 
            # e.g. for X(i,j) = B(i, k) * C(k, j), C_mode_0 is k and C_mode_1 is j
            # however, for RTL, C_mode_0 is mapped to j and C_mode_1 is mapped to k
            cg_source_map_cpy = copy.deepcopy(cg_source_map)
            for tensor_name, mode_list in cg_source_map_cpy.items():
                mode_list.sort()
            for i in range(0, tensor_dim):
                main_file.write("            " + "mode_data_printer(input_data_file, \"" + key + "\", \"" + str(cg_source_map_cpy[key][i]) + "\", cg_subtile_" + key + "1.mode_" + str(i) + ");\n")
                main_file.write("            " + "extent_data_printer(input_meta_data_file, \"" + key + "\", \"" + str(cg_source_map_cpy[key][i]) + "\", cg_extents_" + key + "1.extents_mode_" + str(i) + ", map1);\n")
                main_file.write("            " + "mode_data_len_file << " + "cg_subtile_" + key + "1.mode_" + str(i) + ".size() << \"\\n\";\n")
                main_file.write("\n")

            main_file.write("            " + "val_data_printer(input_data_file, \"" + key + "\", \"vals\", cg_subtile_" + key + "1.mode_vals, \"" + dtype + "\");\n")
            main_file.write("            " + "extent_data_printer(input_meta_data_file, \"" + key + "\", \"vals\", cg_extents_" + key + "1.extents_mode_vals, map1);\n")
            main_file.write("            " + "mode_data_len_file << " + "cg_subtile_" + key + "1.mode_vals.size() << \"\\n\";\n")
            main_file.write("\n")

        main_file.write("        " + "}")
        main_file.write("\n")

        if(unroll != "0"):
            if(unroll == "1"):
                main_file.write("        " + "header_meta_data(input_meta_data_file, \"_unroll\", curr_subtile_num2);\n")
                main_file.write("\n")
                main_file.write("        " + "num_stile_pairs_file << \" \" << curr_subtile_num2;\n")
                main_file.write("\n")
            main_file.write("        " + "if(curr_subtile_num2 > 0){")
            main_file.write("\n")
            for key, value in cg_source_id.items():
                tensor_dim = len(value)
                # TODO: Introduce systematic change to replace this hack
                # this hack is to cope with the old RTL bitstream generation that 
                # always place the matrix modes in the data flow order 
                # e.g. for X(i,j) = B(i, k) * C(k, j), C_mode_0 is k and C_mode_1 is j
                # however, for RTL, C_mode_0 is mapped to j and C_mode_1 is mapped to k
                cg_source_map_cpy = copy.deepcopy(cg_source_map)
                for tensor_name, mode_list in cg_source_map_cpy.items():
                    mode_list.sort()
                for i in range(0, tensor_dim):
                    main_file.write("            " + "mode_data_printer(input_data_file, \"" + key + "\", \"" + str(cg_source_map_cpy[key][i]) + "_unroll\", cg_subtile_" + key + "1.mode_" + str(i) + ");\n")
                    if(unroll == "1"):
                        main_file.write("            " + "extent_data_printer(input_meta_data_file, \"" + key + "\", \"" + str(cg_source_map_cpy[key][i]) + "_unroll\", cg_extents_" + key + "1.extents_mode_" + str(i) + ", map2);\n")
                    main_file.write("            " + "mode_data_len_file << " + "cg_subtile_" + key + "1.mode_" + str(i) + ".size() << \"\\n\";\n")
                    main_file.write("\n")
                main_file.write("            " + "val_data_printer(input_data_file, \"" + key + "\", \"vals_unroll\", cg_subtile_" + key + "1.mode_vals, \"" + dtype + "\");\n")
                if(unroll == "1"):
                    main_file.write("            " + "extent_data_printer(input_meta_data_file, \"" + key + "\", \"vals_unroll\", cg_extents_" + key + "1.extents_mode_vals, map2);\n")
                main_file.write("            " + "mode_data_len_file << " + "cg_subtile_" + key + "1.mode_vals.size() << \"\\n\";\n")
                main_file.write("\n")

            main_file.write("        " + "}")          
            main_file.write("\n")

            if(unroll == "1"):
                main_file.write("        " + "else {")
                main_file.write("\n")
                for key, value in cg_source_id.items():
                    tensor_dim = len(value)
                    # TODO: Introduce systematic change to replace this hack
                    # this hack is to cope with the old RTL bitstream generation that 
                    # always place the matrix modes in the data flow order 
                    # e.g. for X(i,j) = B(i, k) * C(k, j), C_mode_0 is k and C_mode_1 is j
                    # however, for RTL, C_mode_0 is mapped to j and C_mode_1 is mapped to k
                    cg_source_map_cpy = copy.deepcopy(cg_source_map)
                    for tensor_name, mode_list in cg_source_map_cpy.items():
                        mode_list.sort()
                    for i in range(0, tensor_dim):
                        main_file.write("            " + "extent_data_printer(input_meta_data_file, \"" + key + "\", \"" + str(cg_source_map_cpy[key][i]) + "_unroll\", cg_extents_" + key + "1.extents_mode_" + str(i) + ", map1);\n")
                    main_file.write("\n")
                    main_file.write("            " + "extent_data_printer(input_meta_data_file, \"" + key + "\", \"vals_unroll\", cg_extents_" + key + "1.extents_mode_vals, map1);\n")
                    main_file.write("\n")
                main_file.write("        " + "}")          
                main_file.write("\n")

        if lut_tensor is not None:
            for lut in lut_tensor:
                main_file.write("        " + "lut_data_printer(input_data_file, \"" + lut + "\");\n")
                main_file.write("        " + "lut_extent_data_printer(input_meta_data_file, \"" + lut + "\");\n")
                main_file.write("\n")

        main_file.write("        " + "output_gold_file.open(output_gold_path, std::ios_base::app);\n")

        main_file.write("        " + "num_stile_pairs_file << \"\\n\";\n")
        main_file.write("\n")    

        if(gcheck):    
            if(ap_gcheck):
                out_file = "gcheck_cpp_file"
            else:
                out_file = "output_gold_file"

            if(unroll == "1"): 
                main_file.write("        " + "map1.insert(map1.end(), map2.begin(), map2.end());\n")

            if(not ap_gcheck):
                main_file.write("        " + "output_gold_file.open(output_gold_path, std::ios::app);\n")

            if ap_gcheck:
                main_file.write("        " + "codegen_check_gold_head(gcheck_cpp_file, curr_subtile_num, output_subtile_size, " + str(out_tensor_dim) + ", " + str(unroll) +", \"" + glb_bank_offset + "\", \"" + glb_tile_offset + "\", map1, true);\n")
            else:
                main_file.write("        " + "codegen_check_gold_head(output_gold_file, curr_subtile_num, output_subtile_size, " + str(out_tensor_dim) + ", " + str(unroll) +", \"" + glb_bank_offset + "\", \"" + glb_tile_offset + "\", map1, false);\n")

            for i in range(0, out_tensor_dim + 1):
                curr_mapping = mapping_dict[dest_read][i]
                if ap_gcheck:
                    main_file.write("        " + "codegen_check_gold_read_gdb_bin(gcheck_cpp_file, \"" + str(i) + "\", \"" + str(curr_mapping) + "\", \"" + glb_tile_offset + "\", false);\n")
                else:
                    main_file.write("        " + "codegen_check_gold_outmap(output_gold_file, \"" + str(i) + "\", \"" + str(curr_mapping) + "\", \"" + glb_tile_offset + "\");\n")

            if(unroll == "1"):
                main_file.write("        " + "codegen_check_gold_unroll_ifdef_open(" + out_file + ", 1, curr_subtile_num1);\n")
            elif(unroll == "2"):    
                main_file.write("        " + "codegen_check_gold_unroll_ifdef_open(" + out_file + ", 10, 0);\n")
            else: 
                main_file.write("        " + "codegen_check_gold_unroll_ifdef_open(" + out_file + ", 0, 0);\n")

            if ap_gcheck:
                main_file.write("        " + "codegen_check_gold_tail(gcheck_cpp_file, curr_subtile_num, " + str(out_tensor_dim) + ", \"\", true);\n")
            else:
                main_file.write("        " + "codegen_check_gold_tail(output_gold_file, curr_subtile_num, " + str(out_tensor_dim) + ", \"\", false);\n")

            if(unroll != "0"): 
                main_file.write("        " + "codegen_check_gold_unroll_ifdef_open(" + out_file + ", 2, 0);\n")
                for i in range(0, out_tensor_dim + 1):
                    curr_mapping = mapping_dict[dest_read][i] 
                    if ap_gcheck:
                        main_file.write("        " + "codegen_check_gold_read_gdb_bin(gcheck_cpp_file, \"" + str(i) + "\", \"" + str(curr_mapping) + "\", \"" + glb_tile_offset + "\", true);\n")
                    else:
                        main_file.write("        " + "codegen_check_gold_outmap_unroll(output_gold_file, \"" + str(i) + "\", \"" + str(curr_mapping) + "\", \"" + glb_tile_offset + "\");\n")
                if ap_gcheck:
                    main_file.write("        " + "codegen_check_gold_tail(gcheck_cpp_file, curr_subtile_num, " + str(out_tensor_dim) + ", \"_unroll\", true);\n")
                else:
                    main_file.write("        " + "codegen_check_gold_tail(output_gold_file, curr_subtile_num, " + str(out_tensor_dim) + ", \"_unroll\", false);\n")

            if(ap_gcheck):
                main_file.write("        " + "codegen_check_gold_ret(gcheck_cpp_file, true);\n")
                main_file.write("        " + "gcheck_cpp_file.close();\n")
            else:
                main_file.write("        " + "codegen_check_gold_ret(output_gold_file, false);\n")
                main_file.write("        " + "output_gold_file.close();\n")



        main_file.write("        " + "input_data_file.close();\n")
        main_file.write("        " + "input_meta_data_file.close();\n")
        
        main_file.write("    " + "}\n")

def cg_tensor_decleration(main_file, cg_source_id, split_factor, cg_dest_id, scalar, nnz_ctr): 

    for key, value in cg_source_id.items():

        if value[0] == '0':
            tensor_dim = 0
        else:
            tensor_dim = len(value)

        main_file.write("\n")
        
        for i in range(0, tensor_dim):
            main_file.write("    " + "int *" + key + str(i + 1) + "_pos = subtile_" + key + ".pos" + str(i + 1) + ".data();\n")
            main_file.write("    " + "int *" + key + str(i + 1) + "_crd = subtile_" + key + ".crd" + str(i + 1) + ".data();\n")

        main_file.write("    " + "float *" + key + "_vals = subtile_" + key + ".vals.data();" + "\n")
        if(nnz_ctr): 
            main_file.write("    nnz_file << subtile_" + key + ".vals.size();\n")
            main_file.write("    nnz_file << \"\\n\";\n")

        main_file.write("\n")

    outsize = 1

    if(nnz_ctr): 
        main_file.write("    std::vector<int> out_nnz_id;\n")

    for key, value in cg_dest_id.items():
        if(scalar != 1):
            for id in value:
                outsize *= int(split_factor[id][1])
        else: 
            outsize = 1
    
        main_file.write("    " + "int output_subtile_size = " + str(outsize) + ";\n")
        main_file.write("    " + "int op_cnt = 0;\n")
        main_file.write("\n")

        main_file.write("    " + "float *" + key + "_vals = (float*)malloc(sizeof(float) * output_subtile_size);\n")
        main_file.write("\n")

        main_file.write("    " + "for (int p" + key + " = 0; p" + key + " < output_subtile_size; p" + key + "++) {\n")
        main_file.write("        " + key + "_vals[p" + key + "] = 0;\n")
        main_file.write("    }\n")

        main_file.write("\n")
        main_file.write("    " + "int p" + key + ";\n")

    return outsize

def subtile_output_declaration(main_file, dest_id, split_factor, scalar):
    for name, id in dest_id.items():
        dest_name = name
    # declare the vectors 
    for idx, _ in enumerate(dest_id[dest_name]):
        main_file.write("    std::vector<int> " + dest_name + str(idx + 1) + "_pos_vec;\n")
        main_file.write("    std::vector<int> " + dest_name + str(idx + 1) + "_crd_vec;\n")
    main_file.write("    std::vector<float> " + dest_name + "_vals_vec;\n")

    main_file.write("\n")

    # build the vectors to store the results from the output file of comal/rtl
    for idx, _ in enumerate(dest_id[dest_name]):
        main_file.write("    build_vec(" + dest_name + str(idx + 1) + "_pos_vec, subtile_path + \"/tensor_" + dest_name + "_mode_" + str(idx) + "_seg\");\n")
        main_file.write("    build_vec(" + dest_name + str(idx + 1) + "_crd_vec, subtile_path + \"/tensor_" + dest_name + "_mode_" + str(idx) + "_crd\");\n") 
    main_file.write("    build_vec_val(" + dest_name + "_vals_vec, subtile_path + \"/tensor_" + dest_name + "_mode_vals\");\n")

    main_file.write("\n")

    # get the pointer to the data
    for idx, _ in enumerate(dest_id[dest_name]):
        main_file.write("    int *" + dest_name + str(idx + 1) + "_pos = " + dest_name + str(idx + 1) + "_pos_vec.data();\n")
        main_file.write("    int *" + dest_name + str(idx + 1) + "_crd = " + dest_name + str(idx + 1) + "_crd_vec.data();\n")
    main_file.write("    float *" + dest_name + "_vals = " + dest_name + "_vals_vec.data();\n")

    main_file.write("\n")

    outsize = 1
    for key, value in dest_id.items():

        if(scalar != 1):
            for id in value:
                outsize *= int(split_factor[id][1])
        else:
            outsize = 1
    
        main_file.write("    " + "int output_subtile_size = " + str(outsize) + ";\n")
        main_file.write("    " + "int op_cnt = 0;\n")
        main_file.write("\n")

        main_file.write("    " + "float *" + key + "_output_vals = (float*)malloc(sizeof(float) * output_subtile_size);\n")
        main_file.write("\n")

        main_file.write("    " + "for (int p" + key + " = 0; p" + key + " < output_subtile_size; p" + key + "++) {\n")
        main_file.write("        " + key + "_output_vals[p" + key + "] = 0;\n")
        main_file.write("    }\n")

        main_file.write("\n")
        main_file.write("    " + "if (")
        for idx, _ in enumerate(dest_id[dest_name]):
            if idx != 0:
                main_file.write(" && ")
            main_file.write(f"{dest_name}{idx + 1}_crd_vec.size() == 0")
        main_file.write(") {\n")
        main_file.write(f"        return {dest_name}_output_vals;\n")
        main_file.write("    }\n")
        main_file.write("\n")
        main_file.write("    " + "int p" + key + "_output;\n")

def apply_output_activation(main_file, output_tile_size, activation_function, dest_id):
    supported_activation = ["relu", "leakyrelu", "exp", "elu"]
    for activation in activation_function:
        if activation == "none":
            continue
        if activation not in supported_activation:
            raise NotImplementedError(f"Activation function {activation} is not supported")
        main_file.write("    apply_output_" + activation + "(" + dest + "_vals, " + str(output_tile_size) + ");\n")
    main_file.write("\n")

def apply_input_activation(main_file, input_activation_dict):
    supported_activations = ["relu", "recip"]
    for op, activation in input_activation_dict.items():
        if activation in supported_activations:
            main_file.write(f"    apply_input_{activation}(subtile_{op}.vals);\n")
            main_file.write("\n")
        
def write_output(main_file, ap_split_factor, dest_id, scalar, output_dir, kernel_name):
    output_tile_size = 0
    dest_name = None
    for name, id in dest_id.items():
        dest_name = name
        if(scalar != 1): 
            for i in id:
                if output_tile_size == 0:
                    output_tile_size = ap_split_factor[i][0]
                else:
                    output_tile_size *= ap_split_factor[i][0]
        else:
            output_tile_size = 1

    main_file.write("    std::string output_path = \"" + output_dir + "/" + kernel_name + "/output.txt\";\n")
    main_file.write("    std::ofstream output_file;\n")
    main_file.write("    output_file.open(output_path, std::ios::app);\n")
    main_file.write("    rtl_output_subtile_printer(" + dest_name + "_vals, " + str(output_tile_size) + ", 0, output_file);\n")
    main_file.write("    output_file.close();\n")

def write_subtile_paths(main_file, output_dir, kernel_name, batch_size):
    main_file.write("    if (mode == \"tiling\") {\n")
    main_file.write("        subtile_paths_printer(subtile_paths, std::string(\"" + output_dir + "\"), std::string(\"" + kernel_name + "\"), " + str(batch_size) + ");\n")
    main_file.write("    }\n")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    prog="Lego_v0",
                    description="Generate Cpp code for tiling and reduction given the input program and tensors")
    parser.add_argument("-t", "--tensor", type=str, default="./input/tensor.txt")
    parser.add_argument("-p", "--program", type=str, default="./input/program.txt")
    parser.add_argument("--bitstream", type=str, default="./input/bitstream.bs")
    parser.add_argument("--design_meta", type=str, default="./input/design_meta.json")
    parser.add_argument("--reg_write", type=str, default="./input/reg_write.h")
    parser.add_argument("--positive_only", action="store_true", help="Option that force all input data to be positive (used in onyx results)")
    parser.add_argument("-m", "--mode", type=str, default="rtl")
    parser.add_argument("-b", "--comal_batch_size", type=int, default=100000)
    parser.add_argument("-g", "--gold_check", choices=["s", "d", "none"], default = "none")
    parser.add_argument("-w", "--workspace", action="store_true")
    parser.add_argument("-o", "--output_dir", type=str, default="lego_scratch", help="Output directory for the generated tiles")
    parser.add_argument("-n", "--no_preprocess", action="store_true")   
    parser.add_argument("-x", "--xplicit_zero", action="store_true")
    parser.add_argument("-u", "--unroll_cgen", type=str, default="0")
    parser.add_argument("-f", "--fill_diag", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--gcheck", action="store_true")
    parser.add_argument("--ap_gcheck", action="store_true")
    parser.add_argument("--nnz_ctr", action="store_true")

    args = parser.parse_args()

    tensor_path_dict, tensor_type_dict, tensor_format_dict, tensor_transpose_dict, tensor_density_dict, tensor_dtype_dict = tensor_path_type_dict(args.tensor)

    level = "ap"
    app_name, dest, op, ap_dest_id, ap_dest_map, ap_source_id, ap_source_map, expr, ap_split_factor, op_list, ap_schedule, scalar, ap_activation = parse(args.program, level)

    level = "cp"
    _, _, _, cp_dest_id, cp_dest_map, cp_source_id, cp_source_map, _, cp_split_factor, _, cp_schedule, scalar, cp_activation = parse(args.program, level)

    level = "cg"
    _, _, _, cg_dest_id, cg_dest_map, cg_source_id, cg_source_map, _, cg_split_factor, _, cg_schedule, scalar, cg_activation = parse(args.program, level)

    process_csf    = args.xplicit_zero
    unroll         = args.unroll_cgen
    fill_diag      = args.fill_diag
    gcheck         = args.gcheck
    ap_gcheck      = args.ap_gcheck
    nnz_ctr        = args.nnz_ctr

    # go throug the activation function and return list of lut required
    activation_list = cg_activation.copy()
    activation_list.extend(list(tensor_transpose_dict.values()))
    lut_tensor = parse_lut_tensor(activation_list)

    if os.path.exists("./lego_scratch"):
        shutil.rmtree("./lego_scratch")
    os.mkdir("./lego_scratch")
    
    if os.path.exists(os.path.join(args.output_dir, app_name)):
        shutil.rmtree(os.path.join(args.output_dir, app_name))
    os.makedirs(os.path.join(args.output_dir, app_name), exist_ok=True)

    mapping_dict = {}

    for key, value in dest.items():
        dest_read = key

    mode = args.mode
    
    glb_tile_offset = None
    glb_bank_offset = None
    if mode == "onyx" or mode == "opal":
    
        # decide the bank and tile offset of GLB base on the chip
        if mode == "onyx":
            glb_tile_offset = "0x40000"
            glb_bank_offset = "0x20000"
        elif mode == "opal":
            glb_tile_offset = "0x20000"
            glb_bank_offset = "0x10000"

        mapping_dict = mapping_dict_gen(args.design_meta)
        main_file = open(os.path.join(args.output_dir, app_name) + "/main.c", "w+")
        main_gen_c_lib_include(main_file)
        main_app_header_include(main_file, app_name, gcheck, ap_gcheck)
        main_gen_soc_lib_include(main_file)
        main_block_1(main_file, args.unroll_cgen, args.debug)
        main_block_2(main_file, mapping_dict, op_list, args.unroll_cgen, glb_tile_offset, glb_bank_offset, args.debug)
        main_block_3(main_file, mapping_dict, dest_read, args.unroll_cgen, glb_tile_offset, glb_bank_offset, args.debug, gcheck, ap_gcheck)    

        inputs, outputs, input_order, output_order, bitstream_name = meta_scrape(args.design_meta)

        unrolling_header_file = open(os.path.join(args.output_dir, app_name) + "/" + app_name + "_unrolling.h", "w+")
        unrolling(inputs, outputs, input_order, output_order, unrolling_header_file, app_name, unroll, glb_tile_offset, glb_bank_offset)

        bitstream_file = args.bitstream 
        bitstream_header_file = open(os.path.join(args.output_dir, app_name) + "/" + app_name + "_script.h", "w+")
        convert_bs(bitstream_file, bitstream_header_file)

        linker_header_file = open(os.path.join(args.output_dir, app_name) + "/sections.ld", "w+")
        first_half_of_body(linker_header_file)
        input_list = [input.strip(".raw") for input in inputs]
        linker_header_file.write(generate_data_location_content(input_list, input_order, glb_tile_offset))
        if(unroll != "0"): 
            linker_header_file.write(generate_data_location_content_unroll(input_list, input_order, glb_tile_offset))
        bottom_half_of_body(linker_header_file)

        reg_write_file = args.reg_write

        reg_write_content = generate_reg_write(reg_write_file, glb_tile_offset, glb_bank_offset)

        with open(os.path.join(args.output_dir, app_name) + '/' + app_name + '_reg_write.h', 'w+') as file:
            file.write(reg_write_content)
    
    for key, value in tensor_path_dict.items():
        output_dir_path = "./lego_scratch/" + "tensor_" + key 
        tensor_schedule = []
        tensor_schedule.append(ap_source_map[key])
        tensor_schedule.append(cp_source_map[key])
        tensor_schedule.append(cg_source_map[key])
        tensor_size = []
        id_list = op[key]

        for i in range(0, 3):
            tensor_size.append([])

        for i in range(0, len(id_list)):
            if id_list[i] == '0':
                tensor_size[0].append('0')
            else:
                tensor_size[0].append(int(ap_split_factor[id_list[i]][0]))
        
        for i in range(0, len(id_list)):
            if id_list[i] == '0':
                tensor_size[1].append('0')
                tensor_size[2].append('0')
            else:
                tensor_size[1].append(int(cp_split_factor[id_list[i]][0]))
                tensor_size[2].append(int(cp_split_factor[id_list[i]][1]))
        
        input_dir_path = tensor_path_dict[key]
        tensor_type    = tensor_type_dict[key]
        transpose      = tensor_transpose_dict[key]  
        format         = tensor_format_dict[key]  
        density        = tensor_density_dict[key]
        dtype          = tensor_dtype_dict[key]

        if(not args.no_preprocess): 
            pre_process.process(tensor_type, input_dir_path, output_dir_path, tensor_size, tensor_schedule, format, transpose, density, args.gold_check, args.positive_only, dtype, fill_diag)    
    
    workspace = args.workspace

    if(args.gold_check == "s"):
        gold_cgen.sparse(expr, op_list, op, dest, ap_split_factor, "./lego_scratch/", scalar, workspace)
    elif(args.gold_check == "d"):
        gold_file = open("gold_check.py", "w+") 
        stmt = gold_cgen.dense(expr, op_list, op, dest, "./lego_scratch/")
        gold_file.write("".join(stmt))

    
    main_file = open("main.cpp", "w+")

    # Printing the header files
    main_file.write("#include <stdlib.h>\n")   
    main_file.write("#include <stdio.h>\n")
    main_file.write("#include <cstring>\n")
    main_file.write("#include <iostream>\n")
    main_file.write("#include <fstream>\n")
    main_file.write("#include <vector>\n")
    main_file.write("#include <string>\n")
    main_file.write("#include <cassert>\n")
    main_file.write("#include <sys/types.h>\n")
    main_file.write("#include <sys/stat.h>\n")
    main_file.write("using namespace std;\n")
    main_file.write("\n")
    main_file.write("#include \"src/data_parser.h\"")
    main_file.write("\n")
    main_file.write("#include \"src/mem_op.h\"")
    main_file.write("\n")
    main_file.write("#include \"src/activation.h\"")
    main_file.write("\n")
    main_file.write("#include \"src/bf16_op.h\"")
    main_file.write("\n")
    main_file.write("\n")

    # CGRA gold code
    if cg_source_id[op_list[0]] == ['0']:
        tensor_dim = "0"
    else:
        tensor_dim = str(len(cg_source_id[op_list[0]]))
    stmt = ""
    stmt = stmt + "(" + "subtile" + tensor_dim + " subtile_" + op_list[0]  

    for op in op_list[1:]: 
        if cg_source_id[op] == ['0']:
            tensor_dim = "0"
        else:
            tensor_dim = str(len(cg_source_id[op]))
        stmt = stmt + ", " + "subtile" + tensor_dim + " subtile_" + op
    
    if(nnz_ctr):
        stmt += ", int curr_subtile_num, ofstream &output_gold_file, ofstream &nnz_file)"
    else: 
        stmt += ", int curr_subtile_num, ofstream &output_gold_file)"

    main_file.write("float* subtile_gold" + stmt + " {\n")
    stile_outsize = cg_tensor_decleration(main_file, cg_source_id, cg_split_factor, cg_dest_id, scalar, nnz_ctr)

    input_activation = tensor_transpose_dict
    apply_input_activation(main_file, input_activation)

    for element in codegen.lower(expr, cg_source_id, cg_source_id, op_list, cg_schedule, 1, "cg", cg_split_factor, cg_dest_id, mode, cg_source_id, cg_source_map, scalar, workspace, process_csf, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict):
        if element != [""]:
            main_file.write(element[0])
            main_file.write("\n")

    for key in dest.keys():
        dest = key

    main_file.write("\n")
    cg_tile_size = 1
    if (scalar != 1):
        for key in cg_dest_id.keys():
            for id in cg_dest_id[key]:
                cg_tile_size *= cg_split_factor[id][1]
    apply_output_activation(main_file, cg_tile_size, cg_activation, cg_dest_id)

    if(mode == "rtl"):
        stmt = "    rtl_output_subtile_printer(" + dest + "_vals, output_subtile_size, curr_subtile_num, output_gold_file);"
    elif(mode == "onyx" or mode == "opal"):
        stmt = ""
        if(nnz_ctr):     
            stmt += "    nnz_file << out_nnz_id.size();\n"
            stmt += "    nnz_file << \"\\n\";\n"
            stmt += "\n"

        if(gcheck):

            if(not ap_gcheck):
                stmt += "    if(curr_subtile_num == 0){"
                stmt += "\n"
                
                if(scalar != 1):
                    for key in cg_dest_id.keys():
                        out_id_list = cg_dest_id[key]
                        out_id_map = cg_dest_map[key]
                    for i in range(0, len(out_id_list)):
                        stmt += "        header_subtile_dim_decl(output_gold_file, " + str(out_id_map[i]) + ", " + str(cg_split_factor[out_id_list[i]][1]) + ");\n"
                
                stmt += "        header_check_gold(output_gold_file, output_subtile_size, false);\n"

                stmt += "    }"
                stmt += "\n"
                stmt += "\n"

            if ap_gcheck:
                stmt += "    output_subtile_printer(" + dest + "_vals, output_subtile_size, curr_subtile_num, output_gold_file, \"" + dtype +  "\", true, op_cnt);"
            else:
                stmt += "    output_subtile_printer(" + dest + "_vals, output_subtile_size, curr_subtile_num, output_gold_file, \"" + dtype +  "\", false, op_cnt);"

    main_file.write(stmt)
    main_file.write("\n")
    main_file.write("\n")
    for key in cg_dest_id.keys():
        return_key = key
    main_file.write("    return " + return_key + "_vals;\n")
    main_file.write("\n")
    main_file.write("}\n")
    main_file.write("\n")

    main_file.write("float* read_subtile_output(std::string subtile_path) {\n")
    subtile_output_declaration(main_file, cg_dest_id, cg_split_factor, scalar)
    rtl_output_dest_id = {}
    for key in cg_dest_id.keys():
        dest_name = key
        # have to do this conversion to prevent input vals array and the converted dense output array 
        # having the same variable name due to the expression A = A
        rtl_output_dest_id[key + "_output"] = cg_dest_id[key]

    # Conversion from fibertree sparse rtl/comal output file to dense matrix representation for reduction
    # This is accomplished by generating code using the A = A expression 

    if(scalar != 1):
        for element in codegen.lower("(" + dest_name + ")", cg_dest_id, cg_dest_id, [dest_name], cg_dest_id[dest_name], 1, "cg", cg_split_factor, rtl_output_dest_id, mode, rtl_output_dest_id, cg_dest_map, scalar, workspace, process_csf, unroll, gcheck, ap_gcheck, 0, lut_tensor, dtype, tensor_format_dict):
            if element != [""]:
                main_file.write(element[0])
                main_file.write("\n")
    else:
        main_file.write("    " + dest_name + "_output_vals[0] = " + dest_name + "_vals_vec[0];\n")

    main_file.write("\n")
    main_file.write("    return " + dest_name + "_output_vals;\n")
    main_file.write("}\n")
    main_file.write("\n")

    # Sub-tile pairing code
    if cp_source_id[op_list[0]] == ['0']:
        tensor_dim = "0"
    else:
        tensor_dim = str(len(cp_source_id[op_list[0]]))
    stmt = ""
    stmt = stmt + "(" + "tile" + tensor_dim + " tile_" + op_list[0]  
    
    for op in op_list[1:]: 
        if cp_source_id[op] == ['0']:
            tensor_dim = "0"
        else:
            tensor_dim = str(len(cp_source_id[op]))
        stmt = stmt + ", " + "tile" + tensor_dim + " tile_" + op
    stmt += ", std::string curr_tile"
    
    if mode == 'rtl':
        stmt += ", std::vector<std::string> &subtile_paths, std::string mode"

    stmt = stmt + ")"

    main_file.write("float* tile_operate" + stmt + " {\n")

    cp_tensor_decleration(main_file, cp_source_id, cp_split_factor, mode, args.output_dir, app_name, unroll, gcheck, ap_gcheck)
    main_file.write("\n")

    if(workspace):
        main_file.write(codegen.workspace_declaration(cp_split_factor, cp_dest_id, scalar))
        main_file.write("\n")

    for element in codegen.lower(expr, cp_source_id, cp_source_id, op_list, cp_schedule, 1, "cp", cp_split_factor, cp_dest_id, mode, cg_source_id, cg_source_map, scalar, workspace, process_csf, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict):
        if element != [""]:
            main_file.write(element[0])
            main_file.write("\n")

    cp_closing_decleration(main_file, cp_source_id, cg_source_map, op_list, mode, ap_dest_id, unroll, glb_tile_offset, gcheck, ap_gcheck, cg_dest_id, cg_dest_map, stile_outsize, scalar, mapping_dict=mapping_dict, lut_tensor=lut_tensor)
    main_file.write("\n")

    if(workspace):
        stmt = codegen.workspace_reduction(cp_split_factor, "cp", cp_dest_id, scalar)
        for line in stmt:
            main_file.write(line)
        main_file.write("\n")

    cp_tile_size = 1

    if(scalar != 1):
        for key in cp_dest_id.keys():
            for id in cp_dest_id[key]:
                cp_tile_size *= cp_split_factor[id][0]

    apply_output_activation(main_file, cp_split_factor, cp_activation, cp_dest_id)
    
    main_file.write("\n")
    for key in cg_dest_id.keys():
        return_key = key
    
    if(workspace):
        main_file.write("    return " + return_key + "_vals;\n")
    else: 
        main_file.write("    return NULL;\n")

    main_file.write("}\n")
    main_file.write("\n")

    # AP driver code
    main_file.write("int main(int argc, char *argv[]) {\n")
    main_file.write("\n")
    if mode == "rtl":
        # parsing command line argument that specify if we are in reduction mode or not
        # reduction mode: iterate through all the subtile results computed by rtl/comal and perform reduction/combination
        # tiling mode: iterate through all the subtiles and print them out for rtl/comal
        main_file.write("    assert(argc == 2);\n")
        main_file.write("    std::string mode = argv[1];\n")

    ap_tensor_decleration(main_file, ap_source_id)

    # vector for storing the list of all the subtile path 
    # this is for comal
    if mode == "rtl":
        main_file.write("\n")
        main_file.write("    std::vector<std::string> subtile_paths;\n")

    main_file.write("\n")

    if(workspace):
        main_file.write(codegen.workspace_declaration(ap_split_factor, ap_dest_id, scalar))
        main_file.write("\n")

    for element in codegen.lower(expr, ap_source_id, ap_source_id, op_list, ap_schedule, 1, "ap", ap_split_factor, ap_dest_id, mode, cp_source_id, cp_source_map, scalar, workspace, process_csf, unroll, gcheck, ap_gcheck, nnz_ctr, lut_tensor, dtype, tensor_format_dict):
        if element != [""]:
            main_file.write(element[0])
            main_file.write("\n")

    if(workspace):        
        stmt = codegen.workspace_reduction(ap_split_factor, "ap", ap_dest_id, scalar)
        for line in stmt:
            main_file.write(line)
        main_file.write("\n")
    
    # generate code that applies the activation function specified in the argument
    ap_tile_size = 1

    if(scalar != 1):
        for key in ap_dest_id.keys():
            for id in ap_dest_id[key]:
                ap_tile_size *= ap_split_factor[id][0]
                
    apply_output_activation(main_file, ap_tile_size, ap_activation, ap_dest_id)

    # generate code that write the output matrix to file
    if (workspace):
        write_output(main_file, ap_split_factor, ap_dest_id, scalar, args.output_dir, app_name)
        main_file.write("\n")

    # genearte the toml path list file for comal
    if mode == "rtl":
        write_subtile_paths(main_file, args.output_dir, app_name, args.comal_batch_size)

    main_file.write("\n")
    main_file.write("    return 0;\n")
    main_file.write("}\n")
    main_file.close()
    