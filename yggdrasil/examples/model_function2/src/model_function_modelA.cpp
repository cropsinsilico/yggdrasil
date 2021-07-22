#include <iostream>

int model_function(float x, float& y) {
  y = x + 1.0;
  std::cout << "Model A: " << x << "->" << y << std::endl;
  return 0;
}
