# script to convert bitstream to h file

import itertools


def convert_image(input_data, output_data, data_file_str):

    raw_input_data_list = []
    raw_input_data_size_list = []
    raw_output_data_list = []
    raw_output_data_size_list = []

    for input in input_data:
        with open(input, "rb") as f:
            raw = f.read()
        raw = [hex(c) for c in raw]

        raw1 = raw[0::2]
        raw2 = raw[1::2]
        raw_image0 = []

        for (raw_i, raw_j) in itertools.zip_longest(raw1, raw2):
            raw_j = raw_j[2:]
            if(len(raw_j) == 1):
                raw_j = '0'+ raw_j
            raw_final = raw_i + raw_j
            raw_image0.append(raw_final)

        raw2 = raw_image0 

        length_input_data = len(raw2)
        raw_input_data_size_list.append(length_input_data)
        raw_input_data = ', '.join(raw2)
        raw_input_data_list.append(raw_input_data)

    for output in output_data:
        with open(output, "rb") as f:
            raw = f.read()
        raw = [hex(c) for c in raw]

        raw1 = raw[0::2]
        raw2 = raw[1::2]
        raw_image0 = []

        for (raw_i, raw_j) in itertools.zip_longest(raw1, raw2):
            raw_j = raw_j[2:]
            if(len(raw_j) == 1):
                raw_j = '0'+ raw_j
            raw_final = raw_i + raw_j
            raw_image0.append(raw_final)

        raw2 = raw_image0 

        length_output_data = len(raw2)
        raw_output_data_size_list.append(length_output_data)
        raw_output_data = ', '.join(raw2)
        raw_output_data_list.append(raw_output_data)


    f = open(data_file_str+"_input_script.h", "w")
    # defines
    f.write("#ifndef DATA_H\n")
    f.write("#define DATA_H\n\n")

    for idx, input in enumerate(input_data):
        input_str = input.replace("hw_", "")
        input_str = input_str.replace(".raw", "")
        f.write(f"const uint16_t app_{input_str}_data[] = {{ \n")
        f.write(raw_input_data_list[idx])
        f.write("\n};\n")
        f.write(f"const unsigned int app_{input_str}_data_size =  " + str(raw_input_data_size_list[idx]) +  ";\n")

    for idx, output in enumerate(output_data):
        output_str = output.replace("hw_", "")
        output_str = output_str.replace(".raw", "")
        f.write(f"const uint16_t app_{output_str}_data[] = {{ \n")
        f.write(raw_output_data_list[idx])
        f.write("\n};\n")
        f.write(f"const unsigned int app_{output_str}_data_size =  " + str(raw_output_data_size_list[idx]) +  ";\n")


    # defines
    f.write("#endif // DATA_H\n\n")


if __name__ == '__main__':
    convert_image(input_data, output_data)
