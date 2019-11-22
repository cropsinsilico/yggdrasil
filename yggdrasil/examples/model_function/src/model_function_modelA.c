#include <stdio.h>

int model_function(char *inputA, uint64_t length_inputA,
		   char** outputA, uint64_t* length_outputA) {

  length_outputA[0] = length_inputA;
  outputA[0] = (char*)malloc(length_inputA);
  memcpy(outputA[0], inputA, length_inputA);
  outputA[0][length_inputA] = '\0';
  printf("Model A: %s (length = %d)\n", *outputA, (int)(*length_outputA));
  return 0;

}
