#include <iostream>
#include <vector>

int model_function(std::vector<float> x,
		   std::vector<float> &y) {
  std::vector<float>::iterator it;
  for (it = x.begin(); it != x.end(); it++)
    y.push_back(*it + 2.0);
  std::cout << "Model B: [";
  for (it = x.begin(); it != x.end(); it++)
    std::cout << *it << " ";
  std::cout << "] -> [";
  for (it = y.begin(); it != y.end(); it++)
    std::cout << *it << " ";
  std::cout << "]" << std::endl;
  return 0;

}
