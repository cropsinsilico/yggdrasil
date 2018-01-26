#include <iostream>
// Include methods for input/output channels
#include "PsiInterface.hpp"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  PsiInput in_channel("inputA");
  PsiOutput out_channel("outputA");

  // Declare resulting variables and create buffer for received message
  int flag;
  char buf[MYBUFSIZ];

  // Receive input from input channel
  // If there is an error, the flag will be negative
  // Otherwise, it is the size of the received message
  flag = in_channel.recv(buf, MYBUFSIZ);

  // Print received message
  std::cout << buf << std::endl;

  // Send output to output channel
  // If there is an error, the flag will be negative
  flag = out_channel.send(buf, flag);
  
  return 0;
}
