#include <cstdio>
#include "hardware_process_helper.h"
#include "halide_image_io.h"

#if defined(WITH_CPU)
   #include "divide.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "divide_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  OneInOneOut_ProcessController<uint8_t> processor("divide");

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        divide( proc.input, proc.output );
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
          divide_clockwork( proc.input, proc.output );

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

  // Add all defined functions
  processor.run_calls = functions;
  //processor.inputs_preset = true;

  processor.input   = Buffer<uint8_t>(64, 64);
  processor.output  = Buffer<uint8_t>(64, 64);

  processor.input(0, 0) = -2;
  processor.input(0, 1) = -1;
  processor.input(0, 2) = 0;
  processor.input(0, 3) = 1;
  processor.input(0, 4) = 2;
  
  
  auto return_value = processor.process_command(argc, argv);

  std::cout << "out(0,0) = " << +processor.output(0, 0) << std::endl;
  std::cout << "out(0,1) = " << +processor.output(0, 1) << std::endl;
  std::cout << "out(0,2) = " << +processor.output(0, 2) << std::endl;
  std::cout << "out(0,3) = " << +processor.output(0, 3) << std::endl;
  std::cout << "out(0,4) = " << +processor.output(0, 4) << std::endl;

  return return_value;
  
}
