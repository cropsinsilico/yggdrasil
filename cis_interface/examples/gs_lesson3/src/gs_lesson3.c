#include <stdio.h>
// Include methods for input/output channels
#include "PsiInterface.h"

#define BUFSIZ 1000

int main(int argc, char *argv[]) {
  // Initialize input/output channels
  setbuf(stdout, NULL);
  printf("in gs_lesson4\n");
  psiInput_t in_channel = psiInput("input");
  psiOutput_t out_channel = psiOutput("output");

  /* // Declare resulting variables and create buffer for received message */
  /* int flag = 1; */
  /* char buf[BUFSIZ]; */

  /* // Loop until there is no longer input or the queues are closed */
  /* while (flag >= 0) { */
  
  /*   // Receive input from input channel */
  /*   // If there is an error or the queue is closed, the flag will be negative */
  /*   // Otherwise, it is the size of the received message */
  /*   flag = psi_recv(in_channel, buf, BUFSIZ); */
  /*   if (flag < 0) { */
  /*     printf("No more input.\n"); */
  /*     break; */
  /*   } */

  /*   // Print received message */
  /*   printf("%s\n", buf); */

  /*   // Send output to output channel */
  /*   // If there is an error, the flag will be negative */
  /*   flag = psi_send(out_channel, buf, flag); */
  /*   if (flag < 0) { */
  /*     printf("Error sending output.\n"); */
  /*     break; */
  /*   } */

  /* } */

  // Free input/output channels
  psi_free(&in_channel);
  psi_free(&out_channel);
  
  return 0;
}

