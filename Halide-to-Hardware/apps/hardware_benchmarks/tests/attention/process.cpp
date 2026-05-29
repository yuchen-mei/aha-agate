#include <cstdio>
#include "hardware_process_helper.h"
#include "halide_image_io.h"

#if defined(WITH_CPU)
   #include "attention.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "attention_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  ManyInOneOut_ProcessController<uint8_t> processor("attention", {"Q.png", "K.png", "V.png"});

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        attention( proc.inputs["Q.png"], proc.inputs["K.png"], proc.inputs["V.png"], proc.output );
      };
      functions["cpu"] = [&](){ cpu_process( processor ); } ;
  #endif
  
  #if defined(WITH_COREIR)
      auto coreir_process = [&]( auto &proc ) {
          run_coreir_on_interpreter<>( "bin/design_top.json",
                                       proc.input, proc.output,
                                       "self.in_arg_0_0_0", "self.out_0_0" );
      };
      functions["coreir"] = [&](){ coreir_process( processor ); };
  #endif
  
  #if defined(WITH_CLOCKWORK)
      auto clockwork_process = [&]( auto &proc ) {
          attention_clockwork( proc.inputs["Q.png"], proc.inputs["K.png"], proc.inputs["V.png"], proc.output );

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

  // Add all defined functions
  processor.run_calls = functions;
  processor.inputs_preset = true;

  processor.inputs["Q.png"]   = Buffer<uint8_t>(64, 64);
  processor.inputs["K.png"]   = Buffer<uint8_t>(64, 64);
  processor.inputs["V.png"]   = Buffer<uint8_t>(64, 64);
  processor.output            = Buffer<uint8_t>(64, 64);
  
 return processor.process_command(argc, argv);
  
}
