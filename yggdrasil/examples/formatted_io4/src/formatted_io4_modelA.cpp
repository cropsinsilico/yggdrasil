#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  YggAsciiArrayInput in_channel("inputA");
  YggAsciiArrayOutput out_channel("outputA", "%6s\t%ld\t%f\n");

  // Declare resulting variables and create buffer for received message
  size_t nrows;
  int flag = 1;
  char *name = NULL;
  long *count = NULL;
  double *size = NULL;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = in_channel.recvRealloc(4, &nrows, &name, &count, &size);
    if (flag < 0) {
      std::cout << "Model A: No more input." << std::endl;
      break;
    }

    // Print received message
    printf("Model A: (%lu rows)\n", nrows);
    size_t i;
    for (i = 0; i < nrows; i++)
      printf("   %.6s, %ld, %f\n", &name[6*i], count[i], size[i]);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = out_channel.send(4, nrows, name, count, size);
    if (flag < 0) {
      std::cout << "Model A: Error sending output." << std::endl;
      break;
    }

  }
  
  // Free dynamically allocated columns
  if (name) free(name);
  if (count) free(count);
  if (size) free(size);
  
  return 0;
}
