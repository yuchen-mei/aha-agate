def main_gen_c_lib_include(file):

    file.write("#include <stdio.h>\n")
    file.write("#include <stdlib.h>\n")
    file.write("#include \"diag/trace.h\"\n")
    file.write("\n")

def main_app_header_include(file, app_name, gcheck, ap_gcheck):

    file.write("#include \"" + app_name + "_script.h\"\n")
    file.write("#include \"" + app_name + "_input_script.h\"\n")
    file.write("#include \"" + app_name + "_unrolling.h\"\n")
    file.write("#include \"" + app_name + "_reg_write.h\"\n")
    if(gcheck and not ap_gcheck):
        file.write("#include \"" + app_name + "_gold.h\"\n")
    file.write("\n")

def main_gen_soc_lib_include(file):
    file.write("#include \"amberm3vx_hal.h\"\n")
    file.write("#include \"glb.h\"\n")
    file.write("#include \"glc.h\"\n")
    file.write("#include \"memory.h\"\n")
    file.write("#include \"define.h\"\n")
    file.write("\n")

def main_block_1(file, unroll, debug):
    
    file.write("HAL_PtfmCtrl_t PtfmCtl;\n")
    file.write("\n")
    file.write("int main(int argc, char* argv[])\n")
    file.write("{\n")
    file.write("    HAL_UNUSED(argc);\n")
    file.write("    HAL_UNUSED(argv);\n")
    file.write("\n")
    file.write("    // Send a greeting to the trace device\n")
    file.write("    int status = HAL_PtfmCtrl_Initialize( & PtfmCtl);\n")
    if(debug):
        file.write("    trace_printf(\"Status \\n\");\n")
    else: 
        file.write("    // trace_printf(\"Status \\n\");\n")
    file.write("\n")
    file.write("    u32 cgra_mask = (1 << AHASOC_PCTRL_CGRA_Pos);\n")
    file.write("    u32 sys_mask = (1 << AHASOC_PCTRL_SYS_Pos);\n")
    file.write("\n")
    file.write("    // Slower clocks for configuration\n")
    file.write("    status = HAL_PtfmCtrl_SelectClock( & PtfmCtl, cgra_mask, 0); \n")
    file.write("    status = HAL_PtfmCtrl_SelectClock( & PtfmCtl, sys_mask, 3); \n")
    file.write("    status = HAL_PtfmCtrl_DisableCG( & PtfmCtl, cgra_mask);\n")
    file.write("    status = HAL_PtfmCtrl_ClearReset( & PtfmCtl, cgra_mask);\n")
    file.write("\n")
    file.write("    HAL_Cgra_Glc_WriteReg(GLC_CGRA_STALL_R, 0xFFFF);\n")
    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"Config App\\n\\n\");\n")
    else: 
        file.write("    // trace_printf(\"Config App\\n\\n\");\n")        
    file.write("\n")
    file.write("    for (int config = 0; config < app_size; config++){\n")
    file.write("        HAL_Cgra_Tile_WriteReg(app_addrs_script[config], app_datas_script[config]);\n")
    file.write("    }\n")

    if(unroll != "0"): 
        file.write("    for (int config = 0; config < app_size; config++){\n")
        file.write("        uint32_t addr = app_addrs_script[config];\n")
        file.write("	    uint32_t addr_shifted = (addr & 0xFFFF00FF) | ((((addr & 0x0000FF00) >> 8) + 16) << 8);\n")
        file.write("        HAL_Cgra_Tile_WriteReg(addr_shifted, app_datas_script[config]);\n")
        file.write("    }\n")   

    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"\\nCheck Config\\n\\n\");\n")
    else:
        file.write("    // trace_printf(\"\\nCheck Config\\n\\n\");\n")   

    file.write("    for (int config = 0; config < app_size; config++){\n")
    file.write("        uint32_t read_data = HAL_Cgra_Tile_ReadReg(app_addrs_script[config]);\n")
    file.write("        uint32_t addr = app_addrs_script[config];\n")

    if(unroll != "0"):
        file.write("        uint32_t addr_shifted = (addr & 0xFFFF00FF) | ((((addr & 0x0000FF00) >> 8) + 16) << 8);\n")
        file.write("        uint32_t read_data2 = HAL_Cgra_Tile_ReadReg(addr_shifted);\n")

    file.write("        uint32_t gold = app_datas_script[config];\n")
    file.write("\n")
    file.write("        if ( read_data != gold){\n")
    file.write("            trace_printf(\"config error: %d \", config);\n")
    file.write("            trace_printf(\"address: %lx \", addr);\n")
    file.write("            trace_printf(\"read_data %lx \", read_data);\n")
    file.write("            trace_printf(\"gold data %lx\\n\", gold);\n")
    file.write("        }\n")
    if(unroll != "0"): 
        file.write("        if ( read_data2 != gold){\n")
        file.write("            trace_printf(\"config error: %d \", config);\n")
        file.write("            trace_printf(\"address: %lx \", addr);\n")
        file.write("            trace_printf(\"read_data %lx \", read_data2);\n")
        file.write("            trace_printf(\"gold data %lx\\n\", gold);\n")
        file.write("        }\n")
    file.write("    }\n")
    file.write("\n")
    file.write("    // Faster clocks for App\n")
    file.write("    status = HAL_PtfmCtrl_SelectClock( & PtfmCtl, sys_mask, 1); // 2^2 = 4 60/4 = 15\n")

