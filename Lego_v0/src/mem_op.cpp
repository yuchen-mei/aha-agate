#include "mem_op.h"


tile0 tensor_mem_op_0(int **tensor_op){
    float *vals = (float *) tensor_op[0];
    tile0 tile_op; 
    tile_op.pos1.push_back(0);
    tile_op.pos1.push_back(1);
    tile_op.crd1.push_back(0);
    tile_op.vals.push_back(vals[0]);    
    return tile_op;
}

tile1 tensor_mem_op_1(int **tensor_op, int index){
    
    int *pos1 = tensor_op[2]; 
    int *crd1 = tensor_op[3];
    int *pos2 = tensor_op[4];
    int *crd2 = tensor_op[5];
    float *vals = (float *) tensor_op[6];
    
    tile1 tile_op;
    
    tile_op.pos1.push_back(0);
    tile_op.pos1.push_back(pos1[index + 1] - pos1[index]);
    
    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        tile_op.crd1.push_back(crd1[i]);
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
            tile_op.crd2.push_back(crd2[j]);
            tile_op.vals.push_back(vals[j]);
        }
    }

    for(int i = pos1[index]; i <= pos1[index + 1]; i++) {
        tile_op.pos2.push_back(pos2[i] - pos2[pos1[index]]);
    }
    
    return tile_op;
}

tile2 tensor_mem_op_2(int **tensor_op, int index){

	int *pos1 = tensor_op[4]; 
	int *crd1 = tensor_op[5];
	int *pos2 = tensor_op[6];
	int *crd2 = tensor_op[7];
	int *pos3 = tensor_op[8];
	int *crd3 = tensor_op[9];
	int *pos4 = tensor_op[10];
	int *crd4 = tensor_op[11];
	float *vals = (float *) tensor_op[12];

    tile2 tile_op;

	tile_op.pos1.push_back(0);
	tile_op.pos1.push_back(pos1[index + 1] - pos1[index]);

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        tile_op.crd1.push_back(crd1[i]);
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
			tile_op.crd2.push_back(crd2[j]);
            for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                tile_op.crd3.push_back(crd3[k]);
                for(int l = pos4[k]; l < pos4[k + 1]; l++) {
					tile_op.crd4.push_back(crd4[l]);
					tile_op.vals.push_back(vals[l]);
            	}
            }
        }
    }

    for(int i = pos1[index]; i <= pos1[index + 1]; i++) {
		tile_op.pos2.push_back(pos2[i] - pos2[pos1[index]]);
    }

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
			tile_op.pos3.push_back(pos3[j] - pos3[pos2[pos1[index]]]);
        }
    }

	tile_op.pos3.push_back(pos3[pos2[pos1[index + 1]]] - pos3[pos2[pos1[index]]]);

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
            for(int k = pos3[j]; k < pos3[j + 1]; k++) {
				tile_op.pos4.push_back(pos4[k] - pos4[pos3[pos2[pos1[index]]]]);
            }
        }
    }

	tile_op.pos4.push_back(pos4[pos3[pos2[pos1[index + 1]]]] - pos4[pos3[pos2[pos1[index]]]]);

    return tile_op;

}

