#include <map>
#include <vector>

int model_function(bool a, double b,
		   std::map<std::string, double> c,
		   bool& d, double& e,
		   std::vector<double>& f) {
  d = (!a);
  e = c["c1"];
  for (int i = 0; i < 3; i++) {
    if (a)
      f.push_back(b * pow(i, c["c1"]));
    else
      f.push_back(b * pow(i, c["c2"]));
  }
  return 1;
}
