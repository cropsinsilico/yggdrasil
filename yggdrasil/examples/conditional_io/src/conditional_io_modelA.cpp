#include <iostream>

int modelA_function(float in_val, float &out_val) {
  out_val = in_val;
  std::cout << "modelA_function(" << in_val << ") = " << out_val << std::endl;
  return 0;
}
