#include <stdio.h>

int model_function(char *in, uint64_t length_in,
		   char** out, uint64_t* length_out) {

  length_out[0] = length_in;
  out[0] = (char*)malloc(length_in);
  memcpy(out[0], in, length_in);
  out[0][length_in] = '\0';
  printf("Model A: %s (length = %d)\n", *out, (int)(*length_out));
  return 0;

}
