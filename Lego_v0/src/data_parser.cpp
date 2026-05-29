#include "data_parser.h"

int build_vec(std::vector<int> &vec, std::string file_path) {
    int val;

    ifstream input_file(file_path);   
	if (input_file.good()) {
		vec.clear();
		while(input_file >> val){
			vec.push_back(val);
		}	
	} else {
		throw std::runtime_error("Error: File not found: " + file_path);
	}

    return 0;
}

int build_vec_val(std::vector<float> &vec, std::string file_path) {
    float val;
    ifstream input_file(file_path);   
	if (input_file.good()) {
    	while(input_file >> setprecision(30) >> val){
			// FIXME: Temporary fix to avoid precision loss
			// TODO: Find a better way to set the digit precision
        	vec.push_back(val);
    	}
	} else {
		throw std::runtime_error("Error: File not found: " + file_path);
	}
    return 0;
}

int mode_data_printer(std::ofstream &header_file, std::string tensor_name, std::string mode_name, std::vector<int> mode_0){

	header_file << "const unsigned int app_tensor_" << tensor_name << "_mode_" << mode_name << "_data_size =  " << mode_0.size() << ";";
	header_file << "\n";		
	
	header_file << "uint16_t app_tensor_" << tensor_name << "_mode_" << mode_name << "_data[] " <<  "__attribute__((section(\".app_tensor_" <<  tensor_name << "_mode_" << mode_name << "_data\"))) = {";
	header_file << "\n";

	header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << mode_0[0];

	for(int i = 1; i < mode_0.size(); i++) {
		header_file << ", ";
		header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << mode_0[i];
	}
	header_file << "\n";
	header_file << "};"; 
	header_file << "\n";
	header_file << "\n";
	header_file << std::dec;

	return 0;
}

int val_data_printer(std::ofstream &header_file, std::string tensor_name, std::string mode_name, std::vector<float> mode_0, std::string dtype){

	header_file << "const unsigned int app_tensor_" << tensor_name << "_mode_" << mode_name << "_data_size =  " << mode_0.size() << ";";
	header_file << "\n";		
	
	header_file << "uint16_t app_tensor_" << tensor_name << "_mode_" << mode_name << "_data[] " <<  "__attribute__((section(\".app_tensor_" <<  tensor_name << "_mode_" << mode_name << "_data\"))) = {";
	header_file << "\n";

	header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << int(abs(mode_0[0]));
	int run_length = int(abs(mode_0[0]));

	if(dtype == "int"){
		for(int i = 1; i < mode_0.size(); i++) {
			header_file << ", ";
			header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << int(mode_0[i]);
		}
	} else if (dtype == "bf16"){
		for (int index = 1; index < mode_0.size();) {
			for (int i = 0; i < run_length; i++) {
				header_file << ", ";
				header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << float2bfbin(mode_0[index], true, false);
				index++;
			}
			if (index < mode_0.size()) {
				run_length = int(abs(mode_0[index]));
				header_file << ", ";
				header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << int(abs(mode_0[index]));
				index++;
			} else {
				break;
			}
		}
	}

	header_file << "\n";
	header_file << "};"; 
	header_file << "\n";
	header_file << "\n";
	header_file << std::dec;

	return 0;
}

int extent_data_printer(std::ofstream &header_file, std::string tensor_name, std::string mode_name, std::vector<int> extents_mode_0, std::vector<int> map){
    header_file << "const uint16_t tensor_" << tensor_name << "_mode_" << mode_name << "_extents" << "[" << 2 * map.size() << "] = {";
    header_file << extents_mode_0[2 * map[0]];
	header_file << ", "; 
	header_file << extents_mode_0[2 * map[0] + 1];
    for(int i = 1; i < map.size(); i++){
        header_file << ", "; 
		header_file << extents_mode_0[2 * map[i]];
		header_file << ", "; 
		header_file << extents_mode_0[2 * map[i] + 1];
	}
    header_file << "};";
    header_file << "\n";
    return 0;
}



