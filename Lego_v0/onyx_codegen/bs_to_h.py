# script to convert bitstream to h file

import sys


def convert_bs(bs_file_name, f):

    bs_lines = []
    with open(bs_file_name) as bs_file:
        for bs_line in bs_file:
            bs_lines.append(bs_line)

    # defines
    f.write("#ifndef BITSTREAM_H\n")
    f.write("#define BITSTREAM_H\n\n")
    f.write("const int app_size = " + str(len(bs_lines)) + ";\n\n")

    # addr array
    f.write("const uint32_t app_addrs_script[] = {\n")
    for line in bs_lines:
        strings = line.split()
        f.write("  0x" + strings[0] + ",\n")
    f.write("};\n\n")


    # data array
    f.write("const uint32_t app_datas_script[] = {\n")
    for line in bs_lines:
        strings = line.split()
        f.write("  0x" + strings[1] + ",\n")
    f.write("};\n\n")

    # defines
    f.write("#endif  // BITSTREAM_H\n")
