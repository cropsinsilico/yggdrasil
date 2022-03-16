#include <stdio.h>

int modelA_function(float in_val, float* out_val1, float* out_val2) {
  out_val1[0] = 2 * in_val;
  out_val2[0] = 3 * in_val;
  printf("modelA_function(%f) = (%f, %f)\n", in_val, *out_val1, *out_val2);
  return 0;
}
