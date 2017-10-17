#include <stdio.h>
// Include methods for input/output channels
#include "PsiInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  psiInput_t in_channel = psiInput("inputB");
  psiOutput_t out_channel = psiOutput("outputB");

  // Declare resulting variables and create buffer for received message
  int flag;
  const int bufsiz = 1000;
  char buf[bufsiz];

  // Receive input from input channel
  // If there is an error, the flag will be negative
  // Otherwise, it is the size of the received message
  flag = psi_recv(in_channel, buf, bufsiz);

  // Print received message
  printf("%s\n", buf);

  // Send output to output channel
  // If there is an error, the flag will be negative
  flag = psi_send(out_channel, buf, flag);
  
  return 0;
}

