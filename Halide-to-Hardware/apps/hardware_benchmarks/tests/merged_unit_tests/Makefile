UNAME = $(shell uname)

PNG_LIB = $(shell libpng-config --cflags --ldflags)

THIS_MAKEFILE = $(realpath $(filter %Makefile, $(MAKEFILE_LIST)))
ROOT_DIR = $(strip $(shell dirname $(THIS_MAKEFILE)))
COREIR_DIR ?= $(ROOT_DIR)/../../../../../coreir
DEBUG_SIM ?= 0
COREIR_CXX_FLAGS = -I$(COREIR_DIR)/include
COREIR_LD_FLAGS = -L$(COREIR_DIR)/lib -Wl,-rpath,$(COREIR_DIR)/lib -lcoreir-commonlib -lcoreir -lcoreirsim -lcoreir-float
ifeq ($(UNAME), Darwin)
	COREIR_LD_FLAGS += -headerpad_max_install_names
endif

COREIR_CXX_FLAGS += -DVERBOSE=$(DEBUG_SIM)


all:
	$(CXX) test_main.cpp -g $(COREIR_CXX_FLAGS) $(COREIR_LD_FLAGS)  -I ../../../../tools/ -I ../../../../include -L ../../../../bin -lHalide $(PNG_LIB) -ljpeg -lpthread -ldl -o all-tests -std=c++17
ifeq ($(UNAME), Darwin)
endif
