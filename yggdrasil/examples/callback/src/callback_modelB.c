#include <stdio.h>
#include <math.h>

int modelB_function(float in_val, float* in_val_copy, float* out_val) {
  in_val_copy[0] = in_val;
  out_val[0] = 3 * in_val;
  printf("modelB_function(%f) = %f\n", in_val, *out_val);
  return 0;
}
