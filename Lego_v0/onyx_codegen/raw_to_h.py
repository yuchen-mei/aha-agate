# script to convert bitstream to h file

import sys

data_lines = []
input_data = sys.argv[1]
output_data = sys.argv[2]
data_file_str = input_data.replace('.raw','')

with open(input_data, "rb") as f:
    raw = f.read()
raw = [hex(c) for c in raw]
length_input_data = len(raw)
raw_input_data = ', '.join(raw)


with open(output_data, "rb") as f:
    raw = f.read()
raw = [hex(c) for c in raw]
length_output_data = len(raw)
raw_output_data = ', '.join(raw)



f = open(data_file_str+"_script.h", "w")
# defines
f.write("#ifndef DATA_H\n")
f.write("#define DATA_H\n\n")

# input array
f.write("unsigned char app_input_data[] = { \n")
f.write(raw_input_data)
f.write("\n};\n")

f.write("const unsigned int app_input_data_size =  " + str(length_input_data) +  ";\n")

# output array
f.write("unsigned char app_gold_data[] = { \n")
f.write(raw_output_data)
f.write("\n};\n")

f.write("const unsigned int app_gold_data_size =  " + str(length_output_data) +  ";\n")


# defines
f.write("#endif // DATA_H\n\n")


