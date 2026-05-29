import os
import subprocess
import glob

GINConv_layers = ["GINConv_layer0", "GINConv_layer1", "GINConv_layer2", "GINConv_layer3"]
GINConv_layers = ["GINConv_layer0"]
GINConv_kernels = ["aggr_feat", "mlp_layer0_trans", "mlp_layer0_bias", "mlp_layer1_trans", "mlp_layer1_bias"]

for ginconv_layer in GINConv_layers:
    GINConv_layer_path = os.path.join("input/gin", ginconv_layer)
    for kernel in GINConv_kernels:
        print(f"Running {ginconv_layer} {kernel}")
        program_file = os.path.join(GINConv_layer_path, kernel + "_program.txt")
        tensor_file = os.path.join(GINConv_layer_path, kernel + "_tensor.txt")
        try:
            print(f"=== Generating cpp code ===")
            tile = subprocess.run(["python", "main.py", "--program", program_file, 
                                          "--tensor", tensor_file, "--output_dir" , "output",
                                          "--mode", "rtl", "--workspace"], 
                                          capture_output=True, text=True)
            tile.check_returncode()
        except subprocess.CalledProcessError as e:
            print(e.stderr)

        try: 
            print(f"=== Compiling cpp code ===")
            tile = subprocess.run(["g++", "-o", "main", "main.cpp", "src/data_parser.cpp", "src/mem_op.cpp", "src/activation.cpp"],
                                    capture_output=True, text=True)   

            tile.check_returncode()
        except subprocess.CalledProcessError as e:
            print(e.stderr)

        try: 
            print(f"=== Tiling ===")
            tile = subprocess.run(["./main", "tiling"],
                                    capture_output=True, text=True)

            tile.check_returncode()
        except subprocess.CalledProcessError as e:
            print(e.stderr)
        
        try: 
            print(f"=== Checking Tiled Results ===")
            output_dir = glob.glob(f"output/*_{ginconv_layer}_{kernel}")
            gold_file = f"/nobackup/bwcheng/sparse-datasets/sparse-ml/gin/f32/COLLAB/{ginconv_layer}/{kernel}/X.npy"
            tile = subprocess.run(["python", "scripts/check_gold.py", "--gold", gold_file,
                                   "--input", f"{output_dir[0]}/output.txt"],
                                    capture_output=True, text=True)
            print(tile.stdout)
            tile.check_returncode()
        except subprocess.CalledProcessError as e:
            print(e.stderr)
