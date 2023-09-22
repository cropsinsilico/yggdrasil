#include <stdio.h>

int modelA_function(float in_val, float* out_val) {
  out_val[0] = in_val;
  printf("modelA_function(%f) = %f\n", in_val, *out_val);
  return 0;
}
