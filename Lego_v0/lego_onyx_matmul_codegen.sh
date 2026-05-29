rm -rf lego_scratch/ 
mkdir lego_scratch/ 
rm -rf main.cpp
python3 main.py --mode rtl 
g++ -o main main.cpp src/data_parser.cpp src/mem_op.cpp 
./main tiling
