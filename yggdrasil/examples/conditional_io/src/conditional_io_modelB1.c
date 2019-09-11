#include <stdio.h>
#include <math.h>

int modelB_function1(float in_val, float* in_val_copy, float* out_val) {
  // Only valid if in_val <= 2
  in_val_copy[0] = in_val;
  out_val[0] = pow(in_val, 2);
  printf("modelB_function1(%f) = %f\n", in_val, *out_val);
  return 0;
}
