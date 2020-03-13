#include <iostream>
#include <math.h>

int modelC_function(float in_val, float &in_val_copy, float &out_val) {
  in_val_copy = in_val;
  out_val = 2 * in_val;
  std::cout << "modelC_function(" << in_val << ") = " << out_val << std::endl;
  return 0;
}
