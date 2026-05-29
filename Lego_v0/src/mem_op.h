#ifndef MEM_OP_H
#define MEM_OP_H

#include "data_def.h"
#include <fstream>
#include <iostream>
#include <string>
#include <iomanip>

using namespace std;

tile0 tensor_mem_op_0(int **tensor_op);
tile1 tensor_mem_op_1(int **tensor_op, int index);
tile2 tensor_mem_op_2(int **tensor_op, int index);
tile3 tensor_mem_op_3(int **tensor_op, int index);
subtile0 tile_mem_op_0(tile0 tile_op);
subtile1 tile_mem_op_1(tile1 tile_op, int index);
subtile2 tile_mem_op_2(tile2 tile_op, int index);
subtile3 tile_mem_op_3(tile3 tile_op, int index);
cg_subtile1 cg_tile_mem_op_1(cg_subtile1 cg_subtile_op, int **store_subtile_op, subtile1 subtile_op, int id_store_op); 
cg_subtile2 cg_tile_mem_op_2(cg_subtile2 cg_subtile_op, int **store_subtile_op, subtile2 subtile_op, int id_store_op);
cg_subtile3 cg_tile_mem_op_3(cg_subtile3 cg_subtile_op, int **store_subtile_op, subtile3 subtile_op, int id_store_op); 
cg_extents1 build_extents_1(cg_extents1 op_extents, int **store_subtile_op, int id_store_op);
cg_extents2 build_extents_2(cg_extents2 op_extents, int **store_subtile_op, int id_store_op);
cg_extents3 build_extents_3(cg_extents3 op_extents, int **store_subtile_op, int id_store_op);
int rtl_output_subtile_printer(float *op_vals, int output_subtile_size, int curr_subtile_num, ofstream &output_gold_file);
int rtl_subtile2_print(subtile2 subtile_op, std::string output_path, std::string mode_name, int dim1, int dim2);
tile0 tensor_zero_op_0(tile0 tile_op);
tile1 tensor_zero_op_1(tile1 tile_op);
tile2 tensor_zero_op_2(tile2 tile_op);
tile3 tensor_zero_op_3(tile3 tile_op);
subtile0 tile_zero_op_0(subtile0 subtile_op);
subtile1 tile_zero_op_1(subtile1 subtile_op);
subtile2 tile_zero_op_2(subtile2 subtile_op);
subtile3 tile_zero_op_3(subtile3 subtile_op);
cg_subtile1 cg_tile_zero_op_1(int **store_subtile_op, cg_subtile1 cg_subtile_op, int id_store_op);
cg_subtile2 cg_tile_zero_op_2(int **store_subtile_op, cg_subtile2 cg_subtile_op, int id_store_op);
cg_subtile3 cg_tile_zero_op_3(int **store_subtile_op, cg_subtile3 cg_subtile_op, int id_store_op);
subtile1 process_csf_1(subtile1 subtile_op, int dim1);
subtile2 process_csf_2(subtile2 subtile_op, int dim1, int dim2);
subtile3 process_csf_3(subtile3 subtile_op, int dim1, int dim2, int dim3);
#endif