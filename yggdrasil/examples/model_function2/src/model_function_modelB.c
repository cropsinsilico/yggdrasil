#include <stdio.h>

int model_function(float *x, uint64_t length_x,
		   float **y, uint64_t *length_y) {
  uint64_t i;
  length_y[0] = length_x;
  y[0] = (float*)malloc(length_x * sizeof(float));
  for (i = 0; i < length_x; i++)
    (*y)[i] = x[i] + 2.0;
  printf("Model B: [");
  for (i = 0; i < length_x; i++)
    printf("%f ", x[i]);
  printf("] -> [");
  for (i = 0; i < length_x; i++)
    printf("%f ", (*y)[i]);
  printf("]\n");
  return 0;

}
