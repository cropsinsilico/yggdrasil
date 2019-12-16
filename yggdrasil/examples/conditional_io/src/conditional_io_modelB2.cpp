#include <iostream>
#include <math.h>

int modelB_function2(float in_val, float &in_val_copy, float &out_val) {
  // Only valid if in_val > 2
  in_val_copy = in_val;
  out_val = 2 * pow(in_val, 2);
  std::cout << "modelB_function2(" << in_val << ") = " << out_val << std::endl;
  return 0;
}