int lut_data_printer(std::ofstream &header_file, std::string lut_name) {
	// generate lut values based on the specified lut name
	int lut_content[1024] = {0};
	if (lut_name == "exp") {
		int index = 0;
		for (int i = 0; i < 128; i ++) {
			lut_content[index] = bfbin2uint(float2bfbin(pow(2, float(i) / 128.0), false, true));
			index ++;
		}
		for (int i = -128; i < 0; i ++) {
			lut_content[index] = bfbin2uint(float2bfbin(pow(2, float(i) / 128.0), false, true));
			index ++;
		}
		for (int i = 256; i < 1024; i ++) {
			lut_content[i] = 0;
		}
	}

	// print the lut to the input script file

	header_file << "const unsigned int app_tensor_" << lut_name << "_mode_vals_data_size =  " << 1025 << ";";
	header_file << "\n";

	header_file << "uint16_t app_tensor_" << lut_name << "mode_vals_data[] " <<  "__attribute__((section(\".app_tensor_" <<  lut_name << "_mode_vals_data\"))) = {";
	header_file << "\n";

	header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << 1024;
	header_file << ", ";

	for (int i = 0; i < 1024; i ++) {
		header_file << "0x" << std::hex << std::setw(3) << std::setfill('0') << lut_content[i];
		if (i != 1023) {
			header_file << ", ";
		}
	}

	header_file << "\n";
	header_file << "};";
	header_file << std::dec;

	return 0;
}

int lut_extent_data_printer(std::ofstream &header_file, std::string lut_name) {
	header_file << "const int tensor_" << lut_name << "_mode_vals_extents[2] = {0, 1025};";
	header_file << "\n";

	return 0;
}

int rtl_mode_data_printer(std::vector<int> mode_0, std::string output_path, std::string tensor_name, std::string mode_type, std::string mode_name, bool is_dense) {

	// for dimension, the regression is only expecting seg
	if (mode_type == "crd" && is_dense) {
		return 0;
	}

	std::string output_file_name = output_path + "/tensor_" + tensor_name + "_mode_" + mode_name + "_" + mode_type;
	ofstream output_file(output_file_name.c_str());
	if (is_dense) {
		// for dense dimension, dump the (0, dim_size) pair
		// since the matrix is completely dense, data at index 1 in the segment array 
		// will be the size of the dimension
		output_file << "0\n";
		output_file <<  mode_0[1] << "\n";
	} else {
		for (int pA = 0; pA < mode_0.size(); pA++) {
			output_file << mode_0[pA];
			output_file << "\n";
		}
	}

	output_file.close();

	return 0;
}

int rtl_vals_data_printer(std::vector<float> mode_0, std::string output_path, std::string tensor_name) {

	std::string output_file_name = output_path + "/tensor_" + tensor_name + "_mode_vals";
	ofstream output_file(output_file_name.c_str());

	for (int pA = 0; pA < mode_0.size(); pA++) {
		// FIXME: Temporary fix to avoid precision loss
		// TODO: Find a better way to set the digit precision
		output_file << std::fixed << setprecision(30) << mode_0[pA];
		output_file << "\n";
	}

	output_file.close();
	// TODO: Store integer values to file if dtype is integer 
	// Propogate data type 

	return 0;
}

int rtl_lut_data_printer(std::string output_path, std::string lut_name) {
	// generate lut values based on the specified lut name
	std::vector<float> lut_content;
	if (lut_name == "exp") {
		lut_content = gen_exp_lut();
	} else if (lut_name == "recip") {
		lut_content = gen_div_lut();
		// hack to make the name of the file matches that expected by the metamapper
		lut_name = "div";
	}
	
	// the metamapper mapped lut will be looking for a file with the name "tensor_fp_<operation>_mode_vals"
	std::string output_file_name = output_path + "/tensor_fp_" + lut_name + "_mode_vals";
	ofstream output_file(output_file_name.c_str());

	for (int i = 0; i < 1024; i ++) {
		// FIXME: Temporary fix to avoid precision loss
		// TODO: Find a better way to set the digit precision
		output_file << std::fixed << setprecision(30) << lut_content[i];
		output_file << "\n";
	}

	// TODO: Store integer values to file if dtype is integer 
	// Propogate data type 

	return 0;
}

int rtl_size_data_printer_1(std::string output_path, std::string tensor_name, int dim1) {

	std::string output_file_name = output_path + "/tensor_" + tensor_name + "_mode_shape";
	ofstream output_file(output_file_name.c_str());

	output_file << dim1 << "\n";

	return 0;
}

