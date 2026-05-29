# script to convert bitstream to h file

import json


def meta_scrape(meta_file_name):

    f = open(meta_file_name)
    meta = json.load(f)

    input_files = []
    input_order_list = []
    output_files = []
    output_order_list = []


    # inputs 
    for input in meta["IOs"]["inputs"]:
        input_files.append(input["datafile"])
        input_order = []
        for io in input["io_tiles"]:
            input_order.append(io["x_pos"] // 2)
        input_order_list.append(input_order)

    # outputs
    for output in meta["IOs"]["outputs"]:
        output_files.append(output["datafile"])
        output_order = []
        for io in output["io_tiles"]:
            output_order.append(io["x_pos"] // 2)
        output_order_list.append(output_order)
    
    return input_files, output_files, input_order_list, output_order_list,  meta["testing"]["bitstream"]

def mapping_dict_gen(design_file):
    
    inputs, outputs, input_order, output_order, bitstream_name = meta_scrape(design_file)
    map_dict = {}
    dim_dict = {}
    for input in inputs: 
        input_name = input.split("_")[1]
        input_mode = input.split("_")[3].split(".")[0]
        if(input_name not in map_dict.keys()):
            dim_dict[input_name] = 0
            map_dict[input_name] = {}
            map_dict[input_name][input_mode] = input_order[inputs.index(input)][0]
        else: 
            dim_dict[input_name] += 1
            map_dict[input_name][input_mode] = input_order[inputs.index(input)][0]

    for output in outputs:
        output_name = output.split("_")[1]
        output_mode = output.split("_")[3].split(".")[0]
        if(output_name not in map_dict.keys()):
            dim_dict[output_name] = 0
            map_dict[output_name] = {}
            map_dict[output_name][output_mode] = output_order[outputs.index(output)][0]
        else: 
            dim_dict[output_name] += 1
            map_dict[output_name][output_mode] = output_order[outputs.index(output)][0]

    mapping_dict = {}

    for key in map_dict.keys():
        mapping_dict[key] = []
        for i in range(dim_dict[key]):
            mapping_dict[key].append(map_dict[key][str(i)])
        mapping_dict[key].append(map_dict[key]["vals"])

    return mapping_dict  
