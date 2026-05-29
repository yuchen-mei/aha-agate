import re
import os
import json
import argparse
import itertools
import shutil
import numpy as np
import math

def generate_rounded_sequence(start, end, num_points):
    # Generate 10 equally spaced integers between start and end
    sequence = np.linspace(start, end, num_points).round().astype(int)
    
    # Round each number to the nearest 0 or 5
    rounded_sequence = np.round(sequence / 5) * 5
    
    return rounded_sequence.astype(int)

# Function to generate input data
def generate_input_data(entry):
    name = entry["name"]
    sweep = entry["sweep"]
    tile_list = entry["L2_tile_size_list"]
    tensor_list = entry["L0_L1_tile_size"]
    datasets = entry["datasets"]
    app = entry["app"][0]  # Assuming single app for each entry
    schedule_list = entry["schedule_list"][0]  # Assuming single schedule list for each entry
    bitstreams = entry["bitstreams"]
    pre_process = entry["pre_process"][0]
    flags = entry["flags"]

    if sweep == 1:
        # Generate input data for sweeping over tile_list and datasets
        input_data = []
        for tile in tile_list:
            for dataset in datasets:
                input_data.append([[app], schedule_list, tile, tensor_list[0].copy(), pre_process, dataset])
        return name, input_data, bitstreams, flags
    elif sweep == 0:
        # Pair tile_list and datasets element by element
        if len(tile_list) != len(datasets):
            raise ValueError("tile_list and datasets length mismatch for sweep=0")
        input_data = []
        for tile, dataset in zip(tile_list, datasets):
            input_data.append([[app], schedule_list, tile, tensor_list[0].copy(), pre_process, dataset])
        return name, input_data, bitstreams, flags 
    else:
        raise ValueError(f"Unknown sweep mode: {sweep}")

def num_modes(equation):
    # Split the equation into left-hand side (output) and right-hand side (input)
    lhs_rhs = equation.split('=')  # Split at '='
    
    if len(lhs_rhs) != 2:
        raise ValueError("Invalid equation format. Make sure it contains '='.")

    # We are interested only in the right-hand side (RHS) of the equation (inputs)
    rhs = lhs_rhs[1]
    
    # Use regex to find all indices (variables) inside parentheses on the RHS
    indices = re.findall(r'[a-zA-Z]', rhs)  # This matches any alphabetical character (variable)
    
    # Assign values to indices (you can customize the values if needed)
    # By default, we're assigning 1 to every index we find
    values = {idx: 1 for idx in set(indices)}  # Assign value 1 to each unique variable

    # Sum up the values based on the extracted indices
    total_sum = sum(values[idx] for idx in indices)

    return total_sum

# Main function to process all data entries and generate input data
def process_data(data):
    all_input_data = []
    for entry in data:
        name, input_data, bitstreams, flags = generate_input_data(entry)
        all_input_data.append([name, input_data, bitstreams, flags])
    return all_input_data

def generate_program_txt(equation, schedules, tile_splits, tensor_splits, activation_ap='none', activation_cp='none', activation_cgra='none'):
    """
    Generates the content of the program.txt file based on dynamic indices.
    
    :param equation: String, the equation for matrix multiplication (e.g. "X(i,j)=B(i,j)*C(i,j)")
    :param schedules: List of schedules, 3 elements for ap, cp, cgra (e.g. ["ikj", "ikj", "ijk"])
    :param tile_splits: List of splits for indices (e.g. [30, 30, 30] for i, j, k)
    :param activation_ap: String, activation for ap (default: none)
    :param activation_cp: String, activation for cp (default: none)
    :param activation_cgra: String, activation for cgra (default: none)
    
    :return: String, content of program.txt
    """
    # Build split strings dynamically based on number of indices

    splits = ""
    for idx, split in zip(schedules[0], tile_splits):  # Using schedule_ap to match with tile splits
        splits += f"{idx}:split:{tensor_splits[0]}:{tensor_splits[1]}:{split}\n"

    program_txt = f"""
app_name: app
stmt: {equation[0]}
schedule_ap:   [{schedules[0]}]
schedule_cp:   [{schedules[1]}]
schedule_cgra: [{schedules[2]}]
{splits.strip()}
activation_ap:   {activation_ap}
activation_cp:   {activation_cp}
activation_cgra: {activation_cgra}
"""
    return program_txt.strip()