int rtl_size_data_printer_2(std::string output_path, std::string tensor_name, int dim1, int dim2) {

	std::string output_file_name = output_path + "/tensor_" + tensor_name + "_mode_shape";
	ofstream output_file(output_file_name.c_str());

	output_file << dim1 << "\n";
	output_file << dim2 << "\n";

	return 0;
}

int rtl_size_data_printer_3(std::string output_path, std::string tensor_name, int dim1, int dim2, int dim3) {
	
	std::string output_file_name = output_path + "/tensor_" + tensor_name + "_mode_shape";
	ofstream output_file(output_file_name.c_str());

	output_file << dim1 << "\n";
	output_file << dim2 << "\n";
	output_file << dim3 << "\n";

	return 0;
}

int rtl_dump_dtype(std::string output_path, std::string dtype) {
	std::string output_file_name = output_path + "/dtype";
	ofstream output_file(output_file_name.c_str());

	output_file << dtype << "\n";

	return 0;
}

int output_subtile_printer(float *op_vals, int output_subtile_size, int curr_subtile_num, ofstream &output_gold_file, std::string dtype, bool ap_gcheck, int op_cnt) {

	std::string type_16_bit;
	if(!ap_gcheck){
		type_16_bit = "uint16_t";
	}

	if(!ap_gcheck){
		output_gold_file << "const " << type_16_bit << " gold_" << curr_subtile_num << "_[" << output_subtile_size << "] = {";
	}


    if(dtype == "int"){
    	for (int pA = 0; pA < output_subtile_size; pA++) {
        	output_gold_file << int(op_vals[pA]);
        	if(pA != output_subtile_size - 1){
				if(ap_gcheck){
					output_gold_file << "\n"; 
				}
				else{
            		output_gold_file << ", ";
				}
        	}
    	} 
		if(!ap_gcheck){
    		output_gold_file << "};\n";
		}
	} 
    
    if (dtype == "bf16"){
        for (int pA = 0; pA < output_subtile_size; pA++) {
            output_gold_file << float2bfbin(op_vals[pA], false, false);
            if (pA != output_subtile_size - 1){
				if (ap_gcheck) {
					output_gold_file << "\n";
				}
				else {
					output_gold_file << ", ";
				}
            }
        }
		if (!ap_gcheck) {
        	output_gold_file << "};\n";
		}
    }

	// write the total number of ops required to compute this tile
	if (ap_gcheck) {
		output_gold_file << "\n" << op_cnt << "\n";
	}

    return 0;
}

int subtile_paths_printer(const std::vector<std::string> &subtile_paths,
						  const std::string &output_dir,
						  const std::string &kernel_name, 
						  const int &batch_size) {
	
	int batch_idx = 0;
	for (int i = 0; i < subtile_paths.size(); i += batch_size) {
		std::string subtile_paths_file_path = output_dir + "/" + kernel_name + "/subtile_paths_" + std::to_string(batch_idx) + ".toml";
		std::ofstream subtile_paths_file;
		subtile_paths_file.open(subtile_paths_file_path, std::ios::out);
		
		if (!subtile_paths_file) {
			std::cerr << "Error: Cannot open file " << subtile_paths_file_path << "for writing" << std::endl;
			return 1;
		}

		// prefix fields required by comal
		subtile_paths_file << "[sam_config]" << "\n";
		subtile_paths_file << "name = \"" << kernel_name << "\"\n";
		subtile_paths_file << "sam_path = [ \n";

		std::string path_prefix = "output/" + kernel_name + "/";

		for (int j = 0; j < batch_size && i+j < subtile_paths.size(); j++) {
			std::string subtile_path = subtile_paths[i+j];
			std::string::size_type i = subtile_path.find(path_prefix);
			if (i != std::string::npos) {
				subtile_path.erase(i, path_prefix.length());
			}
			subtile_paths_file << "    \"" << subtile_path << "\",\n";
		}

		subtile_paths_file << "    ]";
		subtile_paths_file.close();
		batch_idx++;
	}

	return 0;
}

int header_meta_data(ofstream &header_file, std::string label, int max_run){
	header_file << "const int runs" << label << " = " << max_run << ";" << "\n";
	return 0; 
} 

