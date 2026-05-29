import os 
import re
import numpy as np 
import argparse


directory = "ctests"
app_list = [x[0] for x in os.walk(directory)]
app_list = app_list[1:]

total_count = 0
pass_count  = 0
fail_count  = 0

regex = re.compile(r'program.*\.txt')

for app in app_list: 
    for roots,dirs,files in os.walk(app):
        for file in files:
            if regex.match(file):
                program_file = app + "/" + file
                tensor_file  = app + "/tensor" + file[7:]

                print(program_file)
                print(tensor_file)

                os.system("./lego_test_sparse.sh " + program_file + " " + tensor_file)
                
                file1 = "lego_scratch/gold_output.txt"
                gold_mat = np.loadtxt(file1)

                if len(gold_mat.shape) == 0:
                    gold_mat = np.array([gold_mat])

                file2 = "lego_scratch/ctest_output/output.txt"

                output_mat = np.zeros(gold_mat.shape, dtype=np.float32)
                with open(file2, "r") as f:
                    for i in range(gold_mat.shape[0]):
                        output_mat[i] = float(f.readline().strip())

                check = np.allclose(output_mat, gold_mat, rtol=0.0000001)
                total_count += 1
                if check:                     
                    pass_count += 1
                    print("\033[32m=========== OUTPUT MATCHES GOLD ===========\033[0m")
                else: 
                    fail_count += 1
                    print("\033[31m=========== OUTPUT DOES NOT MATCH GOLD ===========\033[0m")

print("Total tests: ", total_count)
print("Passed:      ", pass_count)
print("Failed:      ", fail_count)

