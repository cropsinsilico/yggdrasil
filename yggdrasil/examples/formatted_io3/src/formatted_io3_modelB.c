#include <stdio.h>
// Include methods for input/output channels
#include "YggInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  yggAsciiArrayInput_t in_channel = yggAsciiArrayInput("inputB");
  yggAsciiArrayOutput_t out_channel = yggAsciiArrayOutput("outputB", "%6s\t%d\t%f\n");

  // Declare resulting variables and create buffer for received message
  size_t nrows;
  int flag = 1;
  char *name = NULL;
  int *count = NULL;
  double *size = NULL;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = yggRecvRealloc(in_channel, &nrows, &name, &count, &size);
    if (flag < 0) {
      printf("Model B: No more input.\n");
      break;
    }

    // Print received message
    printf("Model B: (%lu rows)\n", nrows);
    size_t i;
    for (i = 0; i < nrows; i++)
      printf("   %.6s, %d, %f\n", &name[6*i], count[i], size[i]);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = yggSend(out_channel, nrows, name, count, size);
    if (flag < 0) {
      printf("Model B: Error sending output.\n");
      break;
    }

  }
  
  // Free dynamically allocated columns
  if (name) free(name);
  if (count) free(count);
  if (size) free(size);
  
  return 0;
}

