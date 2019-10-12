#include <stdio.h>
// Include methods for input/output channels
#include "YggInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  yggInput_t in_channel = yggInput("inputA");
  yggOutput_t out_channel = yggOutput("outputA");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  vector_t vec = init_vector();

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = yggRecv(in_channel, &vec);
    if (flag < 0) {
      printf("Model A: No more input.\n");
      break;
    }

    // Print received message
    printf("Model A:\n");
    display_vector(vec);

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = yggSend(out_channel, vec);
    if (flag < 0) {
      printf("Model A: Error sending output.\n");
      break;
    }

  }

  // Free dynamically allocated vector structure
  free_vector(&vec);
  
  return 0;
}