int header_check_gold(ofstream &output_gold_file, int output_subtile_size, bool ap_gcheck){
	output_gold_file << "#define AHASOC_CGRA_DATA_BASE    (0x20400000UL)  /*!< (CGRA DATA ) Base Address */" << "\n";

	output_gold_file << "\n"; 

	if (ap_gcheck) {
		output_gold_file << "#include <sstream>" << "\n";
		output_gold_file << "#include <string>" << "\n";
		output_gold_file << "#include <iomanip>" << "\n";
		output_gold_file << "#include <iostream>" << "\n";
		output_gold_file << "#include <fstream>" << "\n";
		output_gold_file << "#include <vector>" << "\n";
		output_gold_file << "#include <cassert>" << "\n";
		output_gold_file << "std::vector<unsigned short> check_0_ = {0";
	} else {
		output_gold_file << "uint16_t check_0_[" << output_subtile_size << "] = {0";
	}

	for(int i = 0; i < output_subtile_size - 1; i++){
		output_gold_file << ", 0";
	}

	output_gold_file << "};" << "\n";
	output_gold_file << "\n"; 

	if (ap_gcheck) {
		output_gold_file << "int total_op_cnt = 0;\n";
	}

	return 0;
}

int header_subtile_dim_decl(ofstream &header_file, int dim_id, int dim_size){
	header_file << "#define STILE_DIM" << dim_id << " " << dim_size << "\n";
	return 0;
}


int codegen_check_gold_head(ofstream &output_gold_file, int max_run, int output_subtile_size, int tensor_dim, int unroll, std::string glb_bank_offset, std::string glb_tile_offset, std::vector<int> map1, bool ap_gcheck){

	// different data types depending on whether gold check happens on ap or cp
	std::string type_32_bit;
	std::string type_16_bit;
	std::string type_8_bit;
	if (ap_gcheck) {
		type_32_bit = "unsigned int";
		type_16_bit = "unsigned short";
		type_8_bit = "unsigned short";
	} else {
		type_32_bit = "uint32_t";
		type_16_bit = "uint16_t";
		type_8_bit = "uint8_t";
	}

	if(!ap_gcheck && (unroll == 2)){
		output_gold_file << type_8_bit << " map[" << max_run << "];\n";
		output_gold_file << "\n"; 
	}
	output_gold_file << "\n"; 

	// define the main gold check funtion
	if (ap_gcheck) {
		output_gold_file << "int main() {" << "\n";
	} else {
		output_gold_file << "uint16_t check_gold_data(){" << "\n";
	}

	output_gold_file << "\n"; 

	output_gold_file << "    " << type_16_bit << " size; " << "\n";
	output_gold_file << "    " << type_16_bit << " err = 0;" << "\n";

	// define index variables to keep track of the idx of the current output tile

	for(int i = 0; i < tensor_dim; i++){
		output_gold_file << "    " << type_16_bit << " mode" << i << "_idx = 0;" << "\n";
	}
	output_gold_file << "    " << type_16_bit << " vals_idx = 0;" << "\n";	

	if(unroll){
		for(int i = 0; i < tensor_dim; i++){
			output_gold_file << "    " << type_16_bit << " mode" << i << "_idx_unroll = 0;" << "\n";
		}
		output_gold_file << "    " << type_16_bit << " vals_idx_unroll = 0;" << "\n";	
	}

	output_gold_file << "\n"; 
	output_gold_file << "    const " << type_32_bit << " read_start_addr = " << glb_bank_offset << ";" << "\n";;

	output_gold_file << "\n";
	output_gold_file << "    for(" << type_16_bit << " run = 0; run < " << max_run << "; run++){" << "\n";
	output_gold_file << "\n"; 
	if(ap_gcheck){
		output_gold_file << "        " << type_16_bit << " gold_num;" << "\n";
	}
	else{
		output_gold_file << "        " << type_16_bit << " *gold_ptr;" << "\n";
	}
	
	output_gold_file << "        " << type_16_bit << "* check_ptr;" << "\n";
	output_gold_file << "        switch(run){" << "\n";

	for(int i = 0; i < map1.size(); i++){
		output_gold_file << "            case " << i << ":" << "\n";
		if(ap_gcheck) {
			output_gold_file << "                gold_num = " << map1[i] << ";" << "\n";
			output_gold_file << "                check_ptr = check_0_.data();" << "\n";
		}
		else{
			output_gold_file << "                gold_ptr = gold_" << map1[i] << "_;" << "\n";
			output_gold_file << "                check_ptr = check_0_;" << "\n";
		}
		
		output_gold_file << "                break;" << "\n";
	}

	output_gold_file << "            default:" << "\n";
	output_gold_file << "                break;" << "\n";
	output_gold_file << "        }\n"; 
	output_gold_file << "\n"; 

	if(ap_gcheck){
		output_gold_file << "        std::vector<unsigned short> gold_ptr;\n"; 
		output_gold_file << "        std::string file_path = std::to_string(gold_num) + \".txt\";\n";
		output_gold_file << "        int val;\n";
		output_gold_file << "        std::ifstream input_file(file_path);\n";
		output_gold_file << "        if (input_file.good()) {\n";
		output_gold_file << "            gold_ptr.clear();\n";
		output_gold_file << "            for (int i = 0; i < " << output_subtile_size << "; i++) {\n";
		output_gold_file << "                input_file >> val;\n";
		output_gold_file << "                gold_ptr.push_back(val);\n";
		output_gold_file << "            }\n";
		output_gold_file << "            int op_cnt = 0;";
		output_gold_file << "            input_file >> op_cnt;\n";
		output_gold_file << "            total_op_cnt += op_cnt;\n";
		output_gold_file << "        } else {\n";
		output_gold_file << "            throw std::runtime_error(\"Error: File not found: \" + file_path);\n";
		output_gold_file << "        }\n";
	}


	if(ap_gcheck && (unroll == 2)){
		output_gold_file << "    unsigned int map_base_addr = AHASOC_CGRA_DATA_BASE + read_start_addr + " << "6" << " * " << glb_tile_offset << ";" << "\n";
		output_gold_file << "    std::stringstream ss_map_base;\n";
		output_gold_file << "    ss_map_base << std::hex << map_base_addr;\n";
		output_gold_file << "    std::string map_base_filename = ss_map_base.str() + \".bin\";\n";
		output_gold_file << "    std::ifstream map_base_file(map_base_filename, std::ios::binary);\n";
		output_gold_file << "    int map_base_len = 0;\n";
		output_gold_file << "    map_base_file.seekg (0, std::ios::end);\n";
		output_gold_file << "    map_base_len = map_base_file.tellg();\n";
		output_gold_file << "    map_base_file.seekg (0, std::ios::beg);\n";
		output_gold_file << "    std::vector<unsigned short> map(map_base_len);\n";
		output_gold_file << "    map_base_file.read((char *) &map[0], map_base_len);\n";
		output_gold_file << "    map_base_file.close();\n";
		output_gold_file << "\n";
	}

	return 0;
} 