tile3 tensor_mem_op_3(int **tensor_op, int index){
    
        int *pos1 = tensor_op[6]; 
        int *crd1 = tensor_op[7];
        int *pos2 = tensor_op[8];
        int *crd2 = tensor_op[9];
        int *pos3 = tensor_op[10];
        int *crd3 = tensor_op[11];
        int *pos4 = tensor_op[12];
        int *crd4 = tensor_op[13];
        int *pos5 = tensor_op[14];
        int *crd5 = tensor_op[15];
        int *pos6 = tensor_op[16];
        int *crd6 = tensor_op[17];
        float *vals = (float *) tensor_op[18];
    
        tile3 tile_op;
    
        tile_op.pos1.push_back(0);
        tile_op.pos1.push_back(pos1[index + 1] - pos1[index]);
    
        for(int i = pos1[index]; i < pos1[index + 1]; i++) {
            tile_op.crd1.push_back(crd1[i]);
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                tile_op.crd2.push_back(crd2[j]);
                for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                    tile_op.crd3.push_back(crd3[k]);
                    for(int l = pos4[k]; l < pos4[k + 1]; l++) {
                        tile_op.crd4.push_back(crd4[l]);
                        for(int m = pos5[l]; m < pos5[l + 1]; m++) {
                            tile_op.crd5.push_back(crd5[m]);
                            for(int n = pos6[m]; n < pos6[m + 1]; n++) {
                                tile_op.crd6.push_back(crd6[n]);
                                tile_op.vals.push_back(vals[n]);
                            }
                        }
                    }
                }
            }
        }
    
        for(int i = pos1[index]; i <= pos1[index + 1]; i++) {
            tile_op.pos2.push_back(pos2[i] - pos2[pos1[index]]);
        }
    
        for(int i = pos1[index]; i < pos1[index + 1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                tile_op.pos3.push_back(pos3[j] - pos3[pos2[pos1[index]]]);
            }
        }

        tile_op.pos3.push_back(pos3[pos2[pos1[index + 1]]] - pos3[pos2[pos1[index]]]);

        for(int i = pos1[index]; i < pos1[index + 1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                    tile_op.pos4.push_back(pos4[k] - pos4[pos3[pos2[pos1[index]]]]);
                }
            }
        }

        tile_op.pos4.push_back(pos4[pos3[pos2[pos1[index + 1]]]] - pos4[pos3[pos2[pos1[index]]]]);

        for(int i = pos1[index]; i < pos1[index + 1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                    for(int l = pos4[k]; l < pos4[k + 1]; l++) {
                        tile_op.pos5.push_back(pos5[l] - pos5[pos4[pos3[pos2[pos1[index]]]]]);
                    }
                }
            }
        }

        tile_op.pos5.push_back(pos5[pos4[pos3[pos2[pos1[index + 1]]]]] - pos5[pos4[pos3[pos2[pos1[index]]]]]);

        for(int i = pos1[index]; i < pos1[index + 1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                    for(int l = pos4[k]; l < pos4[k + 1]; l++) {
                        for(int m = pos5[l]; m < pos5[l + 1]; m++) {
                            tile_op.pos6.push_back(pos6[m] - pos6[pos5[pos4[pos3[pos2[pos1[index]]]]]]);
                        }
                    }
                }
            }
        }

        tile_op.pos6.push_back(pos6[pos5[pos4[pos3[pos2[pos1[index + 1]]]]]] - pos6[pos5[pos4[pos3[pos2[pos1[index]]]]]]);

        return tile_op;
}

subtile0 tile_mem_op_0(tile0 tile_op){
    subtile0 subtile_op;
    subtile_op.pos1.push_back(0);
    subtile_op.pos1.push_back(1);
    subtile_op.crd1.push_back(0);
    subtile_op.vals.push_back(tile_op.vals[0]);
    return subtile_op;
}

subtile1 tile_mem_op_1(tile1 tile_op, int index){

    int *pos1 = tile_op.pos2.data();
    int *crd1 = tile_op.crd2.data();
    float *vals = tile_op.vals.data();

    subtile1 subtile_op;

    subtile_op.pos1.push_back(0);
    subtile_op.pos1.push_back(pos1[index + 1] - pos1[index]);

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        subtile_op.crd1.push_back(crd1[i]);
        subtile_op.vals.push_back(vals[i]);
    }

    return subtile_op;

}

subtile2 tile_mem_op_2(tile2 tile_op, int index){

    int *pos1 = tile_op.pos3.data();
    int *crd1 = tile_op.crd3.data();
    int *pos2 = tile_op.pos4.data();
    int *crd2 = tile_op.crd4.data();
    float *vals = tile_op.vals.data();

    subtile2 subtile_op;

	subtile_op.pos1.push_back(0);
	subtile_op.pos1.push_back(pos1[index + 1] - pos1[index]);

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        subtile_op.crd1.push_back(crd1[i]);
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
			subtile_op.crd2.push_back(crd2[j]);
            subtile_op.vals.push_back(vals[j]);
        }
    }

    for(int i = pos1[index]; i <= pos1[index + 1]; i++) {
		subtile_op.pos2.push_back(pos2[i] - pos2[pos1[index]]);
    }

    return subtile_op;
}

