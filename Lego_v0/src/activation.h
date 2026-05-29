#ifndef ACTIVATION_H
#define ACTIVATION_H
#include <vector>
#include "bf16_op.h"
#include "gen_lut.h"

int apply_output_relu(float *input, int size);
int apply_input_relu(std::vector<float> &input);
int apply_input_recip(std::vector<float> &input);
void apply_output_exp(float *input, int size);
void apply_output_leakyrelu(float *input, int size);
void apply_output_elu(float *input, int size);

#endif