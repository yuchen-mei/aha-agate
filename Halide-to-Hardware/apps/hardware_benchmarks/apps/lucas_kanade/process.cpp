#include <cmath>
#include <iostream>
#include <cstdio>
#include "hardware_process_helper.h"
#include "halide_image_io.h"

#if defined(WITH_CPU)
   #include "lucas_kanade.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "lucas_kanade_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  ManyInOneOut_ProcessController<uint8_t,float> processor("lucas_kanade", {"input0.png", "input1.png"});

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        lucas_kanade(proc.inputs["input0.png"], proc.inputs["input1.png"], proc.output);
      };
      functions["cpu"] = [&](){ cpu_process( processor ); } ;
  #endif
  
  #if defined(WITH_COREIR)
      auto coreir_process = [&]( auto &proc ) {
          run_coreir_on_interpreter<>( "bin/design_top.json",
                                       proc.inputs["input0.png"], proc.output,
                                       "self.in_arg_0_0_0", "self.out_0_0" );
      };
      functions["coreir"] = [&](){ coreir_process( processor ); };
  #endif
  
  #if defined(WITH_CLOCKWORK)
      auto clockwork_process = [&]( auto &proc ) {
          lucas_kanade_clockwork(proc.inputs["input0.png"], proc.inputs["input1.png"], proc.output);

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

    // Add all defined functions
    processor.run_calls = functions;

    processor.inputs["input0.png"] = Buffer<uint8_t>(64,64);
    processor.inputs["input1.png"] = Buffer<uint8_t>(64,64);

    processor.inputs_preset = true;
    processor.output = Buffer<float>(64, 64, 2);

    return processor.process_command(argc, argv);
}
