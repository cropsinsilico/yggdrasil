#include <iostream>
#include <math.h>

int modelD_function(float in_val1, float in_val2, float &in_val1_copy, float &in_val2_copy, float &out_val) {
  in_val1_copy = in_val1;
  in_val2_copy = in_val2;
  out_val = in_val1 + in_val2;
  std::cout << "modelD_function(" << in_val1 << ", " << in_val2 << ") = " << out_val << std::endl;
  return 0;
}
