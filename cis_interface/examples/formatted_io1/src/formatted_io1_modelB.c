#include <stdio.h>
// Include methods for input/output channels
#include "CisInterface.h"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  cisInput_t in_channel = cisInput("inputB");
  cisOutput_t out_channel = cisOutput("outputB");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  size_t msg_siz = 0;
  char *msg = NULL;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = cisRecvRealloc(in_channel, &msg, &msg_siz);
    if (flag < 0) {
      printf("Model B: No more input.\n");
      break;
    }

    // Print received message
    printf("Model B: %s\n", msg);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = cisSend(out_channel, msg, msg_siz);
    if (flag < 0) {
      printf("Model B: Error sending output.\n");
      break;
    }

  }
  
  return 0;
}

