#include <stdio.h>
// Include methods for input/output channels
#include "YggInterface.h"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  yggInput_t in_channel = yggInput("inputB");
  yggOutput_t out_channel = yggOutput("outputB");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  char buf[MYBUFSIZ];

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = ygg_recv(in_channel, buf, MYBUFSIZ);
    if (flag < 0) {
      printf("Model B: No more input.\n");
      break;
    }

    // Print received message
    printf("Model B: %s\n", buf);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = ygg_send(out_channel, buf, flag);
    if (flag < 0) {
      printf("Model B: Error sending output.\n");
      break;
    }

  }
  
  return 0;
}