int codegen_check_gold_unroll_ifdef_open(ofstream &output_gold_file, int select, int val){

	if(select == 0){
		output_gold_file << "        if(run % 1 == 0){" << "\n";
	}

	if(select == 1){
		output_gold_file << "        if(run < " << val << "){" << "\n"; 
	}

	if(select == 10){
		output_gold_file << "        if(map[run] == 0){" << "\n"; 
	}

	if(select == 2){
		output_gold_file << "        else{" << "\n"; 
	}

	return 0; 
}

int codegen_check_gold_outmap(ofstream &output_gold_file, std::string base_id, std::string tile_id, std::string glb_tile_offset){
	output_gold_file << "        uint16_t * read_base_" << base_id << " = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + " << tile_id << " * " << glb_tile_offset << ");" << "\n";
	return 0; 
}

int codegen_check_gold_read_gdb_bin(ofstream &output_gold_file, std::string base_id, std::string tile_id, std::string glb_tile_offset, bool unroll){
	if(unroll)
		output_gold_file << "        unsigned int read_base_" << base_id << "_addr = AHASOC_CGRA_DATA_BASE + read_start_addr + " << tile_id << " * " << glb_tile_offset << " + " << glb_tile_offset <<  " * 8;" << "\n";
	else
		output_gold_file << "        unsigned int read_base_" << base_id << "_addr = AHASOC_CGRA_DATA_BASE + read_start_addr + " << tile_id << " * " << glb_tile_offset << ";" << "\n";
	output_gold_file << "        std::stringstream ss_read_base_" << base_id << ";\n";
	output_gold_file << "        ss_read_base_" << base_id << " << std::hex << read_base_" << base_id << "_addr;\n";
	output_gold_file << "        std::string read_base_" << base_id << "_filename = ss_read_base_" << base_id << ".str() + \".bin\";\n";
	output_gold_file << "        std::ifstream read_base_" << base_id << "_file(read_base_" << base_id << "_filename, std::ios::binary);\n";
	output_gold_file << "        if (!read_base_" << base_id << "_file) {\n";
	output_gold_file << "            assert(false && \"Error: Cannot read binary file\");\n";
	output_gold_file << "        }\n";
	output_gold_file << "        int read_base_" << base_id << "_len = 0;\n";
	output_gold_file << "        read_base_" << base_id << "_file.seekg (0, std::ios::end);\n";
	output_gold_file << "        read_base_" << base_id << "_len = read_base_" << base_id << "_file.tellg();\n";
	output_gold_file << "        read_base_" << base_id << "_file.seekg (0, std::ios::beg);\n";
	output_gold_file << "        std::vector<unsigned short> read_base_" << base_id << "(read_base_" << base_id << "_len);\n";
	output_gold_file << "        read_base_" << base_id << "_file.read((char *) &read_base_" << base_id << "[0], read_base_" << base_id << "_len);\n";
	output_gold_file << " 	     read_base_" << base_id << "_file.close();\n";
	output_gold_file << "\n";
	return 0; 
}

