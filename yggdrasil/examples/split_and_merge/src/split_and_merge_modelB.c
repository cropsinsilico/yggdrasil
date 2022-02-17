#include <stdio.h>
#include <math.h>

float modelB_function(float in_val) {
  float out_val = 3 * in_val;
  printf("modelB_function(%f) = %f\n", in_val, out_val);
  return out_val;
}
