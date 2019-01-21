#include <stdio.h>
#include "YggInterface.h"

#define BSIZE 512 // the max

int main(int argc, char *argv[]) {
  int ret = 0;
  char buf[BSIZE];
  
  printf("Hello from C\n");

  // Ins/outs matching with the the model yaml
  yggInput_t inf = yggInput("inFile"); 
  yggOutput_t outf = yggOutput("outFile");
  yggInput_t inq = yggInput("helloQueueIn");
  yggOutput_t outq = yggOutput("helloQueueOut");
  printf("hello(C): Created I/O channels\n");

  // Receive input from a local file
  ret = ygg_recv(inf, buf, BSIZE);
  if (ret < 0) {
    printf("hello(C): ERROR FILE RECV\n");
    return -1;
  }
  int bufsiz = ret;
  printf("hello(C): Received %d bytes from file: %s\n", bufsiz, buf);

  // Send output to the output queue
  ret = ygg_send(outq, buf, bufsiz);
  if (ret != 0) {
    printf("hello(C): ERROR QUEUE SEND\n");
    return -1;
  }
  printf("hello(C): Sent to outq\n");

  // Receive input form the input queue
  ret = ygg_recv(inq, buf, BSIZE);
  if (ret < 0) {
    printf("hello(C): ERROR QUEUE RECV\n");
    return -1;
  }
  bufsiz = ret;
  printf("hello(C): Received %d bytes from queue: %s\n", bufsiz, buf);
  
  // Send output to a local file
  ret = ygg_send(outf, buf, bufsiz);
  if (ret != 0) {
    printf("hello(C): ERROR FILE SEND\n");
    return -1;
  }
  printf("hello(C): Sent to outf\n");

  printf("Goodbye from C\n");
  return 0;
}

