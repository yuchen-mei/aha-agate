## Lego_v0 

### ONYX Docker Setup

Use docker_create.sh to create the docker container and within the docker container:  

-- Within sam:
```
git checkout mapping_to_cgra
pip install -r requirements.txt
pip install -e .
```

--  Within Lego_v0
```
./requirements.sh
```

Your bashrc should have (you might need to mkdir these as well)

```
export SUITESPARSE_PATH=/aha/datasets/sparse-datasets/suitesparse/
export TACO_TENSOR_PATH=/aha/datasets/sparse-datasets/other
export FROSTT_PATH=/aha/datasets/sparse-datasets/frostt/
export SUITESPARSE_FORMATTED_PATH=/aha/datasets/sam/SUITESPARSE_FORMATTED
export FROSTT_FORMATTED_TACO_PATH=/aha/datasets/sam/FROST_FORMATTED_TACO
export FROSTT_FORMATTED_PATH=/aha/datasets/sam/FROST_FORMATTED
```
### Input Language 

#### 
-- program.txt
```
app_name: matmul_ijk_football                   \\ Name of the app
stmt: X(i, j) = B(i, k) * C(k, j)               \\ Tensor expression  
schedule_ap:   [ikj]                            \\ Schedule to pair the tiles
schedule_cp:   [ikj]                            \\ Schedule to pair the subtiles
schedule_cgra: [ikj]                            \\ Schedule on the CGRA 
i:split:10000:10000:30                          \\ <tensor-dim>:<tile-dim>:<subtile-dim> 
j:split:10000:10000:30
k:split:10000:10000:30
```
- So, if we need (30, 40) subtiles for B and (40, 30) subtiles for C, the schedule would be: 
```
i:split:10000:10000:30                          
j:split:10000:10000:30
k:split:10000:10000:40
```
####
-- tensor.txt 
```
tensor_name:dataset:dataset_name:gcn_flag sparse/dense:get_other_tensor_flag:random_matrix_density(%):data_type
B:ss:quilp:s:0:60:int 
C:ss:quilp:s:shift_transpose:60:int
```
- dataset:
  - ss: SUITESPARSE
  - frostt: FROSTT
  - gen: random tensor generation
  - sparse_ml: Sparse ML datasets
  - ex: extensor
  - New datasets could be updated in pre_process.py

- dataset_name: The name of the actual .mtx or .tns file within the dataset
  
- GCN Flag <TODO: Bo Wun>

- get_other_tensor_flag:
  - Process the tensor to generate a new tensor, Ex: shift_transpose, shifts the last mode and transposes the tensor. C = B.T
  - More operations can be found in pre_process,py
 
- random_matrix_density:    
  - Percentage density of the random matrix being generated
    
- data_type: int - int16, f32 - float32, bf16 - bfloat16
####
-- bitstream.bs

-- design_meta.json

-- reg_write.h

All the above files are to be placed within: ```input/```

### Organization

- ```main.py``` generates the ```main.cpp``` code and the tiled_CSF formats for the tensors stored in ```lego_scratch/```
- Executing ```main.cpp``` performs the subtile pairing and packing of data into the ONYX format
- Execution: ```python3 main.py --mode onyx``` // Check other arguments that might be useful
- ```./lego_onyx_codegen.sh```          // For all apps 
- ```./lego_onyx_matmul_codegen.sh```   // For matmul data generation, with different schedules for tiling and pairing
- General output scripts are available at ```lego_scratch/```
- Paired sub-tiles, extents and gold data are available at ```lego_scratch/app_name/```

