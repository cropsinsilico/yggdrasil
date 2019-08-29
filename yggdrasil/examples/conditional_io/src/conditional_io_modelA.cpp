#include <iostream>

int model_function(float in_val, float* out_val) {
  out_val[0] = in_val;
  std::cout << "modelA_function(" << in_val << ") = " << *out_val << std::endl;
  return 0;
}
