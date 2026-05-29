file_path = "tensorX/tensor_X_mode_vals_0.txt"

# Read the content of the text file
with open(file_path, 'r') as file:
    content = file.read().strip()

# Split the content into individual hexadecimal values
hex_values = content.split()

# Convert hexadecimal values to C-style string literals with "0x" prefix
c_array = "{"
for hex_value in hex_values:
    c_array += f'0x{hex_value}, '
c_array = c_array.rstrip(', ') + "};"

# Output the C array
print(c_array)
