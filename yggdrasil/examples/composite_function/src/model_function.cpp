#include <map>
#include <vector>

int model_function(bool a, double b,
		   std::map<std::string, double> c,
		   std::vector<double>& out) {
  for (int i = 0; i < 3; i++) {
    if (a)
      out.push_back(b * pow(i, c["c1"]));
    else
      out.push_back(b * pow(i, c["c2"]));
  }
  return 1;
}
