#include <cstdio>
#include <fstream>
#include "coreir.h"
#include "hardware_process_helper.h"
#include "halide_image_io.h"
#include "hw_support_utils.h"

#if defined(WITH_CPU)
   #include "pointwise.h"
#endif

#if defined(WITH_COREIR)
    #include "coreir_interpret.h"
#endif

#if defined(WITH_CLOCKWORK)
    #include "pointwise_clockwork.h"
#endif

using namespace Halide::Tools;
using namespace Halide::Runtime;

int main( int argc, char **argv ) {
  std::map<std::string, std::function<void()>> functions;
  OneInOneOut_ProcessController<uint8_t> processor("pointwise");

  #if defined(WITH_CPU)
      auto cpu_process = [&]( auto &proc ) {
        pointwise( proc.input, proc.output );
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
          pointwise_clockwork( proc.input, proc.output );

      };
      functions["clockwork"] = [&](){ clockwork_process( processor ); };
  #endif

  // Add all defined functions
  processor.run_calls = functions;

  processor.input   = Buffer<uint8_t>(64, 64);
  processor.output  = Buffer<uint8_t>(64, 64);

  // Create glb bank config file for packing
  // Generate glb_bank_config.json if "USE_GLB_BANK_CONFIG" is 1
  std::cout << "Checking for GLB bank configuration..." << std::endl;
  std::cout << "USE_GLB_BANK_CONFIG = " << getenv("USE_GLB_BANK_CONFIG") << std::endl;
  if (getenv("USE_GLB_BANK_CONFIG") && std::stoi(getenv("USE_GLB_BANK_CONFIG"))) {
      std::vector<int> hw_input_stencil_pos = parse_glb_bank_config_num_list("HW_INPUT_STENCIL_POS");
      std::vector<int> hw_output_stencil_pos = parse_glb_bank_config_num_list("HW_OUTPUT_STENCIL_POS");

      std::vector<int> hw_input_stencil_packed = parse_glb_bank_config_num_list("HW_INPUT_STENCIL_PACKED");
      std::vector<int> hw_output_stencil_packed = parse_glb_bank_config_num_list("HW_OUTPUT_STENCIL_PACKED");

      // Create the glb_bank_config.json structure
      json config = {
          {"inputs", {
              {
                  {"hw_input_stencil", {
                      {"x_coord", hw_input_stencil_pos},
                      {"E64_packed", hw_input_stencil_packed}
                  }}
              }
          }},
          {"outputs", {
              {
                  {"hw_output_stencil", {
                      {"x_coord", hw_output_stencil_pos},
                      {"E64_packed", hw_output_stencil_packed}
                  }}
              }
          }}
      };

      std::ofstream file("bin/glb_bank_config.json");
      if (file.is_open()) {
          file << config.dump(4) << std::endl;
          file.close();
          std::cout << "Successfully wrote to bin/glb_bank_config.json" << std::endl;
      } else {
          std::cerr << "Unable to open file for writing." << std::endl;
          return 1;
      }
  }

  return processor.process_command(argc, argv);

}