subtile3 tile_mem_op_3(tile3 tile_op, int index){

    int *pos1 = tile_op.pos4.data();
    int *crd1 = tile_op.crd4.data();
    int *pos2 = tile_op.pos5.data();
    int *crd2 = tile_op.crd5.data();
    int *pos3 = tile_op.pos6.data();
    int *crd3 = tile_op.crd6.data();
    float *vals = tile_op.vals.data();

    subtile3 subtile_op;

    subtile_op.pos1.push_back(0);
    subtile_op.pos1.push_back(pos1[index + 1] - pos1[index]);

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        subtile_op.crd1.push_back(crd1[i]);
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
            subtile_op.crd2.push_back(crd2[j]);
            for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                subtile_op.crd3.push_back(crd3[k]);
                subtile_op.vals.push_back(vals[k]);
            }
        }
    }

    for(int i = pos1[index]; i <= pos1[index + 1]; i++) {
        subtile_op.pos2.push_back(pos2[i] - pos2[pos1[index]]);
    }

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
            subtile_op.pos3.push_back(pos3[j] - pos3[pos2[pos1[index]]]);
        }
    }
    subtile_op.pos3.push_back(pos3[pos2[pos1[index + 1]]] - pos3[pos2[pos1[index]]]);

    return subtile_op;
}

