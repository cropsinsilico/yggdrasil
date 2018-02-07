#include <stdio.h>
#include "PsiInterface.h"

#define BSIZE 512 // the max

int main(int argc, char *argv[]) {
  int ret = 0;
  char buf[BSIZE];
  
  printf("Hello from C\n");

  // Ins/outs matching with the the model yaml
  psiInput_t inf = psiInput("inFile"); 
  psiOutput_t outf = psiOutput("outFile");
  psiInput_t inq = psiInput("helloQueueIn");
  psiOutput_t outq = psiOutput("helloQueueOut");
  printf("hello(C): Created I/O channels\n");

  // Receive input from a local file
  ret = psi_recv(inf, buf, BSIZE);
  if (ret < 0) {
    printf("hello(C): ERROR FILE RECV\n");
    return -1;
  }
  int bufsiz = ret;
  printf("hello(C): Received %d bytes from file: %s\n", bufsiz, buf);

  // Send output to the output queue
  ret = psi_send(outq, buf, bufsiz);
  if (ret != 0) {
    printf("hello(C): ERROR QUEUE SEND\n");
    return -1;
  }
  printf("hello(C): Sent to outq\n");
  psi_send_eof(outq);

  // Receive input form the input queue
  ret = psi_recv(inq, buf, BSIZE);
  if (ret < 0) {
    printf("hello(C): ERROR QUEUE RECV\n");
    return -1;
  }
  bufsiz = ret;
  printf("hello(C): Received %d bytes from queue: %s\n", bufsiz, buf);
  
  // Send output to a local file
  ret = psi_send(outf, buf, bufsiz);
  if (ret != 0) {
    printf("hello(C): ERROR FILE SEND\n");
    return -1;
  }
  printf("hello(C): Sent to outf\n");

  // Free input/output channels
  psi_free(&inf);
  psi_free(&outf);
  psi_free(&inq);
  psi_free(&outq);
  
  printf("Goodbye from C\n");
  return 0;
}

