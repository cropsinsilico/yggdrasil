#include <iostream>

int modelB_function1(float in_val, float* in_val_copy, float* out_val) {
  // Only valid if in_val <= 2
  in_val_copy[0] = in_val;
  out_val[0] = in_val**2;
  std::cout << "modelB_function1(" << in_val << ") = " << *out_val << std::endl;
  return 0;
}
