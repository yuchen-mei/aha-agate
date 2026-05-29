import sys
import numpy as np
import scipy.sparse
import scipy.io
import os
import argparse
import ast
import yaml
import copy
import pickle
import random
import sparse
import sys
import math
from scipy.io import mmwrite

from pathlib import Path

from sam.util import SUITESPARSE_PATH, SuiteSparseTensor, InputCacheSuiteSparse, PydataTensorShifter, ScipyTensorShifter, \
    FROSTT_PATH, FrosttTensor, PydataSparseTensorDumper, InputCacheTensor, constructOtherMatKey, constructOtherVecKey, \
    InputCacheSparseML, SPARSEML_PATH, SparseMLTensor
from sam.sim.src.tiling.process_expr import parse_all
from lassen.utils import float2bfbin, bfbin2float

def dense_mat_padding(tensor, tile_dims):
    # make tensor size a multiple of cpu tile size
    dense_tensor = tensor.todense()
    tensor_n_dims = len(dense_tensor.shape)
    padded_tensor_size = []
    for idx in range(0, tensor_n_dims):
        if dense_tensor.shape[idx] % tile_dims[0][idx] != 0:
            padded_tensor_size.append(math.ceil(dense_tensor.shape[idx] / tile_dims[0][idx]) * tile_dims[0][idx])
        else:
            padded_tensor_size.append(dense_tensor.shape[idx])

    padded_tensor = np.zeros(padded_tensor_size)
    for idx, val in np.ndenumerate(dense_tensor):
        padded_tensor[idx] = val

    return sparse.COO(padded_tensor)

def process_coo(tensor, tile_dims, output_dir_path, format, schedule_dict, positive_only, dtype):
    
    ''' 
    This is the main function that is called to tile and store as CSF
    Inputs: 
    tensor: The input tensor in COO format
    tile_dims: The dimensions of the tiles at each level
    output_dir_path: The path to the output directory to store the CSF tiles
    '''
    
    # The input tensor is a COO tensor
    coords = []
    data = []

    if format == "s": 
        coords = tensor.coords
        data = tensor.data
    # if the input format is dense, we need to fill in all the zero entries
    elif format == "d":
        tensor = dense_mat_padding(tensor, tile_dims)
        n_dim = len(tensor.coords)
        for i in range(n_dim):
            coords.append([])
        for idx, val in np.ndenumerate(tensor.todense()):
            for i in range(n_dim):
                coords[i].append(idx[i])
            data.append(val)
    else:
        raise ValueError("Format must be either \"s\" or \"d\"")

    # The number of values in the tensor
    num_values = len(data)
    n_dim = len(coords)

    # The number of dimensions in the tensor
    n_dim = len(coords)

    # The number of levels of tiling
    n_levels = len(tile_dims)

    # Create n_levels * n_dim lists to store the coordinates and data
    n_lists = np.zeros(((n_levels + 1) * n_dim, num_values), dtype=int)
    if dtype == "int":
        d_list = np.zeros((num_values), dtype=int)
    else:
        d_list = np.zeros((num_values), dtype=float)

    if tile_dims[0] == "0": 
        d_list[0] = tensor.fill_value
    else:
        # Creating the COO representation for the tiled tensor at each level
        for i in range(num_values):
            d_list[i] = data[i] 
            for level in range(n_levels):
                for dim in range(n_dim):

                    crd_dim = schedule_dict[level][dim] 
                    nxt_dim = schedule_dict[level + 1].index(crd_dim)

                    idx1 = level * n_dim + dim
                    idx2 = (level + 1) * n_dim + nxt_dim

                    if(level == 0):
                        n_lists[idx1][i] = coords[crd_dim][i] // tile_dims[level][crd_dim]
                        n_lists[idx2][i] = coords[crd_dim][i] % tile_dims[level][crd_dim]
                    else:
                        n_lists[idx1][i] = n_lists[idx1][i] // tile_dims[level][crd_dim]
                        n_lists[idx2][i] = coords[crd_dim][i] % tile_dims[level][crd_dim]

    tiled_COO = sparse.COO(n_lists, d_list)

    # tiled_coo.coords holds the COO coordinates for each level
    # tiled_coo.data holds the data for each level

    # Create the CSF representation for the tensor at each level
    crd_dict = {} 
    pos_dict = {}

    pos_ctr = np.ones(((n_levels + 1) * n_dim), dtype=int)
 
    for i in range(num_values):   
        propogate = 0; 
        for level in range(n_levels + 1):
            for dim in range(n_dim):
                idx = level * n_dim + dim
                if(i == 0): 
                    crd_dict[idx] = [tiled_COO.coords[idx][i]]
                    pos_dict[idx] = [0] 
                else:
                    if(crd_dict[idx][-1] != tiled_COO.coords[idx][i]):
                        propogate = 1

                    if(propogate == 1):
                        pos_ctr[idx] += 1
                        crd_dict[idx].append(tiled_COO.coords[idx][i])
                        if(idx != n_levels * n_dim + n_dim - 1):
                            pos_dict[idx + 1].append(pos_ctr[idx + 1])
                     
    for level in range(n_levels + 1):
        for dim in range(n_dim):
            idx = level * n_dim + dim
            if(idx == 0):
                pos_dict[idx].append(pos_ctr[idx])
            if(idx != n_levels * n_dim + n_dim - 1):
                pos_dict[idx + 1].append(pos_ctr[idx + 1])

    # Write the CSF representation to disk
    for level in range(n_levels + 1):
        for dim in range(n_dim):
            crd_dict_path = output_dir_path + "/tcsf_crd" + str(level * n_dim + dim + 1) + ".txt"
            with open(crd_dict_path, 'w+') as f:
                for item in crd_dict[level * n_dim + dim]:
                    f.write("%s\n" % item)
            pos_dict_path = output_dir_path + "/tcsf_pos" + str(level * n_dim + dim + 1) + ".txt"
            with open(pos_dict_path, 'w+') as f:
                for item in pos_dict[level * n_dim + dim]:
                    f.write("%s\n" % item)
    
    d_list_path = output_dir_path + "/tcsf_vals" + ".txt"

    with open(d_list_path, 'w+') as f:
        if tile_dims[0][0] == '0':
            if(dtype == "int"):
                f.write("%s\n" % (int(tensor.fill_value)))
            else:
                f.write("%s\n" % (tensor.fill_value))
        else:
            for val in range(num_values):
                if(dtype == "int"):
                    if positive_only:
                        # caution: could lead to overflow
                        f.write("%s\n" % (abs(int(tiled_COO.data[val]))))
                    else:
                        f.write("%s\n" % (int(tiled_COO.data[val])))
                else:   
                    f.write("%s\n" % (tiled_COO.data[val]))      

    return n_lists, d_list, crd_dict, pos_dict

