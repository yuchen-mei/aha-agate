#include <iostream>
#include <math.h>
#include <cstdio>
#include "hardware_process_helper.h"
#include "halide_image_io.h"

#if defined(WITH_CPU)
   #include "relu_layer.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "relu_layer_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  ManyInOneOut_ProcessController<int16_t> processor("relu_layer", {"input.mat", "input_bias.mat"});

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        relu_layer(proc.inputs["input.mat"], proc.inputs["input_bias.mat"], proc.output);
      };
      functions["cpu"] = [&](){ cpu_process( processor ); } ;
  #endif
  
  #if defined(WITH_COREIR)
      auto coreir_process = [&]( auto &proc ) {
          run_coreir_on_interpreter<>( "bin/design_top.json",
                                       proc.inputs["input.mat"], proc.output,
                                       "self.in_arg_0_0_0", "self.out_0_0" );
      };
      functions["coreir"] = [&](){ coreir_process( processor ); };
  #endif
  
  #if defined(WITH_CLOCKWORK)
      auto clockwork_process = [&]( auto &proc ) {
          relu_layer_clockwork(proc.inputs["input.mat"], proc.inputs["input_bias.mat"], proc.output);

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

  auto OX = getenv("out_img");
  auto OC = getenv("n_oc");
  auto out_img = OX ? atoi(OX) : 56;
  auto n_oc = OC ? atoi(OC) : 32;
      
  // Add all defined functions
  processor.run_calls = functions;

  processor.inputs["input.mat"]        = Buffer<int16_t>(n_oc, out_img, out_img);
  processor.inputs["input_bias.mat"]   = Buffer<int16_t>(n_oc, out_img, out_img);
  processor.output                     = Buffer<int16_t>(n_oc, out_img, out_img);

  processor.inputs_preset = true;
  int max_rand = std::pow(2,8) - 1;
  
  for (int y = 0; y < processor.inputs["input.mat"].dim(2).extent(); y++) {
    for (int x = 0; x < processor.inputs["input.mat"].dim(1).extent(); x++) {
      for (int w = 0; w < processor.inputs["input.mat"].dim(0).extent(); w++) {
        
        if (rand() % 100 < 60) { // 60% zero, else rand
          processor.inputs["input.mat"](w, x, y) = 0;
        } else {
          processor.inputs["input.mat"](w, x, y) = (rand() % (2*max_rand)) - max_rand;
        }
        
        if (rand() % 100 < 60) { // 60% zero, else rand
          processor.inputs["input_bias.mat"](w, x, y) = 0;
        } else {
          processor.inputs["input_bias.mat"](w, x, y) = (rand() % (2*max_rand)) - max_rand;
        }
      }
    }
  }
  
  return processor.process_command(argc, argv);
  
}
