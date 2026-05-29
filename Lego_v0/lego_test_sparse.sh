rm -rf lego_scratch/ 
mkdir lego_scratch/ 
rm -rf main.cpp
rm -rf gold.cpp
python3 main.py -p $1 -t $2 -g s -m rtl -w 
g++ -o main main.cpp src/data_parser.cpp src/mem_op.cpp 
./main tiling 
g++ -o gold gold.cpp src/data_parser.cpp src/mem_op.cpp 
./gold