def write_csf(COO, output_dir_path): 

    # The number of values in the tensor
    num_values = len(COO.data)
    n_dim = len(COO.coords)

    # Create the CSF representation for the tensor at each level
    crd_dict = {} 
    pos_dict = {}

    pos_ctr = np.ones(n_dim, dtype=int)
 
    for i in range(num_values):   
        propogate = 0; 
        for dim in range(n_dim):
            idx = dim
            if(i == 0): 
                crd_dict[idx] = [COO.coords[idx][i]]
                pos_dict[idx] = [0] 
            else:
                if(crd_dict[idx][-1] != COO.coords[idx][i]):
                    propogate = 1

                if(propogate == 1):
                    pos_ctr[idx] += 1
                    crd_dict[idx].append(COO.coords[idx][i])
                    if(idx != n_dim - 1):
                        pos_dict[idx + 1].append(pos_ctr[idx + 1])
                     
    for dim in range(n_dim):
        idx = dim
        if(idx == 0):
            pos_dict[idx].append(pos_ctr[idx])
        if(idx != n_dim - 1):
            pos_dict[idx + 1].append(pos_ctr[idx + 1])

    for dim in range(n_dim):
        crd_dict_path = output_dir_path + "/csf_crd" + str(dim + 1) + ".txt"
        with open(crd_dict_path, 'w+') as f:
            for item in crd_dict[dim]:
                f.write("%s\n" % item)
        pos_dict_path = output_dir_path + "/csf_pos" + str(dim + 1) + ".txt"
        with open(pos_dict_path, 'w+') as f:
            for item in pos_dict[dim]:
                f.write("%s\n" % item)
    
    d_list_path = output_dir_path + "/csf_vals" + ".txt"
    with open(d_list_path, 'w+') as f:
        for val in range(num_values):
            f.write("%s\n" % abs((COO.data[val])))

