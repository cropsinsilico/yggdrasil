#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  YggInput in_channel("inputB");
  YggOutput out_channel("outputB");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  size_t msg_siz = 0;
  char *msg = NULL;
  size_t * const p_msg_siz = &msg_siz; // Required in C++ to get msg size

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = in_channel.recvRealloc(2, &msg, &msg_siz);
    if (flag < 0) {
      std::cout << "Model B: No more input." << std::endl;
      break;
    }

    // Print received message
    std::cout << "Model B: " << msg << std::endl;

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = out_channel.send(2, msg, msg_siz);
    if (flag < 0) {
      std::cout << "Model B: Error sending output." << std::endl;
      break;
    }

  }
  
  return 0;
}
