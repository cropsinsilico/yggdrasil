#include <stdio.h>

int model_function(bool a, double b, generic_t c,
		   bool* d, double* e,
		   double** f, size_t* f_length) {
  d[0] = (!a);
  e[0] = generic_map_get_double(c, "c1");
  f_length[0] = 3;
  f[0] = (double*)realloc(f[0], 3 * sizeof(double));
  for (int i = 0; i < 3; i++) {
    if (a)
      f[0][i] = b * pow(i, generic_map_get_double(c, "c1"));
    else
      f[0][i] = b * pow(i, generic_map_get_double(c, "c2"));
  }
  return 1;
}
