#include <stdio.h>

int model_function(bool a, double b, generic_t c,
		   double** out, size_t* out_length) {
  out_length[0] = 3;
  out[0] = (double*)realloc(out[0], 3 * sizeof(double));
  for (int i = 0; i < 3; i++) {
    if (a)
      out[0][i] = b * pow(i, generic_map_get_double(c, "c1"));
    else
      out[0][i] = b * pow(i, generic_map_get_double(c, "c2"));
  }
  return 1;
}
