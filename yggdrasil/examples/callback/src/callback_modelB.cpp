#include <iostream>
#include <math.h>

int modelB_function(float in_val, float &in_val_copy, float &out_val) {
  in_val_copy = in_val;
  out_val = 3 * in_val;
  std::cout << "modelB_function(" << in_val << ") = " << out_val << std::endl;
  return 0;
}
