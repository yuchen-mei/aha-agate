#ifndef DATA_PARSER_H
#define DATA_PARSER_H

#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <csignal>
#include <iomanip>
#include <bitset>
#include <cmath>
#include <algorithm>
#include <numeric>
#include "bf16_op.h"
#include "gen_lut.h"


using namespace std;

int build_vec(std::vector<int> &vec, std::string file_path);
int build_vec_val(std::vector<float> &vec, std::string file_path);
int mode_data_printer(std::ofstream &header_file, std::string tensor_name, std::string mode_name, std::vector<int> mode_0);
int val_data_printer(std::ofstream &header_file, std::string tensor_name, std::string mode_name, std::vector<float> mode_0, std::string dtype);
int extent_data_printer(std::ofstream &header_file, std::string tensor_name, std::string mode_name, std::vector<int> extents_mode_0, std::vector<int> map);
int lut_data_printer(std::ofstream &header_file, std::string lut_name);
int lut_extent_data_printer(std::ofstream &header_file, std::string lut_name);
int rtl_mode_data_printer(std::vector<int> mode_0, std::string output_path, std::string tensor_name, std::string mode_type, std::string mode_name, bool is_dense);
int rtl_vals_data_printer(std::vector<float> mode_0, std::string output_path, std::string tensor_name);
int rtl_lut_data_printer(std::string output_path, std::string lut_name);
int rtl_size_data_printer_1(std::string output_path, std::string tensor_name, int dim1);
int rtl_size_data_printer_2(std::string output_path, std::string tensor_name, int dim1, int dim2);
int rtl_size_data_printer_3(std::string output_path, std::string tensor_name, int dim1, int dim2, int dim3);
int rtl_dump_dtype(std::string output_path, std::string dtype);
int output_subtile_printer(float *op_vals, int output_subtile_size, int curr_subtile_num, ofstream &output_gold_file, std::string dtype, bool ap_gcheck, int op_cnt);
int subtile_paths_printer(const std::vector<std::string> &subtile_paths, const std::string &output_dir, const std::string &kernel_name, const int &batch_size);
int header_check_gold(ofstream &output_gold_file, int output_subtile_size, bool ap_gcheck);
int header_subtile_dim_decl(ofstream &header_file, int dim_id, int dim_size);
int codegen_check_gold_head(ofstream &output_gold_file, int max_run, int output_subtile_size, int tensor_dim, int unroll, std::string glb_bank_offset, std::string glb_tile_offset, std::vector<int> map1, bool ap_gcheck);
int codegen_check_gold_tail(ofstream &output_gold_file, int max_run, int tensor_dim, std::string type, bool ap_gcheck);
int codegen_check_gold_unroll_ifdef_open(ofstream &output_gold_file, int select, int val);
int codegen_check_gold_unroll_ifdef_close(ofstream &output_gold_file); 
int codegen_check_gold_outmap(ofstream &output_gold_file, std::string base_id, std::string tile_id, std::string glb_tile_offset);
int codegen_check_gold_outmap_unroll(ofstream &output_gold_file, std::string base_id, std::string tile_id, std::string glb_tile_offset);
int codegen_check_gold_unroll_ifdef_open(int select); 
int codegen_check_gold_ret(ofstream &output_gold_file, bool ap_gcheck); 
int header_meta_data(ofstream &header_file, std::string label, int max_run);
int codegen_check_gold_read_gdb_bin(ofstream &output_gold_file, std::string base_id, std::string tile_id, std::string glb_tile_offset, bool unroll);
std::vector<int> generate_range(int n); 
std::pair<std::vector<int>, std::vector<int>> partition_vec(const std::vector<int>& a);

#endif
