#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  YggAnyInput in_channel("inputA");
  YggAnyOutput out_channel("outputA");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  generic_t obj = init_generic();

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = in_channel.recv(1, &obj);
    if (flag < 0) {
      std::cout << "Model A: No more input." << std::endl;
      break;
    }

    // Print received message
    printf("Model A:\n");
    display_generic(obj);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = out_channel.send(1, obj);
    if (flag < 0) {
      std::cout << "Model A: Error sending output." << std::endl;
      break;
    }

  }

  // Free dynamically allocated obj structure
  free_generic(&obj);
  
  return 0;
}

