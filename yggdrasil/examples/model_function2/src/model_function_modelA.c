#include <stdio.h>

int model_function(float x, float* y) {
  y[0] = x + 1.0;
  printf("Model A: %f -> %f\n", x, *y);
  return 0;

}
