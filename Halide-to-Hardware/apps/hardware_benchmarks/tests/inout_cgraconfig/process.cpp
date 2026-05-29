#include <iostream>
#include <cstdio>
#include "hardware_process_helper.h"
#include "halide_image_io.h"

#if defined(WITH_CPU)
   #include "inout_cgraconfig.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "inout_cgraconfig_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  ManyInOneOut_ProcessController<uint8_t> processor("inout_cgraconfig", {"input.png", "kernel.png"});

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        inout_cgraconfig(proc.inputs["input.png"], proc.inputs["kernel.png"], proc.output);
      };
      functions["cpu"] = [&](){ cpu_process( processor ); } ;
  #endif
  
  #if defined(WITH_COREIR)
      auto coreir_process = [&]( auto &proc ) {
          run_coreir_on_interpreter<>( "bin/design_top.json",
                                       proc.inputs["input.png"], proc.output,
                                       "self.in_arg_0_0_0", "self.out_0_0" );
      };
      functions["coreir"] = [&](){ coreir_process( processor ); };
  #endif
  
  #if defined(WITH_CLOCKWORK)
      auto clockwork_process = [&]( auto &proc ) {
          inout_cgraconfig_clockwork(proc.inputs["input.png"], proc.inputs["kernel.png"], proc.output);

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

    // Add all defined functions
    processor.run_calls = functions;

    int X = 64;
    int Y = 64;
    int K_X = 64;
    int K_Y = 64;
    processor.inputs_preset = true;
  
    processor.inputs["input.png"] = Buffer<uint8_t>(X, Y);
    auto input_copy_stencil = processor.inputs["input.png"];
    for (int y = 0; y < input_copy_stencil.dim(1).extent(); y++) {
      for (int x = 0; x < input_copy_stencil.dim(0).extent(); x++) {
          input_copy_stencil(x, y) = x + y;
          //input_copy_stencil(z, x, y) = 1;
        } }

    std::cout << "input has dims: " << processor.inputs["input.png"].dim(0).extent() << "x"
              << processor.inputs["input.png"].dim(1).extent() << "\n";

  
    processor.inputs["kernel.png"] = Buffer<uint8_t>(K_X, K_Y);
    auto kernel_copy_stencil = processor.inputs["kernel.png"];
    for (int y = 0; y < kernel_copy_stencil.dim(1).extent(); y++) {
      for (int x = 0; x < kernel_copy_stencil.dim(0).extent(); x++) {
            kernel_copy_stencil(x, y) = x - y;
            //kernel_copy_stencil(z, w, x, y) = 1;
          } }
  
    std::cout << "kernel has dims: " << processor.inputs["kernel.png"].dim(0).extent() << "x"
              << processor.inputs["kernel.png"].dim(1).extent() << "\n";

    processor.output = Buffer<uint8_t>(X,Y);

    return processor.process_command(argc, argv);
}  