cg_subtile1 cg_tile_mem_op_1(cg_subtile1 cg_subtile_op, int **store_subtile_op, subtile1 subtile_op, int id_store_op){
    
    int *pos1 = subtile_op.pos1.data();
    int *crd1 = subtile_op.crd1.data();
    float *vals = subtile_op.vals.data();
    
    int stile_pos1_len = subtile_op.pos1.size();	
    int stile_crd1_len = subtile_op.crd1.size();
    int stile_vals_len = subtile_op.vals.size();    
        
    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode_vals_start = store_subtile_op[2];
    int *op_mode_vals_end = store_subtile_op[3];
    
    op_mode0_start[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode_vals_start[id_store_op] = cg_subtile_op.mode_vals.size(); 
    
    cg_subtile_op.mode_0.push_back(stile_pos1_len);
    cg_subtile_op.mode_0.push_back(0);
    cg_subtile_op.mode_0.push_back(pos1[1]);
    cg_subtile_op.mode_0.push_back(stile_crd1_len);
    
    for(int i = 0; i < pos1[1]; i++) {
        cg_subtile_op.mode_0.push_back(crd1[i]);
    }
    
    cg_subtile_op.mode_vals.push_back(stile_vals_len);
    
    for(int i = 0; i < pos1[1]; i++) {
        cg_subtile_op.mode_vals.push_back(vals[i]);
    }
    
    op_mode0_end[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode_vals_end[id_store_op] = cg_subtile_op.mode_vals.size();
    
    return cg_subtile_op;
}

cg_subtile2 cg_tile_mem_op_2(cg_subtile2 cg_subtile_op, int **store_subtile_op, subtile2 subtile_op, int id_store_op){

    int *pos1 = subtile_op.pos1.data();
    int *crd1 = subtile_op.crd1.data();
    int *pos2 = subtile_op.pos2.data();
    int *crd2 = subtile_op.crd2.data();
    float *vals = subtile_op.vals.data();

    int stile_pos1_len = subtile_op.pos1.size();	
	int stile_pos2_len = subtile_op.pos2.size();
	int stile_crd1_len = subtile_op.crd1.size();
	int stile_crd2_len = subtile_op.crd2.size(); 
	int stile_vals_len = subtile_op.vals.size(); 
    
    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode1_start = store_subtile_op[2];
    int *op_mode1_end = store_subtile_op[3];
    int *op_mode_vals_start = store_subtile_op[4];
    int *op_mode_vals_end = store_subtile_op[5];

    op_mode0_start[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode1_start[id_store_op] = cg_subtile_op.mode_1.size();
    op_mode_vals_start[id_store_op] = cg_subtile_op.mode_vals.size(); 

    cg_subtile_op.mode_0.push_back(stile_pos1_len);
	cg_subtile_op.mode_0.push_back(0);
	cg_subtile_op.mode_0.push_back(pos1[1]);
	cg_subtile_op.mode_0.push_back(stile_crd1_len);

    for(int i = 0; i < pos1[1]; i++) {
		cg_subtile_op.mode_0.push_back(crd1[i]);
    }

	cg_subtile_op.mode_1.push_back(stile_pos2_len); 
    for(int i = 0; i <= pos1[1]; i++) {
        cg_subtile_op.mode_1.push_back(pos2[i]);
    }

	cg_subtile_op.mode_1.push_back(stile_crd2_len);
	cg_subtile_op.mode_vals.push_back(stile_vals_len);

	for(int i = 0; i < pos1[1]; i++) {
        for(int j = pos2[i]; j < pos2[i + 1]; j++) {
            cg_subtile_op.mode_1.push_back(crd2[j]);
            cg_subtile_op.mode_vals.push_back(vals[j]);
        }
    }

    op_mode0_end[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode1_end[id_store_op] = cg_subtile_op.mode_1.size();
    op_mode_vals_end[id_store_op] = cg_subtile_op.mode_vals.size();

    return cg_subtile_op;
} 

cg_subtile1 cg_tile_zero_op_1(int **store_subtile_op, cg_subtile1 cg_subtile_op, int id_store_op){
    
    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode_vals_start = store_subtile_op[2];
    int *op_mode_vals_end = store_subtile_op[3];

    op_mode0_start[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode_vals_start[id_store_op] = cg_subtile_op.mode_vals.size(); 

    cg_subtile_op.mode_0.push_back(2);
    cg_subtile_op.mode_0.push_back(0);
    cg_subtile_op.mode_0.push_back(1);
    cg_subtile_op.mode_0.push_back(1);
    cg_subtile_op.mode_0.push_back(0);

    cg_subtile_op.mode_vals.push_back(1);
    cg_subtile_op.mode_vals.push_back(0);

    op_mode0_end[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode_vals_end[id_store_op] = cg_subtile_op.mode_vals.size();

    return cg_subtile_op;
}

cg_subtile2 cg_tile_zero_op_2(int **store_subtile_op, cg_subtile2 cg_subtile_op, int id_store_op){
      
    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode1_start = store_subtile_op[2];
    int *op_mode1_end = store_subtile_op[3];
    int *op_mode_vals_start = store_subtile_op[4];
    int *op_mode_vals_end = store_subtile_op[5];

    op_mode0_start[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode1_start[id_store_op] = cg_subtile_op.mode_1.size();
    op_mode_vals_start[id_store_op] = cg_subtile_op.mode_vals.size(); 

    cg_subtile_op.mode_0.push_back(2);
    cg_subtile_op.mode_0.push_back(0);
    cg_subtile_op.mode_0.push_back(1);
    cg_subtile_op.mode_0.push_back(1);
    cg_subtile_op.mode_0.push_back(0);

    cg_subtile_op.mode_1.push_back(2);
    cg_subtile_op.mode_1.push_back(0);
    cg_subtile_op.mode_1.push_back(1);
    cg_subtile_op.mode_1.push_back(1);
    cg_subtile_op.mode_1.push_back(0);

    cg_subtile_op.mode_vals.push_back(1);
    cg_subtile_op.mode_vals.push_back(0);

    op_mode0_end[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode1_end[id_store_op] = cg_subtile_op.mode_1.size();
    op_mode_vals_end[id_store_op] = cg_subtile_op.mode_vals.size();

    return cg_subtile_op;
}

cg_subtile3 cg_tile_zero_op_3(int **store_subtile_op, cg_subtile3 cg_subtile_op, int id_store_op){
    
    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode1_start = store_subtile_op[2];
    int *op_mode1_end = store_subtile_op[3];
    int *op_mode2_start = store_subtile_op[4];
    int *op_mode2_end = store_subtile_op[5];
    int *op_mode_vals_start = store_subtile_op[6];
    int *op_mode_vals_end = store_subtile_op[7];

    op_mode0_start[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode1_start[id_store_op] = cg_subtile_op.mode_1.size();
    op_mode2_start[id_store_op] = cg_subtile_op.mode_2.size();
    op_mode_vals_start[id_store_op] = cg_subtile_op.mode_vals.size(); 

    cg_subtile_op.mode_0.push_back(2);
    cg_subtile_op.mode_0.push_back(0);
    cg_subtile_op.mode_0.push_back(1);
    cg_subtile_op.mode_0.push_back(1);
    cg_subtile_op.mode_0.push_back(0);

    cg_subtile_op.mode_1.push_back(2);
    cg_subtile_op.mode_1.push_back(0);
    cg_subtile_op.mode_1.push_back(1);
    cg_subtile_op.mode_1.push_back(1);
    cg_subtile_op.mode_1.push_back(0);

    cg_subtile_op.mode_2.push_back(2);
    cg_subtile_op.mode_2.push_back(0);
    cg_subtile_op.mode_2.push_back(1);
    cg_subtile_op.mode_2.push_back(1);
    cg_subtile_op.mode_2.push_back(0);

    cg_subtile_op.mode_vals.push_back(1);
    cg_subtile_op.mode_vals.push_back(0);

    op_mode0_end[id_store_op] = cg_subtile_op.mode_0.size();
    op_mode1_end[id_store_op] = cg_subtile_op.mode_1.size();
    op_mode2_end[id_store_op] = cg_subtile_op.mode_2.size();
    op_mode_vals_end[id_store_op] = cg_subtile_op.mode_vals.size();

    return cg_subtile_op;
}

cg_subtile3 cg_tile_mem_op_3(cg_subtile3 cg_subtile_op, int **store_subtile_op, subtile3 subtile_op, int id_store_op){
    
        int *pos1 = subtile_op.pos1.data();
        int *crd1 = subtile_op.crd1.data();
        int *pos2 = subtile_op.pos2.data();
        int *crd2 = subtile_op.crd2.data();
        int *pos3 = subtile_op.pos3.data();
        int *crd3 = subtile_op.crd3.data();
        float *vals = subtile_op.vals.data();
    
        int stile_pos1_len = subtile_op.pos1.size();
        int stile_pos2_len = subtile_op.pos2.size();
        int stile_pos3_len = subtile_op.pos3.size();
        int stile_crd1_len = subtile_op.crd1.size();
        int stile_crd2_len = subtile_op.crd2.size();
        int stile_crd3_len = subtile_op.crd3.size();
        int stile_vals_len = subtile_op.vals.size();
        
        int *op_mode0_start =  store_subtile_op[0];
        int *op_mode0_end = store_subtile_op[1];
        int *op_mode1_start = store_subtile_op[2];
        int *op_mode1_end = store_subtile_op[3];
        int *op_mode2_start = store_subtile_op[4];
        int *op_mode2_end = store_subtile_op[5];
        int *op_mode_vals_start = store_subtile_op[6];
        int *op_mode_vals_end = store_subtile_op[7];
    
        op_mode0_start[id_store_op] = cg_subtile_op.mode_0.size();
        op_mode1_start[id_store_op] = cg_subtile_op.mode_1.size();
        op_mode2_start[id_store_op] = cg_subtile_op.mode_2.size();
        op_mode_vals_start[id_store_op] = cg_subtile_op.mode_vals.size(); 
    
        cg_subtile_op.mode_0.push_back(stile_pos1_len);
	    cg_subtile_op.mode_0.push_back(0);
	    cg_subtile_op.mode_0.push_back(pos1[1]);
	    cg_subtile_op.mode_0.push_back(stile_crd1_len);

        for(int i = 0; i < pos1[1]; i++) {
	    	cg_subtile_op.mode_0.push_back(crd1[i]);
        }

	    cg_subtile_op.mode_1.push_back(stile_pos2_len); 
        for(int i = 0; i <= pos1[1]; i++) {
            cg_subtile_op.mode_1.push_back(pos2[i]);
        }

    	cg_subtile_op.mode_1.push_back(stile_crd2_len); 
    	for(int i = 0; i < pos1[1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                cg_subtile_op.mode_1.push_back(crd2[j]);
            }
        }

        cg_subtile_op.mode_2.push_back(stile_pos3_len);
        for(int i = 0; i < pos1[1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                cg_subtile_op.mode_2.push_back(pos3[j]);
            }
        }

        cg_subtile_op.mode_2.push_back(pos3[pos2[pos1[1]]]);

        cg_subtile_op.mode_2.push_back(stile_crd3_len);
        cg_subtile_op.mode_vals.push_back(stile_vals_len);

        for(int i = 0; i < pos1[1]; i++) {
            for(int j = pos2[i]; j < pos2[i + 1]; j++) {
                for(int k = pos3[j]; k < pos3[j + 1]; k++) {
                    cg_subtile_op.mode_2.push_back(crd3[k]);
                    cg_subtile_op.mode_vals.push_back(vals[k]);
                }
            }
        }

        op_mode0_end[id_store_op] = cg_subtile_op.mode_0.size();
        op_mode1_end[id_store_op] = cg_subtile_op.mode_1.size();
        op_mode2_end[id_store_op] = cg_subtile_op.mode_2.size();
        op_mode_vals_end[id_store_op] = cg_subtile_op.mode_vals.size();

        return cg_subtile_op;
}

cg_extents1 build_extents_1(cg_extents1 op_extents, int **store_subtile_op, int id_store_op){
    
        int *op_mode0_start =  store_subtile_op[0];
        int *op_mode0_end = store_subtile_op[1];
        int *op_mode_vals_start = store_subtile_op[2];
        int *op_mode_vals_end = store_subtile_op[3];
    
        op_extents.extents_mode_0.push_back(op_mode0_start[id_store_op]);
        op_extents.extents_mode_0.push_back(op_mode0_end[id_store_op]);
        op_extents.extents_mode_vals.push_back(op_mode_vals_start[id_store_op]);
        op_extents.extents_mode_vals.push_back(op_mode_vals_end[id_store_op]);
    
        return op_extents;
}

cg_extents2 build_extents_2(cg_extents2 op_extents, int **store_subtile_op, int id_store_op){

    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode1_start = store_subtile_op[2];
    int *op_mode1_end = store_subtile_op[3];
    int *op_mode_vals_start = store_subtile_op[4];
    int *op_mode_vals_end = store_subtile_op[5];

    op_extents.extents_mode_0.push_back(op_mode0_start[id_store_op]);
    op_extents.extents_mode_0.push_back(op_mode0_end[id_store_op]);
    op_extents.extents_mode_1.push_back(op_mode1_start[id_store_op]);
    op_extents.extents_mode_1.push_back(op_mode1_end[id_store_op]);
    op_extents.extents_mode_vals.push_back(op_mode_vals_start[id_store_op]);
    op_extents.extents_mode_vals.push_back(op_mode_vals_end[id_store_op]);

    return op_extents;
}

cg_extents3 build_extents_3(cg_extents3 op_extents, int **store_subtile_op, int id_store_op){

    int *op_mode0_start =  store_subtile_op[0];
    int *op_mode0_end = store_subtile_op[1];
    int *op_mode1_start = store_subtile_op[2];
    int *op_mode1_end = store_subtile_op[3];
    int *op_mode2_start = store_subtile_op[4];
    int *op_mode2_end = store_subtile_op[5];
    int *op_mode_vals_start = store_subtile_op[6];
    int *op_mode_vals_end = store_subtile_op[7];

    op_extents.extents_mode_0.push_back(op_mode0_start[id_store_op]);
    op_extents.extents_mode_0.push_back(op_mode0_end[id_store_op]);
    op_extents.extents_mode_1.push_back(op_mode1_start[id_store_op]);
    op_extents.extents_mode_1.push_back(op_mode1_end[id_store_op]);
    op_extents.extents_mode_2.push_back(op_mode2_start[id_store_op]);
    op_extents.extents_mode_2.push_back(op_mode2_end[id_store_op]);
    op_extents.extents_mode_vals.push_back(op_mode_vals_start[id_store_op]);
    op_extents.extents_mode_vals.push_back(op_mode_vals_end[id_store_op]);

    return op_extents;
}

int rtl_subtile2_print(subtile2 subtile_op, std::string output_path, std::string mode_name, int dim1, int dim2){

    ofstream pos1_file;
    pos1_file.open(output_path + "/subtile_" + mode_name + "_pos1.txt");
    for(int i = 0; i < subtile_op.pos1.size(); i++){
        pos1_file << subtile_op.pos1[i] << "\n";
    }
    pos1_file.close();

    ofstream pos2_file;
    pos2_file.open(output_path + "/subtile_" + mode_name + "_pos2.txt");
    for(int i = 0; i < subtile_op.pos2.size(); i++){
        pos2_file << subtile_op.pos2[i] << "\n";
    }
    pos2_file.close();

    ofstream crd1_file;
    crd1_file.open(output_path + "/subtile_" + mode_name + "_crd1.txt");
    for(int i = 0; i < subtile_op.crd1.size(); i++){
        crd1_file << subtile_op.crd1[i] << "\n";
    }
    crd1_file.close();

    ofstream crd2_file; 
    crd2_file.open(output_path + "/subtile_" + mode_name + "_crd2.txt");
    for(int i = 0; i < subtile_op.crd2.size(); i++){
        crd2_file << subtile_op.crd2[i] << "\n";
    }
    crd2_file.close();

    ofstream vals_file;
    vals_file.open(output_path + "/subtile_" + mode_name + "_vals.txt");
    for(int i = 0; i < subtile_op.vals.size(); i++){
        vals_file << subtile_op.vals[i] << "\n";
    }
    vals_file.close();

    ofstream subtile_file;
    subtile_file.open(output_path + "/subtile_" + mode_name + ".txt");
    subtile_file << dim1;
    subtile_file << "\n";
    subtile_file << dim2;
    subtile_file << "\n";
    subtile_file.close();

    return 0;

}

int rtl_output_subtile_printer(float *A_vals, int output_subtile_size, int curr_subtile_num, ofstream &output_gold_file){

    for (int pA = 0; pA < output_subtile_size; pA++) {
        output_gold_file << std::fixed << setprecision(30) << A_vals[pA];
        output_gold_file << "\n";
    }

    output_gold_file.close();
    
    return 0;
}

subtile1 tile_zero_op_1(subtile1 subtile_op1){
    subtile1 subtile_op;
    subtile_op.pos1.push_back(0);
    subtile_op.pos1.push_back(1);
    subtile_op.crd1.push_back(0);
    subtile_op.vals.push_back(0);
    return subtile_op;
}

subtile2 tile_zero_op_2(subtile2 subtile_op1){
    subtile2 subtile_op;
    subtile_op.pos1.push_back(0);
    subtile_op.pos1.push_back(1);
    subtile_op.pos2.push_back(0);
    subtile_op.pos2.push_back(1);
    subtile_op.crd1.push_back(0);
    subtile_op.crd2.push_back(0);
    subtile_op.vals.push_back(0);
    return subtile_op;
}

subtile3 tile_zero_op_3(subtile3 subtile_op1){
    subtile3 subtile_op;
    subtile_op.pos1.push_back(0);
    subtile_op.pos1.push_back(1);
    subtile_op.pos2.push_back(0);
    subtile_op.pos2.push_back(1);
    subtile_op.pos3.push_back(0);
    subtile_op.pos3.push_back(1);
    subtile_op.crd1.push_back(0);
    subtile_op.crd2.push_back(0);
    subtile_op.crd3.push_back(0);
    subtile_op.vals.push_back(0);
    return subtile_op;
}

tile1 tensor_zero_op_1(tile1 tile_op1){
    tile1 tile_op;
    tile_op.pos1.push_back(0);
    tile_op.pos1.push_back(1);
    tile_op.pos2.push_back(0);
    tile_op.pos2.push_back(1);
    tile_op.crd1.push_back(0);
    tile_op.crd2.push_back(0);
    tile_op.vals.push_back(0);
    return tile_op;
}

tile2 tensor_zero_op_2(tile2 tile_op1){
    tile2 tile_op;
    tile_op.pos1.push_back(0);
    tile_op.pos1.push_back(1);
    tile_op.pos2.push_back(0);
    tile_op.pos2.push_back(1);
    tile_op.pos3.push_back(0);
    tile_op.pos3.push_back(1);
    tile_op.pos4.push_back(0);
    tile_op.pos4.push_back(1);
    tile_op.crd1.push_back(0);
    tile_op.crd2.push_back(0);
    tile_op.crd3.push_back(0);
    tile_op.crd4.push_back(0);
    tile_op.vals.push_back(0);
    return tile_op;
}

tile3 tensor_zero_op_3(tile3 tile_op1){
    tile3 tile_op;
    tile_op.pos1.push_back(0);
    tile_op.pos1.push_back(1);
    tile_op.pos2.push_back(0);
    tile_op.pos2.push_back(1);
    tile_op.pos3.push_back(0);
    tile_op.pos3.push_back(1);
    tile_op.pos4.push_back(0);
    tile_op.pos4.push_back(1);
    tile_op.pos5.push_back(0);
    tile_op.pos5.push_back(1);
    tile_op.pos6.push_back(0);
    tile_op.pos6.push_back(1);
    tile_op.crd1.push_back(0);
    tile_op.crd2.push_back(0);
    tile_op.crd3.push_back(0);
    tile_op.crd4.push_back(0);
    tile_op.crd5.push_back(0);
    tile_op.crd6.push_back(0);
    tile_op.vals.push_back(0);
    return tile_op;
}

subtile1 process_csf_1(subtile1 subtile_op, int dim1){

    int pos1_size = subtile_op.pos1.size();
    int crd1_size = subtile_op.crd1.size();
    int vals_size  = subtile_op.vals.size();

    if(subtile_op.crd1[crd1_size - 1] != dim1){
        subtile_op.crd1.push_back(dim1);
        subtile_op.pos1[pos1_size - 1] += 1;
    }

    subtile_op.vals.push_back(1);

    return subtile_op;
}

subtile2 process_csf_2(subtile2 subtile_op, int dim1, int dim2){

    int pos1_size = subtile_op.pos1.size();
    int crd1_size = subtile_op.crd1.size();
    int pos2_size = subtile_op.pos2.size();
    int crd2_size = subtile_op.crd2.size();
    int vals_size  = subtile_op.vals.size();

    int is_present = (subtile_op.crd1[crd1_size - 1] == dim1) && (subtile_op.crd2[crd2_size - 1] == dim2);

    if(!is_present){
        if(subtile_op.crd1[crd1_size - 1] == dim1){
            subtile_op.pos2[pos2_size - 1] += 1; 
            subtile_op.crd2.push_back(dim2); 
            subtile_op.vals.push_back(1);
        }
        else{
            subtile_op.pos1[pos1_size - 1] += 1; 
            subtile_op.crd1.push_back(dim1); 
            subtile_op.pos2.push_back(subtile_op.pos2[pos2_size - 1] + 1);
            subtile_op.crd2.push_back(dim2); 
            subtile_op.vals.push_back(1);
        }
    }

    return subtile_op;
}

subtile3 process_csf_3(subtile3 subtile_op, int dim1, int dim2, int dim3){

    int pos1_size = subtile_op.pos1.size();
    int crd1_size = subtile_op.crd1.size();
    int pos2_size = subtile_op.pos2.size();
    int crd2_size = subtile_op.crd2.size();
    int pos3_size = subtile_op.pos3.size();
    int crd3_size = subtile_op.crd3.size();
    int vals_size = subtile_op.vals.size();

    int is_present = (subtile_op.crd1[crd1_size - 1] == dim1) && (subtile_op.crd2[crd2_size - 1] == dim2) && (subtile_op.crd3[crd3_size - 1] == dim3);

    if(!is_present){
        if(subtile_op.crd1[crd1_size - 1] == dim1){
            if(subtile_op.crd2[crd2_size - 1] == dim2){
                subtile_op.pos3[pos3_size - 1] += 1; 
                subtile_op.crd3.push_back(dim3); 
                subtile_op.vals.push_back(1);
            }
            else{
                subtile_op.pos2[pos2_size - 1] += 1; 
                subtile_op.crd2.push_back(dim2); 
                subtile_op.pos3.push_back(subtile_op.pos3[pos3_size - 1] + 1);
                subtile_op.crd3.push_back(dim3); 
                subtile_op.vals.push_back(1);
            }
        }
        else{
            subtile_op.pos1[pos1_size - 1] += 1; 
            subtile_op.crd1.push_back(dim1); 
            subtile_op.pos2.push_back(subtile_op.pos2[pos2_size - 1] + 1);
            subtile_op.crd2.push_back(dim2); 
            subtile_op.pos3.push_back(subtile_op.pos3[pos3_size - 1] + 1);
            subtile_op.crd3.push_back(dim3); 
            subtile_op.vals.push_back(1);
        }
    }

    return subtile_op;
}