def generate_tensor_txt(tensor_data, dataset_names):
    """
    Generates the content of the tensor.txt file.
    
    :param tensor_data: List of tensors and their info (e.g. ["B:0", "C:onyx_matmul"])
    :param dataset_names: List of datasets to be appended to tensors (e.g. ["ss", "football"])
    
    :return: String, content of tensor.txt with hardcoded 60.
    """
    tensor_txt = ""
    for tensor in tensor_data:
        name, var = tensor.split(":")
        tensor_txt += f"{name}:{dataset_names[0]}:{dataset_names[1]}:s:{var}:60:int\n"
    return tensor_txt.strip()

def process_input_data(data):
    """
    Processes the input data and generates the program.txt and tensor.txt files.
    
    :param input_data: List containing the equation, schedules, tile splits, tensors, and datasets.
    """
    #print(data)
    # Unpack input data
    equation, schedules, tile_splits, tensor_splits, tensor_data, dataset_names = data
        
    # Generate content for program.txt and tensor.txt
    program_txt_content = generate_program_txt(equation, schedules, tile_splits, tensor_splits)
    tensor_txt_content = generate_tensor_txt(tensor_data, dataset_names)

    print(program_txt_content)
    print(tensor_txt_content)
    
    # Write the content to program.txt
    with open("input/program.txt", "w+") as program_file:
        program_file.write(program_txt_content)
        
    # Write the content to tensor.txt
    with open("input/tensor.txt", "w+") as tensor_file:
        tensor_file.write(tensor_txt_content)


def create_input_data(apps, schedule_list, tile_list, pre_process, datasets):
    # Create Cartesian product of all inputs
    input_data = list(itertools.product(apps, schedule_list, tile_list, pre_process, datasets))
    return input_data

def run_codegen(args):
    os.system("rm -rf lego_scratch/")
    os.system("mkdir lego_scratch/")
    os.system("rm -rf main.cpp")
    os.system("python3 main.py " + args)
    os.system("g++ -o main main.cpp src/data_parser.cpp src/mem_op.cpp src/bf16_op.cpp")
    os.system("./main")