int codegen_check_gold_outmap_unroll(ofstream &output_gold_file, std::string base_id, std::string tile_id, std::string glb_tile_offset){
	output_gold_file << "        uint16_t * read_base_" << base_id << " = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + " << tile_id << " * " << glb_tile_offset << " + " << glb_tile_offset <<  " * 8);" << "\n";
	return 0; 
}

int codegen_check_gold_tail(ofstream &output_gold_file, int max_run, int tensor_dim, std::string type, bool ap_gcheck){

	std::string type_16_bit;
	if (ap_gcheck) {
		type_16_bit = "unsigned short";
	} else {
		type_16_bit = "uint16_t";
	}
	
	
	if(tensor_dim > 0) {
		output_gold_file << "\n"; 
		output_gold_file << "            size = read_base_0[mode0_idx" << type << "];" << "\n";
		output_gold_file << "            " << type_16_bit << " mode0_size = size + 1 + read_base_0[mode0_idx" << type << " + size + 1] + 1;" << "\n";
		output_gold_file << "            " << type_16_bit << " mode0_stream_size = read_base_0[mode0_idx" << type << " + size + 1];" << "\n";
		output_gold_file << "            " << type_16_bit << " mode0_base = size + 1 + 1;" << "\n";

		for(int i = 1; i < tensor_dim; i++){
			output_gold_file << "\n"; 
			output_gold_file << "            size = read_base_" << i << "[mode" << i << "_idx" << type << "];" << "\n";
			output_gold_file << "            " << type_16_bit << " mode" << i << "_base = size + 1 + 1;" << "\n";
			output_gold_file << "            " << type_16_bit << " mode" << i << "_size = size + 1 + read_base_" << i << "[mode" << i << "_idx" << type << " + size + 1] + 1;" << "\n";
		}

		output_gold_file << "            " << type_16_bit << " vals_size = read_base_" << tensor_dim << "[vals_idx" << type <<"] + 1;" << "\n";

		output_gold_file << "\n"; 
		output_gold_file << "            " << type_16_bit << " x0;" << "\n";

		for(int i = 1; i < tensor_dim; i++){
			output_gold_file << "            " << type_16_bit << " x" << i << ";" << "\n";
			output_gold_file << "            " << type_16_bit << " x" << i << "_dim;" << "\n";
			output_gold_file << "            " << type_16_bit << " x" << i << "_idx = 0;" << "\n";
		}

		output_gold_file << "\n"; 

		for(int i = 0; i < tensor_dim; i++){
			output_gold_file << "            for(" << type_16_bit << " i" << i << " = 0; i" << i << " < STILE_DIM" << i <<  "; i" << i << "++){" << "\n";
			for(int j = 0; j < i + 1; j++){
				output_gold_file << "    ";
			}
		}

		std::string id; 
		std::string id_x; 

		id = ""; 

		for(int i = 0; i < tensor_dim; i++){
			id += "i" + std::to_string(i);
			for(int j = i + 1; j < tensor_dim; j++){
				id += " * STILE_DIM" + std::to_string(j);
			}
			if(i != tensor_dim - 1){
				id += " + ";
			}
		}

		output_gold_file << "            check_ptr[" << id << "] = 0;" << "\n";

		for(int i = 0; i < tensor_dim; i++){
			for(int j = 0; j < tensor_dim - i; j++){
				output_gold_file << "    "; 
			}
			output_gold_file << "        }" << "\n";
		}

		output_gold_file << "\n"; 

		id_x = "";
		for(int i = 0; i < tensor_dim; i++){
			id_x += "x" + std::to_string(i);
			for(int j = i + 1; j < tensor_dim; j++){
				id_x += " * STILE_DIM" + std::to_string(j);
			}
			if(i != tensor_dim - 1){
				id_x += " + ";
			}
		}

		int i  = 0;
		output_gold_file << "            for(" << type_16_bit << " i" << i << " = 0; i" << i << " < mode" << i << "_stream_size; i" << i << "++){" << "\n";
		output_gold_file << "                x" << i << " = read_base_" << i << "[mode" << i << "_idx" << type << "  + mode" << i << "_base + i" << i << "];" << "\n";

		if(tensor_dim > 1) {
			i++;
			output_gold_file << "                x" << i << "_dim = read_base_" << i << "[mode" << i << "_idx" << type <<"  + i" << i - 1 << " + 2] - read_base_" << i << "[mode" << i << "_idx" << type <<"  + i" << i - 1 << " + 1];" << "\n";

			for(int i = 1; i < tensor_dim; i++){
				for(int j = 0; j < i; j++){
					output_gold_file << "    ";
				}
				output_gold_file << "            for(" << type_16_bit << " i" << i << " = 0; i" << i << " < x" << i << "_dim; i" << i << "++){" << "\n";
				for(int j = 0; j < i; j++){
					output_gold_file << "    ";
				}
				output_gold_file << "                x" << i << " = read_base_" << i << "[mode" << i << "_idx" << type <<" + mode" << i << "_base + x" << i << "_idx + i" << i << "];" << "\n";
				if(i == tensor_dim - 1){
					for(int j = 0; j < i; j++){
						output_gold_file << "    ";
					}
					output_gold_file << "                check_ptr[" << id_x << "] = read_base_" << tensor_dim << "[vals_idx" << type <<" + x" << i << "_idx + " << "i" << i << " + 1];" << "\n";
				}
				else{
					int j = i + 1; 
					for(int k = 0; k < i; k++){
						output_gold_file << "    ";
					}
					output_gold_file << "                x" << j << "_dim = read_base_" << j << "[mode" << j << "_idx" << type <<"  + i" << j - 1 << " + 2] - read_base_" << j << "[mode" << j << "_idx" << type <<" + i" << j - 1 << " + 1];" << "\n";
				}
			}
		}
		else{
			output_gold_file << "                check_ptr[" << id_x << "] = read_base_" << tensor_dim << "[vals_idx" << type <<" + " << "i" << i << " + 1];\n";
		}

		for(int i = tensor_dim - 1; i > 0; i--){
			for(int j = 0; j < i; j++){
				output_gold_file << "    "; 
			}
			output_gold_file << "            }" << "\n";
			for(int j = 0; j < i; j++){
				output_gold_file << "    "; 
			}
			output_gold_file << "            x" << i << "_idx += x" << i << "_dim;" << "\n";
		}

		output_gold_file << "            }" << "\n";
		output_gold_file << "\n";

		for(int i = 0; i < tensor_dim; i++){
			output_gold_file << "            for(" << type_16_bit << " i" << i << " = 0; i" << i << " < STILE_DIM" << i <<  "; i" << i << "++){" << "\n";
			for(int j = 0; j < i + 1; j++){
				output_gold_file << "    "; 
			}
		}

		output_gold_file << "            if(check_ptr[" << id << "] != gold_ptr[" << id << "]){" << "\n";

		for(int j = 0; j < tensor_dim; j++){
			output_gold_file << "    ";
		}
		if (ap_gcheck) {
			output_gold_file << "                std::cout << \"error! tile: \" << run << \", ";
			for (int i = 0; i < tensor_dim; i++) {
				output_gold_file << "i" << i << ": \" << i" << i << " << \" ";
			}
			output_gold_file << "gold_ptr:\" << gold_ptr[" << id << "] << \" check_ptr:\" << check_ptr[" << id << "] << std::endl;\n";
		} else {
			output_gold_file << "                trace_printf(\"error! tile: %d, "; 
			for(int i = 0; i < tensor_dim; i++){
				output_gold_file << "i" << i << ": %d ";
			}
			output_gold_file << "gold_ptr:%d check_ptr:%d\\n\", run, ";
			for(int i = 0; i < tensor_dim; i++){
				output_gold_file << "i" << i << ", ";
			}

			output_gold_file << "gold_ptr[" << id << "], check_ptr[" << id << "]);" << "\n";
		}
		
		for(int j = 0; j < tensor_dim; j++){
			output_gold_file << "    ";
		}
		output_gold_file << "                err++;" << "\n";

		for(int i = 0; i < tensor_dim + 1; i++){
			for(int j = 0; j < tensor_dim - i; j++){
				output_gold_file << "    ";
			}
			output_gold_file << "            }" << "\n";
		}

		for(int i = 0; i < tensor_dim; i++){
			output_gold_file << "            mode" << i << "_idx" << type <<" += mode" << i << "_size;" << "\n";
		}

		output_gold_file << "            vals_idx" << type <<" += vals_size;" << "\n";
		output_gold_file << "        }" << "\n";
	}
	else{
		output_gold_file << "            " << type_16_bit << " vals_size = read_base_0[vals_idx" << type <<"] + 1;" << "\n";
		output_gold_file << "            if(read_base_0[vals_idx" << type <<" + 1] != gold_ptr[0]){" << "\n"; 
		if (ap_gcheck) {
			output_gold_file << "                std::cout << \"error! tile: \" << run << \", ";
			output_gold_file << "gold_ptr:\" << gold_ptr[0] << \" check_ptr:\" << read_base_0[vals_idx" << type << " + 1] << std::endl;\n";
        }
        else {
		    output_gold_file << "                trace_printf(\"error! tile: %d, gold_ptr:%d check_ptr:%d\\n\", run, gold_ptr[0], read_base_0[vals_idx" << type <<"  + 1]);" << "\n"; 
        }
		output_gold_file << "                err++;" << "\n";
		output_gold_file << "            }" << "\n";
		output_gold_file << "            vals_idx" << type <<" += vals_size;" << "\n";
		output_gold_file << "        }" << "\n";
	}
	output_gold_file << "\n";

	return 0;
}
int codegen_check_gold_ret(ofstream &output_gold_file, bool ap_gcheck){
	output_gold_file << "    }\n";
	if (ap_gcheck) {
		output_gold_file << "    std::cout << \"err: \" << err << std::endl;\n";
		output_gold_file << "    std::cout << \"total_op_cnt: \" << total_op_cnt << std::endl;\n";
	}

	output_gold_file << "    return err;\n";
	
	output_gold_file << "}\n";
	return 0;
}

std::vector<int> generate_range(int n) {
    std::vector<int> range(n);  // Create a vector of size n
    std::iota(range.begin(), range.end(), 0); // Fill with values from 0 to n-1
    return range;
}

std::pair<std::vector<int>, std::vector<int>> partition_vec(const std::vector<int>& a) {
    std::vector<int> indices(a.size());
    std::iota(indices.begin(), indices.end(), 0); // Create vector with indices [0, 1, 2, ..., a.size()-1]

    // Sort indices based on the values in `a`, largest first (greedy approach)
    std::sort(indices.begin(), indices.end(), [&](int i, int j) {
        return a[i] > a[j];
    });

    std::vector<int> b1, b2;
    int sum_b1 = 0, sum_b2 = 0;

    // Greedily assign elements to b1 or b2 based on the current sums
    for (int idx : indices) {
        if (sum_b1 <= sum_b2) {
            b1.push_back(idx);
            sum_b1 += a[idx];
        } else {
            b2.push_back(idx);
            sum_b2 += a[idx];
        }
    }

    return {b1, b2};
}
