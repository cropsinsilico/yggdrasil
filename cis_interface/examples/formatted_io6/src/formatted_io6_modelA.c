#include <stdio.h>
// Include methods for input/output channels
#include "CisInterface.h"

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  cisObjInput_t in_channel = cisObjInput("inputA");
  cisObjOutput_t out_channel = cisObjOutput("outputA");

  // Declare resulting variables and create buffer for received message
  int flag = 1;
  obj_t p = init_obj();

  // Loop until there is no longer input or the queues are closed
  while (flag >= 0) {
  
    // Receive input from input channel
    // If there is an error, the flag will be negative
    // Otherwise, it is the size of the received message
    flag = cisRecv(in_channel, &p);
    if (flag < 0) {
      printf("Model A: No more input.\n");
      break;
    }

    // Print received message
    printf("Model A: (%d verts, %d faces)\n", p.nvert, p.nface);
    int i;
    printf("  Vertices:\n");
    for (i = 0; i < p.nvert; i++) {
      printf("   %f, %f, %f\n",
	     p.vertices[i][0], p.vertices[i][1], p.vertices[i][2]);
    }
    printf("  Faces:\n");
    for (i = 0; i < p.nface; i++) {
      printf("   %d, %d, %d\n",
	     p.faces[i][0], p.faces[i][1], p.faces[i][2]);
    }

    // Send output to output channel
    // If there is an error, the flag will be negative
    flag = cisSend(out_channel, p);
    if (flag < 0) {
      printf("Model A: Error sending output.\n");
      break;
    }

  }

  // Free dynamically allocated obj structure
  free_obj(&p);
  
  return 0;
}

