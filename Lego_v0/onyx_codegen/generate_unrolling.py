import sys
import shutil

import io_placement
import raw_to_h_16
import bs_to_h
import meta
import os

def codegen_unrolling(design_file, out_file, app_name):

    inputs, outputs, input_order, output_order, bitstream_name = meta.meta_scrape(design_file)
    io_placement.unrolling(inputs, outputs, input_order, output_order, out_file, app_name)
