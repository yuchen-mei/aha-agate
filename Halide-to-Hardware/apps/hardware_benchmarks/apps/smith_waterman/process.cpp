#include <cstdio>
#include "hardware_process_helper.h"
#include "halide_image_io.h"

#if defined(WITH_CPU)
   #include "smith_waterman.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "smith_waterman_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  ManyInOneOut_ProcessController<uint16_t> processor("smith_waterman", {"ref.png", "query.png"});

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        smith_waterman( proc.inputs["ref.png"], proc.inputs["query.png"], proc.output );
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
          smith_waterman_clockwork( proc.inputs["input.png"], proc.inputs["input.png"], proc.output );

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

  // Add all defined functions
  processor.run_calls = functions;
  processor.inputs_preset = true;

  int output_size = 10;
  int input_size = output_size + 1;
  processor.inputs["ref.png"] = Buffer<uint16_t>(input_size);
  processor.inputs["query.png"] = Buffer<uint16_t>(input_size);

  for (int i=0; i<input_size; ++i) {
    processor.inputs["ref.png"](i) = 3*i;
    processor.inputs["query.png"](i) = 7*i - 5;
  }

  processor.output  = Buffer<uint16_t>(output_size, output_size);
  
  return processor.process_command(argc, argv);
  
}
