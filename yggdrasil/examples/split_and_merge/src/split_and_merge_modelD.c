#include <stdio.h>
#include <math.h>

int modelD_function(float in_val1, float in_val2, float* in_val1_copy, float* in_val2_copy, float* out_val) {
  in_val1_copy[0] = in_val1;
  in_val2_copy[0] = in_val2;
  out_val[0] = in_val1 + in_val2;
  printf("modelD_function(%f, %f) = %f\n", in_val1, in_val2, *out_val);
  return 0;
}
