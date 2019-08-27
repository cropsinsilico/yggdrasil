#include <iostream>

int model_function(char *in, uint64_t length_in,
		   char** out, uint64_t* length_out) {

  length_out[0] = length_in;
  out[0] = (char*)realloc(out[0], length_in);
  memcpy(out[0], in, length_in);
  out[0][length_in] = '\0';
  std::cout << "Model A: " << *out << " (length = " << length_out[0] << ")" << std::endl;
  return 0;

}