def main_block_2(file, mapping_dict, op_list, unroll, glb_tile_offset, glb_bank_offset, debug):

    file.write("    uint16_t* input_read_base = AHASOC_CGRA_DATA_BASE;\n")
    
    num_tiles = 0

    for op in op_list:
        num_tiles += len(mapping_dict[op]) 

    file.write("\n")
    for i in range(num_tiles):
        file.write("    input_read_base = AHASOC_CGRA_DATA_BASE + " + glb_tile_offset + " * " + str(i) + ";\n")
        if(debug):
            file.write("    trace_printf(\"first location: %lx\\n\", input_read_base[0]);\n")
        else:
            file.write("    // trace_printf(\"first location: %lx\\n\", input_read_base[0]);\n")

    file.write("\n")

    if(unroll != "0"): 
        for i in range(num_tiles):
            file.write("    input_read_base = AHASOC_CGRA_DATA_BASE + " + glb_tile_offset + " * 8 + " + glb_tile_offset + " * " + str(i) + ";\n")
            if(debug):
                file.write("    trace_printf(\"first location: %lx\\n\", input_read_base[0]);\n")
            else:
                file.write("    // trace_printf(\"first location: %lx\\n\", input_read_base[0]);\n")                
        file.write("\n")

    if(debug):
        file.write("    trace_printf(\"\\nCONFIG GLB\\n\");\n") 
    else:
        file.write("    // trace_printf(\"\\nCONFIG GLB\\n\");\n") 
    file.write("    app_glb_config(0);\n")

    if(unroll != "0"): 
        file.write("    app_glb_config(8);\n")

    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"\\nAPP Prep\\n\");\n")
    else:
        file.write("    // trace_printf(\"\\nAPP Prep\\n\");\n")
    file.write("\n")
    if(unroll != "0"):
        file.write("    HAL_Cgra_Glc_WriteReg(GLC_GLB_FLUSH_CROSSBAR_R, 0x88880000);\n")  
    else:
        file.write("    HAL_Cgra_Glc_WriteReg(GLC_GLB_FLUSH_CROSSBAR_R, 0);\n")      
    file.write("    HAL_Cgra_Glc_WriteReg(GLC_CGRA_STALL_R, 0x0);\n")
    file.write("    HAL_Cgra_Glc_WriteReg(GLC_GLOBAL_IER_R, 1);\n")
    file.write("    HAL_Cgra_Glc_WriteReg(GLC_STRM_F2G_IER_R, 0xffff);\n")
    file.write("    HAL_Cgra_Glc_WriteReg(GLC_STRM_G2F_IER_R, 0xffff);\n")
    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"\\n** Run code-gen  **\\n\");\n")
    else:
        file.write("    // trace_printf(\"\\n** Run code-gen  **\\n\");\n")   
    file.write("\n")
    file.write("    const uint32_t start_addr = 0x0;\n")
    file.write("    const uint32_t read_start_addr = " + glb_bank_offset + ";\n")