def write_to_tns(tensor, filename, one_based_indexing=False):
    """
    Writes a sparse.COO tensor to a .tns file.

    Parameters:
    - tensor: sparse.COO tensor to write.
    - filename: Name of the output .tns file.
    - one_based_indexing: If True, indices are incremented by 1 (MATLAB style).
    """
    coords = tensor.coords  # shape: (ndim, nnz)
    data = tensor.data      # shape: (nnz,)

    with open(filename, 'w') as f:
        for i in range(tensor.nnz):
            # Extract indices for the i-th non-zero element
            indices = coords[:, i]
            if one_based_indexing:
                indices += 1  # Convert to 1-based indexing if necessary
            # Prepare the line to write
            line = ' '.join(map(str, indices)) + ' ' + str(data[i])
            f.write(line + '\n')

def write_to_mtx_scipy(tensor, filename):
    """
    Writes a 2D sparse.COO tensor to a Matrix Market .mtx file using scipy.
    """
    if tensor.ndim != 2:
        raise ValueError("Tensor must be 2-dimensional to write to Matrix Market format.")

    # Convert sparse.COO to scipy.sparse.coo_matrix
    scipy_tensor = scipy.sparse.coo_matrix((tensor.data, tensor.coords), shape=tensor.shape)
    mmwrite(filename, scipy_tensor)

inputCacheSuiteSparse = InputCacheSuiteSparse()
inputCacheTensor = InputCacheTensor()

