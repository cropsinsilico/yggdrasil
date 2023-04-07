#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  YggObjInput in_channel("inputB");
  YggObjOutput out_channel("outputB");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  rapidjson::ObjWavefront p;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = in_channel.recv(1, &p);
    if (flag < 0) {
      std::cout << "Model B: No more input." << std::endl;
      break;
    }

    // Print received message
    printf("Model B: (%ld verts, %ld faces)\n",
	   p.count_elements("v"), p.count_elements("f"));
    std::cerr << p << std::endl;

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = out_channel.send(1, &p);
    if (flag < 0) {
      std::cout << "Model B: Error sending output." << std::endl;
      break;
    }

  }
  
  return 0;
}
