cmake_minimum_required(VERSION 3.0)
project(leidenalg)

set(CMAKE_CXX_STANDARD 14)
include(CheckCXXCompilerFlag)

set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/")
find_package(IGRAPH REQUIRED)

include_directories(include)

add_library(leidenalg
        include/CPMVertexPartition.h
        include/GraphHelper.h
        include/LinearResolutionParameterVertexPartition.h
        include/ModularityVertexPartition.h
        include/MutableVertexPartition.h
        include/Optimiser.h
        include/RBConfigurationVertexPartition.h
        include/RBERVertexPartition.h
        include/ResolutionParameterVertexPartition.h
        include/SignificanceVertexPartition.h
        include/SurpriseVertexPartition.h
        src/CPMVertexPartition.cpp
        src/GraphHelper.cpp
        src/LinearResolutionParameterVertexPartition.cpp
        src/ModularityVertexPartition.cpp
        src/MutableVertexPartition.cpp
        src/Optimiser.cpp
        src/RBConfigurationVertexPartition.cpp
        src/RBERVertexPartition.cpp
        src/ResolutionParameterVertexPartition.cpp
        src/SignificanceVertexPartition.cpp
        src/SurpriseVertexPartition.cpp)

SET(CMAKE_EXE_LINKER_FLAGS "-static")
target_link_libraries(leidenalg PRIVATE ${IGRAPH_LIBRARIES})
target_include_directories(leidenalg PRIVATE ${IGRAPH_INCLUDES})
CHECK_CXX_COMPILER_FLAG(-static-libgcc COMPILER_STATIC)
if (${COMPILER_STATIC})
target_link_libraries(leidenalg PUBLIC -static-libgcc -static-libstdc++)
endif()

set_target_properties(leidenalg PROPERTIES COMPILE_FLAGS
                      "-Wno-unused-parameter -Wno-endif-labels -Wno-sign-compare")
