# Halide-to-Hardware Usage Instructions

## Installation
For a full halide-to-hardware compiler setup on Kiwi, please browse [here](INSTALL.md).

## Applications
Applications are split into two folders in `Halide-to-Hardware/apps/hardware_benchmarks`:
- `tests` features simpler applications like conv_3_3.
- `apps` features more complex applications like resnet.

## Running the Pipeline
In order to run a full Halide-to-Hardware pipeline, follow these steps:
1. From within the halide-to-hardware compiler's top directory, change into the application directory: `cd apps/hardware_benchmarks/path/to/app/`
2. Generate target design: `make compiler && make <TARGET>` where `TARGET` can be `cpu`, `clockwork`, `coreir`, etc.
3. Run pipeline with implemented hardware kernels: `make run-<TARGET>` (e.g. `make run-clockwork`)
4. Compare output to cpu output: `make compare-<TARGET>` (e.g. `make compare-clockwork`)

Here is a list of the different make targets:
<pre><code>make clean               # remove generated files (bin directory)
     compiler            # compile updates to Halide compiler
     generator           # create Halide generator
     cpu                 # create CPU design
     clockwork           # create clockwork design
     image               # create an image with random data
     run-cpu             # create output file using CPU implementation
     run-clockwork       # create output file using clockwork implementation
     compare-clockwork   # compare Clockwork output file to CPU output image
     eval                # evaluate runtime </code></pre>

The definition of all of these targets can be found in `apps/hardware_benchmarks/hw_support/hardware_targets.mk`.

## Halide-to-Hardware Directory Tree for Apps:
<pre><code>Halide-to-Hardware
└── apps
    └── hardware_benchmarks                    // contains simpler test cases
        ├── apps                               // contains all apps compiled to coreir
        └── tests                              // contains all simpler test cases
            └── conv_3_3                       // one of the apps: does 3x3 convolution
                ├── Makefile                   // specifies commands for 'make'
                ├── conv_3_3_generator.cpp     // contains Halide algorithm and schedule
                ├── input.png                  // input image for testing
                ├── process.cpp                // runs input image with design to create ouput image
                ├── golden                     // this holds all expected output files
                │   └── golden_output.png      // output image expected
                │
                └── bin                        //// Running 'make clockwork' generates in this folder:
                    ├── output_cpu.png         // output image created using CPU implementation
                    └── output_clockwork.png   // output image created during testing; should be equivalent to output_cpu.png</code></pre>