def main_block_3(file, mapping_dict, dest, unroll, glb_tile_offset, glb_bank_offset, debug, gcheck, ap_gcheck):

    out_tensor_dim = len(mapping_dict[dest])
    for i in range(out_tensor_dim):
        curr_mapping = mapping_dict[dest][i]    
        file.write("    uint16_t* output_read_base" + str(i) + " = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + " + glb_tile_offset + " * " + str(curr_mapping) + ");\n")
    file.write("\n")

    if(ap_gcheck): 
        if(unroll == "2"): 
            file.write("    uint16_t* map = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + " + glb_tile_offset + " * " + "6" + ");\n")

    for i in range(out_tensor_dim - 1):
        file.write("    int " + dest + "_mode_" + str(i) + "_idx = 0;\n")
    file.write("    int " + dest + "_mode_vals_idx = 0;\n")
    file.write("\n")

    file.write("    int size;\n")
    for i in range(out_tensor_dim - 1):
        file.write("    int " + dest + "_mode_" + str(i) + "_size;\n")
    file.write("    int " + dest + "_mode_vals_size;\n")
    file.write("\n")

    if(unroll != "0"): 
        for i in range(out_tensor_dim):
            curr_mapping = mapping_dict[dest][i]    
            file.write("    uint16_t* output_read_base" + str(i) + "_unroll = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + " + glb_tile_offset + " * 8 + " + glb_tile_offset + " * " + str(curr_mapping) + ");\n")
        file.write("\n")

        for i in range(out_tensor_dim - 1):
            file.write("    int " + dest + "_mode_" + str(i) + "_idx_unroll = 0;\n")
        file.write("    int " + dest + "_mode_vals_idx_unroll = 0;\n")
        file.write("\n")

        file.write("    int size_unroll;\n")
        for i in range(out_tensor_dim - 1):
            file.write("    int " + dest + "_mode_" + str(i) + "_size_unroll;\n")
        file.write("    int " + dest + "_mode_vals_size_unroll;\n")
        file.write("\n")
    
    if(unroll == "2"): 
        file.write("    int run1 = 0;\n")
        file.write("    if(runs > 0){\n")
        file.write("        update_glb_input(run1);\n")
        if(gcheck): 
            file.write("        map[run1] = 0;\n")
        file.write("        run1++;\n")
        file.write("    }\n")
        file.write("    if(runs > 0 && run1 < runs){\n")
        file.write("        update_glb_input_unroll(run1);\n")
        if(gcheck):
             file.write("        map[run1] = 1;\n")
        file.write("        run1++;\n")
        file.write("    }\n")
    else: 
        file.write("    int run1 = 0;\n")
        file.write("    if(runs > 0){\n")
        file.write("        update_glb_input(run1);\n")
        file.write("    }\n")
    
    if(unroll == "1"):
        file.write("    int run2 = 0;\n")
        file.write("    if(runs_unroll > 0){")
        file.write("        update_glb_input_unroll(run2);\n")
        file.write("    }")
        
    file.write("\n")
    
    file.write("    uint32_t cycles = 0;\n")    
    file.write("\n")
    file.write("    // 1. Enable trace and debug (if not enabled already)\n")
    file.write("    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;\n")
    file.write("\n")
    file.write("    // 2. Reset cycle counter\n")
    file.write("    DWT->CYCCNT = 0;\n")
    file.write("\n")
    file.write("    // 3. Start cycle counter\n")
    file.write("    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;\n")
    file.write("\n")

    file.write("    int input_mask = stream_pulse_g2f;\n")
    file.write("    int output_mask = stream_pulse_f2g;\n")
    file.write("\n")

    file.write("    int input_in1 = 0;\n")
    if(unroll != "0"):
        file.write("    int input_in2 = 0;\n")
    file.write("\n")

    if(unroll == "1"):
        while_cond_check = "(run1 < runs || run2 < runs_unroll){"
    elif(unroll == "2"):
        while_cond_check = "((run1 < runs) || ((run1 == runs) && ((input_in1 != 0) || (input_in2 != 0)))){"
    else: 
        while_cond_check = "(run1 < runs){"    
    

    file.write("    HAL_Cgra_Glc_WriteReg(GLC_STREAM_START_PULSE_R, output_mask << 16 | input_mask);\n")
    if(unroll != "0"): 
        file.write("    HAL_Cgra_Glc_WriteReg(GLC_STREAM_START_PULSE_R, (output_mask << 8) << 16 | (input_mask << 8));\n")
    file.write("\n")

    file.write(f"    while{while_cond_check}\n")
    file.write("\n")

    file.write("        // Wait for inputs to finish sending\n")
    file.write("        if(run1 < runs && (input_in1 == 0) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_G2F_ISR_R) & input_mask) == input_mask)){\n")
    file.write("            HAL_Cgra_Glc_WriteReg(GLC_STRM_G2F_ISR_R, input_mask);\n")
    if(unroll == "2"):
        file.write("            update_glb_input(run1);\n")
        if(gcheck):
            file.write("            map[run1] = 0;\n")
        file.write("            run1++;\n")
    else:
        file.write("            update_glb_input(run1 + 1);\n")
    file.write("            input_in1 = 1;\n")
    file.write("        }\n")
    file.write("\n")

    if(unroll != "0"):
        if(unroll == "1"):
            file.write("        if(run2 < runs_unroll && (input_in2 == 0) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_G2F_ISR_R) & (input_mask << 8)) == (input_mask << 8))){\n")
        elif (unroll == "2"):
            file.write("        if(run1 < runs && (input_in2 == 0) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_G2F_ISR_R) & (input_mask << 8)) == (input_mask << 8))){\n")            
        file.write("            HAL_Cgra_Glc_WriteReg(GLC_STRM_G2F_ISR_R, input_mask << 8);\n")
        if(unroll == "2"):
            file.write("            update_glb_input_unroll(run1);\n")
            if(gcheck):
                file.write("            map[run1] = 1;\n")
            file.write("            run1++;\n")
        else:
            file.write("            update_glb_input_unroll(run2 + 1);\n")
        file.write("            input_in2 = 1;\n")
        file.write("        }\n")
        file.write("\n")

    file.write("        // Wait for outputs to all fill in\n")
    if(unroll != "2"):
        file.write("        if(run1 < runs && (input_in1 == 1) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) & output_mask) == output_mask)){\n")
    else:
        file.write("        if(run1 <= runs && (input_in1 == 1) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) & output_mask) == output_mask)){\n")
    file.write("\n")
    file.write("            HAL_Cgra_Glc_WriteReg(GLC_STRM_F2G_ISR_R, output_mask);\n")
    if(unroll != "2"):
        file.write("            run1++;\n")
        file.write("\n")
        file.write("            if(run1 < runs){\n")
        file.write("\n")
    else:
        file.write("            if(run1 <= runs){\n")
        file.write("\n")
    file.write("            // Updating output pointers\n")

    for i in range(out_tensor_dim - 1): 
        file.write("                size = output_read_base" + str(i) + "[" + dest + "_mode_" + str(i) + "_idx];\n")
        file.write("                int " + dest + "_mode_" + str(i) + "_size = size + 1 + output_read_base" + str(i) + "[" + dest + "_mode_" + str(i) + "_idx + size + 1] + 1;\n")
    
    file.write("                int " + dest + "_mode_vals_size = output_read_base" + str(out_tensor_dim - 1) + "[" + dest + "_mode_vals_idx] + 1;\n")
    file.write("\n")

    for i in range(out_tensor_dim - 1):
        file.write("                " + dest + "_mode_" + str(i) + "_idx += " + dest + "_mode_" + str(i) + "_size;\n")
    file.write("                " + dest + "_mode_vals_idx += " + dest + "_mode_vals_size;\n")
    file.write("\n")
    	
    for i in range(out_tensor_dim - 1):
        curr_mapping = mapping_dict[dest][i]
        file.write("                HAL_Cgra_Glb_WriteReg(0x100 * " + str(curr_mapping) + " + GLB_ST_DMA_HEADER_0_START_ADDR_R, " + glb_bank_offset + " + " + glb_tile_offset + " * " + str(curr_mapping) + " + " + dest + "_mode_" + str(i) + "_idx*2);\n")
    val_mapping = mapping_dict[dest][out_tensor_dim - 1]
    file.write("                HAL_Cgra_Glb_WriteReg(0x100 * " + str(val_mapping) + " + GLB_ST_DMA_HEADER_0_START_ADDR_R, " + glb_bank_offset + " + " + glb_tile_offset + " * " + str(val_mapping) + " + " + dest + "_mode_vals_idx*2);\n")
    file.write("\n")
    
    file.write("                HAL_Cgra_Glc_WriteReg(GLC_STREAM_START_PULSE_R, output_mask << 16 | input_mask); // pulsed reg.\n")
    file.write("            }\n")
    file.write("            input_in1 = 0;\n")
    file.write("        }\n")
    file.write("\n")
    
    if(unroll != "0"): 
        
        if(unroll != "2"):
            file.write("        if(run2 < runs_unroll && (input_in2 == 1) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) & (output_mask << 8)) == (output_mask << 8))){\n")
            file.write("\n")
            file.write("            run2++;\n")
            file.write("\n")
            file.write("            HAL_Cgra_Glc_WriteReg(GLC_STRM_F2G_ISR_R, output_mask << 8);\n")     
            file.write("\n")
            file.write("            if(run2 < runs_unroll){\n")
        else:
            file.write("        if(run1 <= runs && (input_in2 == 1) && ((HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) & (output_mask << 8)) == (output_mask << 8))){\n")
            file.write("\n")
            file.write("            HAL_Cgra_Glc_WriteReg(GLC_STRM_F2G_ISR_R, output_mask << 8);\n")
            file.write("\n")
            file.write("            if(run1 <= runs){\n")
        
        file.write("\n")
        file.write("            // Updating output pointers\n")
        for i in range(out_tensor_dim - 1): 
            file.write("                size = output_read_base" + str(i) + "_unroll[" + dest + "_mode_" + str(i) + "_idx_unroll];\n")
            file.write("                int " + dest + "_mode_" + str(i) + "_size_unroll = size + 1 + output_read_base" + str(i) + "_unroll[" + dest + "_mode_" + str(i) + "_idx_unroll + size + 1] + 1;\n")
        
        file.write("                int " + dest + "_mode_vals_size_unroll = output_read_base" + str(out_tensor_dim - 1) + "_unroll[" + dest + "_mode_vals_idx_unroll] + 1;\n")
        file.write("\n")

        for i in range(out_tensor_dim - 1):
            file.write("                " + dest + "_mode_" + str(i) + "_idx_unroll += " + dest + "_mode_" + str(i) + "_size_unroll;\n")
        file.write("                " + dest + "_mode_vals_idx_unroll += " + dest + "_mode_vals_size_unroll;\n")
        file.write("\n")
            
        for i in range(out_tensor_dim - 1):
            curr_mapping = mapping_dict[dest][i]
            file.write("                HAL_Cgra_Glb_WriteReg(0x100 * 8 + 0x100 * " + str(curr_mapping) + " + GLB_ST_DMA_HEADER_0_START_ADDR_R, " + glb_bank_offset + " + " + glb_tile_offset + " * 8 + " + glb_tile_offset + " * " + str(curr_mapping) + " + " + dest + "_mode_" + str(i) + "_idx_unroll*2);\n")
        val_mapping = mapping_dict[dest][out_tensor_dim - 1]
        file.write("                HAL_Cgra_Glb_WriteReg(0x100 * 8 + 0x100 * " + str(val_mapping) + " + GLB_ST_DMA_HEADER_0_START_ADDR_R, " + glb_bank_offset + " + " + glb_tile_offset + " * 8 + " + glb_tile_offset + " * " + str(val_mapping) + " + " + dest + "_mode_vals_idx_unroll*2);\n")
        file.write("\n")
        file.write("                HAL_Cgra_Glc_WriteReg(GLC_STREAM_START_PULSE_R, (output_mask << 8) << 16 | (input_mask << 8)); // pulsed reg.\n")
        file.write("            }\n")
        file.write("            input_in2 = 0;\n")
        file.write("        }")
        file.write("\n")

    file.write("    }\n")   
    file.write("\n")

    if(unroll == "2"):  
        file.write("    while(((HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) & output_mask) != output_mask)){}\n")
        file.write("    if(runs > 1)")
        file.write("        while((HAL_Cgra_Glc_ReadReg(GLC_STRM_F2G_ISR_R) & (output_mask << 8)) != (output_mask << 8)){}")
            
    file.write("    // 5. Stop cycle counter\n")
    file.write("    cycles = DWT->CYCCNT;\n")
    file.write("\n")
    file.write("    // 6. Disable cycle counter\n")
    file.write("    DWT->CTRL &= ~CoreDebug_DEMCR_TRCENA_Msk;\n")
    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"total cycles %d\\n\", cycles*2);\n")
    else:
        file.write("    // trace_printf(\"total cycles %d\\n\", cycles*2);\n")       

    file.write("    int *read_base_cyc_count = AHASOC_CGRA_DATA_BASE;\n")
    file.write("    read_base_cyc_count[0] = cycles * 2;\n")
  
    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"wait for app\\n\");\n")
    else:
        file.write("    // trace_printf(\"wait for app\\n\");\n")        
    file.write("\n")
    file.write("    int errors = 0;\n")
    file.write("\n")
    file.write("    uint16_t* output_read_base = AHASOC_CGRA_DATA_BASE + " + glb_tile_offset + " * 0 + " + glb_bank_offset + ";\n")

    for i in range(out_tensor_dim):
        file.write("    output_read_base = AHASOC_CGRA_DATA_BASE + " + glb_tile_offset + " * " + str(i) + " + " + glb_bank_offset + ";\n")
        if(debug):
            file.write("    trace_printf(\"first location: %lx\\n\", output_read_base" + str(i) + "[0]);\n")
        else:
            file.write("    // trace_printf(\"first location: %lx\\n\", output_read_base" + str(i) + "[0]);\n")            

    if(unroll != "0"):
        for i in range(out_tensor_dim):
            file.write("    output_read_base = AHASOC_CGRA_DATA_BASE + " + glb_tile_offset + " * 8 + " + glb_tile_offset + " * " + str(i) + " + " + glb_bank_offset + ";\n")
            if(debug):
                file.write("    trace_printf(\"first location_unroll: %lx\\n\", output_read_base[0]);\n")
            else:
                file.write("    // trace_printf(\"first location_unroll: %lx\\n\", output_read_base[0]);\n")   

    file.write("\n")
    if(debug):
        file.write("    trace_printf(\"check gold data\\n\");\n")
    else: 
        file.write("    // trace_printf(\"check gold data\\n\");\n") 
    if(gcheck and not ap_gcheck):     
        file.write("    errors = check_gold_data();\n")
        file.write("    read_base_cyc_count[0] = errors;\n")
    if(debug):
        file.write("    trace_printf(\"total errors: %d\\n\", errors);\n")
    else:
        file.write("    // trace_printf(\"total errors: %d\\n\", errors);\n")


          
    file.write("\n")
    file.write("    return 0;\n")
    file.write("}\n")