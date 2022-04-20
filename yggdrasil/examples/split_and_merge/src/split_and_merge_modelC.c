#include <stdio.h>
#include <math.h>

float modelC_function(float in_val) {
  float out_val = 4 * in_val;
  printf("modelC_function(%f) = %f\n", in_val, out_val);
  return out_val;
}
