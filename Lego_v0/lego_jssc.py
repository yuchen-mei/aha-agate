import os 
import re
import numpy as np 
import argparse
import shutil


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    prog="JSSC_Wrapper",
                    description="Args to select if the app could be unrolled or not")

    parser.add_argument("--app", type=str)                
    parser.add_argument("--bitstream_dir", type=str, default="bitstreams")
    parser.add_argument("--input_dir", type=str, default="inputs")
    parser.add_argument("--unroll", action="store_true")
    parser.add_argument("--xplicit_zero", action="store_true")
    parser.add_argument("--fill_diag", action="store_true")
    

    args = parser.parse_args()

    app           = args.app
    bitstream_dir = args.bitstream_dir
    input_dir     = args.input_dir 

    process_tkn = " "

    if(args.unroll):
        process_tkn += "-u "
    
    if(args.xplicit_zero):
        process_tkn += "-x "
    
    if(args.fill_diag):
        process_tkn += "-f "

    directory = "jssc_inputs/"

    app_list = os.listdir(directory)

    if not os.path.exists("./jssc_outputs/" + app + "/"):
        os.makedirs("./jssc_outputs/" + app + "/", exist_ok=True)

    regex = re.compile(r'program.*\.txt')

    app_name = app 

    design_meta_file = directory + app + "/design_meta.json"
    reg_write_file   = directory + app + "/reg_write.h"

    bitstream_list = os.listdir(directory + app + "/" + bitstream_dir + "/")
    file_list = os.listdir(directory + app + "/" + input_dir + "/")

    program_list = []
    for file in file_list: 
        if regex.match(file): 
            program_list.append(file)

    for bitstream in bitstream_list:
        for program in program_list:
            bitstream_name = bitstream[9:-3]
            program_name   = program[7:-4]

            bitstream_file = directory + app + "/" + bitstream_dir + "/" + bitstream
            program_file   = directory + app + "/" + input_dir + "/" + program 
            tensor_file    = directory + app + "/" + input_dir + "/tensor" + program[7:]

            output_dir     = "jssc_outputs/" + app + "/" + bitstream_dir + "_" + bitstream_name +  "_" + input_dir + "_" + program_name 

            os.system("rm -rf lego_scratch/")
            os.system("mkdir lego_scratch/")
            os.system("rm -rf main.cpp")
            
            args = "--mode onyx "
            args += "--program "     + program_file
            args += " --tensor "      + tensor_file
            args += " --bitstream "   + bitstream_file 
            args += " --design_meta " + design_meta_file 
            args += " --reg_write "   + reg_write_file
            args += " --output_dir "  + output_dir
            args += process_tkn

            os.system("python3 main.py " + args)
            os.system("g++ -o main main.cpp src/data_parser.cpp src/mem_op.cpp")
            os.system("./main")

    out_dir = "/aha/Lego_v0/jssc_outputs/" + app + "/"
    
    out_list = os.listdir(out_dir)

    for out in out_list: 
        os.chdir(out_dir + out)
        os.system("find . -type f -exec cp {} . \;")
        dir_list = next(os.walk(out_dir + out))[1]
        os.system("rm -rf " + dir_list[0])