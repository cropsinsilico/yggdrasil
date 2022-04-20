#include <iostream>
#include <math.h>

float modelC_function(float in_val) {
  float out_val = 4 * in_val;
  std::cout << "modelC_function(" << in_val << ") = " << out_val << std::endl;
  return out_val;
}
