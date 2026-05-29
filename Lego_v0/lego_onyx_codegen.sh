rm -rf lego_scratch/ 
mkdir lego_scratch/ 
rm -rf main.cpp
python3 main.py --mode onyx --program $1 --tensor $2 --bitstream $3 --design_meta $4 --reg_write $5 --output_dir $6
g++ -o main main.cpp src/data_parser.cpp src/mem_op.cpp 
./main 