def find_file_in_directory(file_name, search_path):
    for root, dirs, files in os.walk(search_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def check_size(out_dir, modes): 
    stile_file_path = find_file_in_directory("num_stile_pairs.txt", out_dir)

    with open(stile_file_path, "r") as file:
        lines = [line.strip().split(" ") for line in file]

    in_limit = 1
    for runs in lines: 
        total_runs = 0
        for run in runs: 
            total_runs += int(run)
        size = total_runs * 2 * modes * 2 // 1024
        if(size > 120): 
            in_limit = 0
    
    mode_len_path = find_file_in_directory("mode_data_len.txt", out_dir)

    with open(mode_len_path, "r") as mode_len_file:
        mode_len_lines = [line for line in mode_len_file]

    for mode_len in mode_len_lines:
        if(int(mode_len) > (64 * 1024)): 
            in_limit = 0
  
    return in_limit

def check_nnz_max(out_dir): 
    nnz_path = find_file_in_directory("nnz_check.txt", out_dir)

    with open(nnz_path, "r") as nnz_file:
        lines = [line for line in nnz_file]

    nnz_lines = []
    i = 0

    while i < len(lines):
        if(lines[i].strip().isdigit()):
            nnz_lines.append(int(lines[i].strip()))
        i += 1

    not_max = 1
    for nnz in nnz_lines:
        if(int(nnz) > 900): 
            not_max = 0
            break
    
    return not_max 

def check_size_adapt(out_dir, modes, prev_result_dict_keys):
    nnz_path = find_file_in_directory("nnz_check.txt", out_dir)

    with open(nnz_path, "r") as nnz_file:
        lines = nnz_file.readlines()

    # Process the lines to create the dictionary
    result_dict = {}
    i = 0

    while i < len(lines):
        key = lines[i].strip()
        value_list = []
        i += 1
        # Collect all numeric values until the next path or end of lines
        while i < len(lines) and lines[i].strip().isdigit():
            value_list.append(int(lines[i].strip()))
            i += 1
        result_dict[key] = value_list

    del_key_list = []

    for key, value_list in result_dict.items():
        for val in value_list:
            if val > 900:
                # Remove the directory 
                shutil.rmtree(key)
                # Remove the key from the dictionary
                del_key_list.append(key)
                break

    for key in del_key_list:
        del result_dict[key]

    not_empty = 0

    for key, value_list in result_dict.items():
        for prev_key in prev_result_dict_keys:
            if key.split("//")[-1] == prev_key.split("//")[-1]:
                prev_dir = prev_key.split("//")[0]
                not_empty += 1
                shutil.rmtree(prev_key)
    
    if((not_empty == len(prev_result_dict_keys)) and not_empty != 0):
        shutil.rmtree(prev_dir)

    result_dict_keys = list(result_dict.keys())
    

    if len(result_dict) == 0:
        return 0, result_dict_keys
    else:
        return 1, result_dict_keys

if __name__ == "__main__":
    # Input format

    parser = argparse.ArgumentParser(
                    prog="JSSC Lego Wrapper",
                    description="Generates the input and outputs for JSSC testing")

    parser.add_argument("--json", type=str, default="jssc_inputs/jssc_matmul_input.json")     
    parser.add_argument("--mode", type=str, default="onyx")      
    args = parser.parse_args()

    with open(args.json) as f:
        json_data = json.load(f)

    data = process_data(json_data)
   

    for item in data: 
        curr_app_name   = item[0]
        curr_input_data = item[1]
        curr_bitstreams = item[2]
        curr_flags      = item[3]

        if not os.path.exists(f"./jssc_outputs/{curr_app_name}/"):
            os.makedirs(f"./jssc_outputs/{curr_app_name}/", exist_ok=True)

        for input in curr_input_data: 
            for bitstream in curr_bitstreams: 

                out_dir = f"./jssc_outputs/{curr_app_name}/{input[1][-1]}_{input[-1][-2]}_{bitstream[0][-8:]}_{bitstream[1]}_{input[2][-1]}/"
                print(out_dir)

                if os.path.exists(out_dir):     
                    shutil.rmtree(out_dir)               
                os.makedirs(out_dir, exist_ok=True)

                bitstream_file   = f"./jssc_inputs/{bitstream[0]}/bitstream.bs"
                reg_write_file   = f"./jssc_inputs/{bitstream[0]}/reg_write.h"
                design_meta_file = f"./jssc_inputs/{bitstream[0]}/design_meta.json"

                unroll_flag = bitstream[1]
                args_list = f"--mode {args.mode} -u {unroll_flag}"

                curr_dataset = input[-1] 

                if(curr_dataset[-1] == "_"):
                    process_input_data(input)
                    for flag in curr_flags[0]: 
                        if flag != "":
                            args_list += f" {flag}"

                    python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"

                    run_codegen(python_args)
                    modes = num_modes(input[0][0])
                    check_size(out_dir, modes)
        
                elif(curr_dataset[-1] == "r"):
                    
                    in_limit = 0

                    while(not in_limit): 
                        
                        args_list = f"--mode {args.mode} -u {unroll_flag}"

                        process_input_data(input)
                        for flag in curr_flags[0]: 
                            if flag != "":
                                args_list += f" {flag}"

                        python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                        run_codegen(python_args)

                        modes = num_modes(input[0][0])
                        in_limit = check_size(out_dir, modes)

                        if(not in_limit): 
                            print(f"{input[-1][-2]}: Mem. going out-of-bounds for tile_dim: {input[-3][-1]}, trying with tile_dim: {input[-3][-1]//2}")
                            input[-3][-1] = input[-3][-1]//2        
                elif(curr_dataset[-1] == "s"):
                    
                    args_list = f"--mode {args.mode} -u {unroll_flag}"

                    args_list += " --nnz_ctr"

                    for flag in curr_flags[0]: 
                        if flag != "":
                            args_list += f" {flag}"

                    tile_size =  input[-3][-1]

                    start_stile_size = input[2][0]
                    input_test = input.copy()

                    not_max = True
                    run = 0

                    curr_test_tile_size = start_stile_size

                    while(not_max):
                        
                        input_test[2] = [curr_test_tile_size] * len(input_test[2])
                        process_input_data(input_test)
                        python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                        print(python_args)
                        run_codegen(python_args)
                        not_max = check_nnz_max(out_dir)
                        prev_test_tile_size = curr_test_tile_size - (5 * (2**(run - 1)))
                        curr_test_tile_size += (5 * (2**(run)))
                        if(curr_test_tile_size >= tile_size):
                            break
                        run += 1

                    not_max = True

                    curr_test_tile_size = prev_test_tile_size

                    while(not_max):
                        curr_test_tile_size = curr_test_tile_size + 15
                        if(curr_test_tile_size >= tile_size):
                            break
                        input_test[2] = [curr_test_tile_size] * len(input_test[2])
                        process_input_data(input_test)
                        python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                        print(python_args)
                        run_codegen(python_args)
                        not_max = check_nnz_max(out_dir)
                
                    end_stile_size = curr_test_tile_size - 20

                    if(end_stile_size >= start_stile_size + 5):
                        num_points = math.floor(1 + 2.5 * math.log10(end_stile_size - start_stile_size))
                    else:
                        num_points = 1  
                    stile_list = generate_rounded_sequence(start_stile_size, end_stile_size, num_points)

                    for size in stile_list: 
                        out_dir = f"./jssc_outputs/{curr_app_name}/{input[1][-1]}_{input[-1][-2]}_{bitstream[0][-8:]}_{bitstream[1]}_{size}/"
                        input[2] = [size] * len(input[2])

                        in_limit = 0

                        while(not in_limit): 
                            args_list = f"--mode {args.mode} -u {unroll_flag}"

                            process_input_data(input)
                            for flag in curr_flags[0]: 
                                if flag != "":
                                    args_list += f" {flag}"

                            python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                            print(python_args)
                            run_codegen(python_args)

                            modes = num_modes(input[0][0])
                            in_limit = check_size(out_dir, modes)

                            if(not in_limit): 
                                print(f"{input[-1][-2]}: Mem. going out-of-bounds for tile_dim: {input[-3][-1]}, trying with tile_dim: {input[-3][-1]//2}")
                                input[-3][-1] = input[-3][-1]//2   
                                
                elif(curr_dataset[-1] == "f"):

                    mid_stile_size = input[2][0]

                    start_stile_size = mid_stile_size - 10
                    stile_list = []

                    for i in range(0,5):
                        stile_list.append(start_stile_size + 5 * i)

                    for size in stile_list: 
                        out_dir = f"./jssc_outputs/{curr_app_name}/{input[1][-1]}_{input[-1][-2]}_{bitstream[0][-8:]}_{bitstream[1]}_{size}/"
                        input[2] = [size] * len(input[2])

                        in_limit = 0

                        while(not in_limit): 
                            
                            if(unroll_flag != 0):
                                args_list = f"--mode {args.mode} -u {unroll_flag}"
                            else:
                                args_list = f"--mode {args.mode}"

                            process_input_data(input)
                            for flag in curr_flags[0]: 
                                if flag != "":
                                    args_list += f" {flag}"

                            python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                            run_codegen(python_args)

                            modes = num_modes(input[0][0])
                            in_limit = check_size(out_dir, modes)

                            if(not in_limit): 
                                print(f"{input[-1][-2]}: Mem. going out-of-bounds for tile_dim: {input[-3][-1]}, trying with tile_dim: {input[-3][-1]//2}")
                                input[-3][-1] = input[-3][-1]//2  

                elif(curr_dataset[-1] == "a"):

                    global_tile_size = input[-3][-1] 
                    global_tile_size_list = [global_tile_size, global_tile_size//2, global_tile_size//4]


                    for L1_tile_size in global_tile_size_list:

                        curr_stile_size = input[2][0]   

                        # Generate a list from curr_stile_size to L1_tile_size in steps of 5
                        stile_sweep_list = list(range(curr_stile_size, L1_tile_size, 5))

                        atleast_one_in_limit = 1
                        prev_result_dict = []

                        for size in stile_sweep_list:

                            out_dir = f"./jssc_outputs/{curr_app_name}/{input[1][-1]}_{input[-1][-2]}_{bitstream[0][-8:]}_{bitstream[1]}_{L1_tile_size}_{size}/"

                            input[-3][-1] = L1_tile_size
                            input[2] = [size] * len(input[2])

                            if(atleast_one_in_limit != 0):
    
                                if(unroll_flag != 0):
                                    args_list = f"--mode {args.mode} -u {unroll_flag}"
                                else:
                                    args_list = f"--mode {args.mode}"

                                args_list += " --nnz_ctr"

                                process_input_data(input)
                                for flag in curr_flags[0]: 
                                    if flag != "":
                                        args_list += f" {flag}"

                                python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                                run_codegen(python_args)

                                modes = num_modes(input[0][0])  

                                atleast_one_in_limit, prev_result_dict = check_size_adapt(out_dir, modes, prev_result_dict)

                else: 
                    try: 
                        L1_tile_size = int(curr_dataset[-1])
                        input[-3][-1] = L1_tile_size
                        process_input_data(input)
                    except ValueError: 
                        print("Check GLB tile size param passed. Using default val.")
                        process_input_data(input)

                    for flag in curr_flags[0]: 
                        if flag != "":
                            args_list += f" {flag}"

                    python_args = f"{args_list} --bitstream {bitstream_file} --design_meta {design_meta_file} --reg_write {reg_write_file} --output_dir {out_dir}"
                    run_codegen(python_args)
                                
