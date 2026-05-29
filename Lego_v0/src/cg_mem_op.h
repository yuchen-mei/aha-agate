#ifndef CG_MEM_OP_H
#define CG_MEM_OP_H

cg_subtile2 cg_tile_mem_op_2(cg_subtile2 cg_subtile_op, int **store_subtile_op, tile2 tile_op, int index, int id_store_op); 
cg_extents2 build_extents_2(cg_extents2 op_extents, int **store_subtile_op, int id_store_op);

#endif