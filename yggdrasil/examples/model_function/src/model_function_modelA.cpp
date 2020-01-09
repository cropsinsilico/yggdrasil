#include <iostream>

int model_function(char *in, uint64_t length_in,
		   char* &out, uint64_t &length_out) {

  length_out = length_in;
  out = (char*)realloc(out, length_in);
  memcpy(out, in, length_in);
  out[length_in] = '\0';
  std::cout << "Model A: " << out << " (length = " << length_out << ")" << std::endl;
  return 0;

}
