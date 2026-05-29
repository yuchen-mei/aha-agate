import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--type", type=str, default="d")

args = parser.parse_args()

if(args.type == "d"):
    file1 = "lego_scratch/gold_output.npz"
    gold_mat = np.load(file1)['array1']
else: 
    file1 = "lego_scratch/gold_output.txt"
    gold_mat = np.loadtxt(file1)

if len(gold_mat.shape) == 0:
    gold_mat = np.array([gold_mat])

file2 = "lego_scratch/ctest_output/output.txt"

output_mat = np.zeros(gold_mat.shape, dtype=np.float32)
with open(file2, "r") as f:
    for i in range(gold_mat.shape[0]):
            output_mat[i] = float(f.readline().strip())

if np.allclose(output_mat, gold_mat, rtol=0.001):
    print("\033[32m=========== OUTPUT MATCHES GOLD ===========\033[0m")
else:  
    print("\033[31m=========== OUTPUT DOES NOT MATCH GOLD ===========\033[0m")
