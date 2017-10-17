#include <iostream>
// Include methods for input/output channels
#include "PsiInterface.hpp"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  PsiInput in_channel("input");
  PsiOutput out_channel("output");

  // Declare resulting variables and create buffer for received message
  int flag;
  const int bufsiz = 1000;
  char buf[bufsiz];

  // Receive input from input channel
  // If there is an error, the flag will be negative
  // Otherwise, it is the size of the received message
  flag = in_channel.recv(buf, bufsiz);

  // Print received message
  std::cout << buf << std::endl;

  // Send output to output channel
  // If there is an error, the flag will be negative
  flag = out_channel.send(buf, flag);
  
  return 0;
}
