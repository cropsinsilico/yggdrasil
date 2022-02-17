#include <iostream>

int modelA_function(float in_val, float &out_val1, float &out_val2) {
  out_val1 = 2 * in_val;
  out_val2 = 3 * in_val;
  std::cout << "modelA_function(" << in_val << ") = (" << out_val1 << ", " << out_val2 << ")" << std::endl;
  return 0;
}
