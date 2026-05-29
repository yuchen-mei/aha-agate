#include "cg_mem_op.h"

cg_subtile2 cg_tile_mem_op_2(cg_subtile2 cg_subtile_op, int **store_subtile_op, tile2 tile_op, int index, int id_store_op){

    int *pos1 = tile_op.pos3.data();
    int *crd1 = tile_op.crd3.data();
    int *pos2 = tile_op.pos4.data();
    int *crd2 = tile_op.crd4.data();
    float *vals = tile_op.vals.data();

    int stile_pos1_len = 2;	
	int stile_pos2_len = pos1[index + 1] - pos1[index] + 1;
	int stile_crd1_len = pos1[index + 1] - pos1[index];
	int stile_crd2_len = pos2[pos1[index + 1]] - pos2[pos1[index]];
	int stile_vals_len = pos2[pos1[index + 1]] - pos2[pos1[index]];    
    
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
	cg_subtile_op.mode_0.push_back(pos1[index] - pos1[index]);
	cg_subtile_op.mode_0.push_back(pos1[index + 1] - pos1[index]);
	cg_subtile_op.mode_0.push_back(stile_crd1_len);

    for(int i = pos1[index]; i < pos1[index + 1]; i++) {
		cg_subtile_op.mode_0.push_back(crd1[i]);
    }

	cg_subtile_op.mode_1.push_back(stile_pos2_len); 
    for(int i = pos1[index]; i <= pos1[index + 1]; i++) {
        cg_subtile_op.mode_1.push_back(pos2[i] - pos2[pos1[index]]);
    }

	cg_subtile_op.mode_1.push_back(stile_crd2_len);
	cg_subtile_op.mode_vals.push_back(stile_vals_len);

	for(int i = pos1[index]; i < pos1[index + 1]; i++) {
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