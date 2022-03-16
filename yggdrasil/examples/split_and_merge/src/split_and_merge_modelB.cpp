#include <iostream>
#include <math.h>

float modelB_function(float in_val) {
  float out_val = 3 * in_val;
  std::cout << "modelB_function(" << in_val << ") = " << out_val << std::endl;
  return out_val;
}
