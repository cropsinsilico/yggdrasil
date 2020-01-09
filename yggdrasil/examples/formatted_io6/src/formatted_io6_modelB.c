#include <stdio.h>
// Include methods for input/output channels
#include "YggInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  yggObjInput_t in_channel = yggObjInput("inputB");
  yggObjOutput_t out_channel = yggObjOutput("outputB");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  obj_t p = init_obj();

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = yggRecv(in_channel, &p);
    if (flag < 0) {
      printf("Model B: No more input.\n");
      break;
    }

    // Print received message
    printf("Model B: (%d verts, %d faces)\n", p.nvert, p.nface);
    display_obj_indent(p, "  ");

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = yggSend(out_channel, p);
    if (flag < 0) {
      printf("Model B: Error sending output.\n");
      break;
    }

  }
  
  // Free dynamically allocated obj structure
  free_obj(&p);
  
  return 0;
}