def process(tensor_type, input_path, output_dir_path, tensor_size, schedule_dict, format, gen_tensor, density, gold_check, positive_only, dtype, fill_diag):
    tensor = None
    cwd = os.getcwd()
    inputCache = None

    other_nonempty = True

    if tensor_type == "gen":
        # Generating a random tensor for testing purposes of pre-processing kernel 
        size = tuple(tensor_size[0])
        tensor = None
        # TODO: Parameterize this
        np.random.seed(0)
        if size[0] == '0': 
            if dtype == "int":
                # Generate a random integer
                tensor = np.random.randint(low=1, high=10)
            else:
                # Generate a random float
                tensor = np.random.uniform(low=1, high=10)
                if dtype == "bf16":
                    tensor = bfbin2float(float2bfbin(tensor))
        else: 
            if dtype == "int":
                value_cap = 10
                tensor = np.random.randint(low=1, high = value_cap / 2, size=size)
            else:
                value_cap = 10
                tensor = np.random.uniform(low=1, high = value_cap / 2, size=size)
                if dtype == "bf16":
                    for idx, val in np.ndenumerate(tensor):
                        tensor[idx] = bfbin2float(float2bfbin(val))
            # randomly negates 50% of the values
            negate_indices = np.random.choice(np.prod(tensor.shape), int(np.prod(tensor.shape) * 0.5), replace=False)
            tensor[np.unravel_index(negate_indices, tensor.shape)] *= -1
            
            # inject zeros according to the specified density
            num_zero = int(np.prod(tensor.shape) * (1 - density / 100))
            zero_indices = np.random.choice(np.prod(tensor.shape), num_zero, replace=False)
            tensor[np.unravel_index(zero_indices, tensor.shape)] = 0
            # tensor = scipy.sparse.coo_array(tensor)
            # tensor = sparse.COO(tensor)
    elif tensor_type == "ex":
        # Reading an extensor tensor for testing purposes of pre-processing kernel
        tensor = scipy.io.mmread(input_path)
    elif tensor_type == "ss":
        # Reading a SuiteSparse tensor for testing purposes of pre-processing kernel
        inputCache = inputCacheSuiteSparse
        tensor_path = os.path.join(SUITESPARSE_PATH, input_path + ".mtx")
        ss_tensor = SuiteSparseTensor(tensor_path)
        tensor = inputCache.load(ss_tensor, False)
    elif tensor_type == "fusion":
        # Reading a SuiteSparse tensor for testing purposes of pre-processing kernel
        inputCache = inputCacheSuiteSparse
        tensor_path = os.path.join("./exp_30_tensors/", input_path + ".mtx")
        ss_tensor = SuiteSparseTensor(tensor_path)
        tensor = inputCache.load(ss_tensor, False)
    elif tensor_type == "frostt":
        # Reading a FROSTT tensor for testing purposes of pre-processing kernel
        inputCache = inputCacheTensor
        tensor_path = os.path.join(FROSTT_PATH, input_path + ".tns")
        frostt_tensor = FrosttTensor(tensor_path)
        tensor = inputCache.load(frostt_tensor, False)
    elif tensor_type == "sparse_ml":
        inputCache = InputCacheSparseML()
        tensor_path = os.path.join(SPARSEML_PATH, input_path + ".npy")
        sparse_ml_tensor = SparseMLTensor(tensor_path)
        tensor = inputCache.load(sparse_ml_tensor, False)
    else:
       raise ValueError("This choice of 'tensor_type' is unreachable")

    if gen_tensor == "transpose":
        tensor = tensor.transpose()
    elif gen_tensor == "shift_dim2":
        shifted = ScipyTensorShifter().shiftLastMode(tensor)
        tensor = shifted
    elif gen_tensor == "shift_transpose_dim2": 
        shifted = ScipyTensorShifter().shiftLastMode(tensor)
        tensor = shifted.transpose()
    elif gen_tensor == "onyx_matmul": 
        shifted = ScipyTensorShifter().shiftLastMode(tensor)
        tensor = shifted.transpose()

        tensor = sparse.COO(tensor)
        num_values = len(tensor.data)

        tile_op_crd_list = np.zeros((2, num_values), dtype=int)
        tile_op_val_list = []

        subtile_size = tensor_size[-1]
        
        for idx in range(0, num_values):
            i = tensor.coords[0][idx]
            j = tensor.coords[1][idx]

            crd_i = i % subtile_size[0]
            crd_j = j % subtile_size[0]

            ii = i - crd_i + crd_j
            jj = j - crd_j + crd_i  

            tile_op_crd_list[0][idx] = ii 
            tile_op_crd_list[1][idx] = jj
            tile_op_val_list.append(tensor.data[idx])
        tensor = sparse.COO(tile_op_crd_list, tile_op_val_list)    
    elif gen_tensor == "onyx_matmul_rect": 
        shifted = ScipyTensorShifter().shiftLastMode(tensor)
        tensor = shifted.transpose()

        tensor = sparse.COO(tensor)
        num_values = len(tensor.data)

        tile_op_crd_list = np.zeros((2, num_values), dtype=int)
        tile_op_val_list = []
        
        for idx in range(0, num_values):
            i = tensor.coords[0][idx]
            j = tensor.coords[1][idx]

            crd_i = i%30
            crd_j = j%30

            ii = i - crd_i + crd_j
            jj = j - crd_j + crd_i  

            tile_op_crd_list[0][idx] = ii 
            tile_op_crd_list[1][idx] = jj
            tile_op_val_list.append(tensor.data[idx])
        tensor = sparse.COO(tile_op_crd_list, tile_op_val_list)                                
    elif gen_tensor == "shift_twice_dim2":
        shifted = ScipyTensorShifter().shiftLastMode(tensor)
        shifted2 = ScipyTensorShifter().shiftLastMode(shifted)
        tensor = shifted2
    elif gen_tensor == "gen_colvec_dim1":
        tensorName = input_path
        variant = "mode1"
        path = constructOtherVecKey(tensorName,variant)
        tensor_c_from_path = FrosttTensor(path)
        tensor_c = tensor_c_from_path.load().todense()
        # print("TENSOR SHAPE: ", tensor.shape)
        # print("TENSOR_C SHAPE: ", tensor_c.shape)
        #rows, cols = tensor.shape
        #tensor_c = scipy.sparse.random(cols, 1, data_rvs=np.ones).toarray().flatten()
        if other_nonempty: tensor_c[0] = 1
        tensor = tensor_c
    elif gen_tensor == "gen_rowvec_dim1":
        rows, cols = tensor.shape
        tensor_c = scipy.sparse.random(rows, 1, data_rvs=np.ones).toarray().flatten()
        if other_nonempty: tensor_c[0] = 1 
        tensor = tensor_c
    elif gen_tensor == "shift_dim3": 
        shifted = PydataTensorShifter().shiftLastMode(tensor)
        tensor = shifted
    elif gen_tensor == "tensor3_ttv":
        tensorName = input_path
        variant = "mode2"  
        path = constructOtherVecKey(tensorName, variant)
        tensor_c_loader = FrosttTensor(path)
        tensor_c = tensor_c_loader.load().todense()
        #size_i, size_j, size_k = tensor.shape  # i,j,k
        #tensor_c = scipy.sparse.random(size_k, 4, data_rvs=np.ones).toarray().flatten()
        if other_nonempty:
            tensor_c[0] = 1
        tensor = tensor_c   
    elif gen_tensor == "tensor3_ttm":
        tensorName = input_path
        variant = "mode2_ttm"
        path = constructOtherMatKey(tensorName, variant)
        matrix_c_loader = FrosttTensor(path)
        matrix_c = matrix_c_loader.load().todense()
        # size_i, size_j, size_l = tensor.shape  # i,j,k
        # print("OTHER SIZES: ", size_i, size_j, size_l)
        # # dimension_k = random.randint(min(tensor.shape), 10)
        # dimension_k = 3
        # tensor_c = scipy.sparse.random(dimension_k, size_l, density=0.25, data_rvs=np.ones).toarray()
        # tensor_c = scipy.sparse.random(dimension_k, size_l, data_rvs=np.ones).toarray().flatten()
        if other_nonempty:
            matrix_c[0] = 1
        tensor = matrix_c
    elif gen_tensor == "tensor3_mttkrp1":
        size_i, size_j, size_l = tensor.shape  
        tensorName = input_path
        variant = "mode1_mttkrp"
        path = constructOtherMatKey(tensorName, variant)
        matrix_c_loader = FrosttTensor(path)
        matrix_c = matrix_c_loader.load().todense()
        if other_nonempty:
            matrix_c[0] = 1
        tensor = matrix_c
    elif gen_tensor == "tensor3_mttkrp2":
        size_i, size_j, size_l = tensor.shape
        tensorName = input_path
        variant = "mode2_mttkrp"
        path = constructOtherMatKey(tensorName, variant)
        matrix_d_loader = FrosttTensor(path)
        matrix_d = matrix_d_loader.load().todense()
        # size_k = random.randint(min(tensor.shape), 10)
        # # C & D are dense according to TACO documentation
        # matrix_c = scipy.sparse.random(size_j, size_k, density=1, data_rvs=np.ones).toarray()
        # matrix_d = scipy.sparse.random(size_j, size_l, density=1, data_rvs=np.ones).toarray()
        if other_nonempty:
            matrix_d[0] = 1
        tensor = matrix_d
    elif gen_tensor != "0" and gen_tensor != "relu" and gen_tensor != "recip":
        raise NotImplementedError

    tensor = sparse.COO(tensor)

    if(fill_diag):

        subtile_size = tensor_size[-1]
        tensor_dim = len(subtile_size)        

        if(tensor_dim > 1): 
            
            subtile_dim = min(subtile_size[0], subtile_size[1])
            coords_0 = tensor.coords[0]
            coords_1 = tensor.coords[1]
            data     = tensor.data
            num_values = len(data)

            tile_dict = {}
           
            for id1 in range(0, num_values):
                id_key = ""

                tile_id1 = coords_0[id1] // subtile_size[0]
                tile_id2 = coords_1[id1] // subtile_size[1]

                id_key = str(tile_id1) + "." + str(tile_id2)

                if id_key not in tile_dict.keys():         
                    tile_dict[id_key] = 1
                    
                    for ii in range(0, subtile_dim):
                        glob_id1 = tile_id1 * subtile_size[0] + ii 
                        glob_id2 = tile_id2 * subtile_size[1] + ii 

                        is_present = False

                        if(glob_id1 in coords_0):
                            idx_glob_id1 = [idx for idx, value in enumerate(coords_0) if value == glob_id1]
                            for idx in idx_glob_id1:                             
                                if(coords_1[idx] == glob_id2): 
                                    is_present = True
                        
                        if not is_present: 
                            coords_0 = np.append(coords_0, [glob_id1])
                            coords_1 = np.append(coords_1, [glob_id2])
                            data = np.append(data, [0])

            tensor = sparse.COO([coords_0, coords_1], data)

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    if(gold_check == "d"):
        dense_tensor = tensor.todense()
        numpy_array = np.array(dense_tensor)
        out_path = output_dir_path + "/numpy_array" + ".npz"
        np.savez(out_path, array1 = numpy_array)
    elif(gold_check == "s"):
        size = tensor_size[0]
        write_csf(tensor, output_dir_path)
        if(input_path == "mtx"):
            write_to_mtx_scipy(tensor, output_dir_path + "/tensor.mtx")
        elif(input_path == "tns"):
            write_to_tns(tensor, output_dir_path + "/tensor.tns", True)        

    tile_size = tensor_size[1:]
    process_coo(tensor, tile_size, output_dir_path, format, schedule_dict, positive_only, dtype)
