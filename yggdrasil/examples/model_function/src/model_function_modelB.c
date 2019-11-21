#include <stdio.h>

int model_function(char *inputB, uint64_t length_inputB,
		   char** outputB, uint64_t* length_outputB) {

  length_outputB[0] = length_inputB;
  outputB[0] = (char*)malloc(length_inputB);
  memcpy(outputB[0], inputB, length_inputB);
  outputB[0][length_inputB] = '\0';
  printf("Model B: %s (length = %d)\n", *outputB, (int)(*length_outputB));
  return 0;

}
