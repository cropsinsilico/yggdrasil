#include <stdio.h>
// Include methods for input/output channels
#include "YggInterface.h"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  yggAsciiTableInput_t in_channel = yggAsciiTableInput("inputB");
  yggAsciiTableOutput_t out_channel = yggAsciiTableOutput("outputB", "%6s\t%d\t%f\n");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  size_t name_siz = MYBUFSIZ;
  char name[MYBUFSIZ];
  int count = 0;
  double size = 0.0;

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
    name_siz = MYBUFSIZ; // Reset to size of the buffer
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = yggRecv(in_channel, &name, &name_siz, &count, &size);
    if (flag < 0) {
      printf("Model B: No more input.\n");
      break;
    }

    // Print received message
    printf("Model B: %s, %d, %f\n", name, count, size);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = yggSend(out_channel, name, name_siz, count, size);
    if (flag < 0) {
      printf("Model B: Error sending output.\n");
      break;
    }

  }
  
  return 0;
}

