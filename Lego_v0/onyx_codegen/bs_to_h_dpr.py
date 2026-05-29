# script to convert bitstream to h file

import sys

unroll = 8

def add_value_to_bits(address_str, value):
    # Convert the address string to an integer
    address = int(address_str, 16)

    # Extract bits 8-15
    bits_8_to_15 = (address >> 8) & 0xFF

    # Add the value to bits 8-15
    bits_8_to_15 += value

    # Clear bits 8-15 in the original address
    address &= ~(0xFF << 8)

    # Set the updated bits 8-15 in the original address
    address |= (bits_8_to_15 << 8)

    # Convert the address back to a string representation
    updated_address_str = hex(address)[2:].zfill(8).upper()

    return updated_address_str



def convert_bs(bs_file_name, new_name):

    bs_lines = []
    bs_file_str = new_name

    with open(bs_file_name) as bs_file:
        for bs_line in bs_file:
            bs_lines.append(bs_line)

    f = open(bs_file_str+"_script.h", "w")
    # defines
    f.write("#ifndef BITSTREAM_H\n")
    f.write("#define BITSTREAM_H\n\n")
    f.write("const int app_size = " + str(len(bs_lines)*unroll) + ";\n\n")

 
    # addr array
    f.write("uint32_t app_addrs_script[] = {\n")

    for i in range(unroll):
        for line in bs_lines:
            strings = line.split()
            new_addr = add_value_to_bits(strings[0], 4*i)
            f.write("  0x" + new_addr + ",\n")
    f.write("};\n\n")


    # data array
    f.write("uint32_t app_datas_script[] = {\n")
    for i in range(unroll):
        for line in bs_lines:
            strings = line.split()
            f.write("  0x" + strings[1] + ",\n")
    f.write("};\n\n")

    # defines
    f.write("#endif  // BITSTREAM_H\n")


if __name__ == '__main__':
    bs_file_name = "pointwise.bs"
    new_name = "pointwise_gops2_unroll"
    convert_bs(bs_file_name, new_name)
