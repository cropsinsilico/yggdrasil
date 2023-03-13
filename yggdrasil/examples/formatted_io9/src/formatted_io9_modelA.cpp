#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  YggAnyInput in_channel("inputA");
  YggAnyOutput out_channel("outputA");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  rapidjson::Document obj;

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
    std::cerr << "Model A:" << std::endl <<
      document2string(obj) << std::endl;

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = out_channel.send(1, &obj);
    if (flag < 0) {
      std::cout << "Model A: Error sending output." << std::endl;
      break;
    }

  }

  return 0;
}

