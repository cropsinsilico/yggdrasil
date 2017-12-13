#include <stdio.h>
// Include methods for input/output channels
#include "PsiInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  psiInput_t in_channel = psiInput("input");
  psiOutput_t out_channel = psiOutput("output");

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

  // Free input/output channels
  psi_free(&in_channel);
  psi_free(&out_channel);
  
  return 0;
}

