#include <stdio.h>
#include "CisInterface.h"

#define BSIZE 512 // the max

int main(int argc, char *argv[]) {
  int ret = 0;
  char buf[BSIZE];
  
  printf("Hello from C\n");

  // Ins/outs matching with the the model yaml
  cisInput_t inf = cisInput("inFile"); 
  cisOutput_t outf = cisOutput("outFile");
  cisInput_t inq = cisInput("helloQueueIn");
  cisOutput_t outq = cisOutput("helloQueueOut");
  printf("hello(C): Created I/O channels\n");

  // Receive input from a local file
  ret = cis_recv(inf, buf, BSIZE);
  if (ret < 0) {
    printf("hello(C): ERROR FILE RECV\n");
    return -1;
  }
  int bufsiz = ret;
  printf("hello(C): Received %d bytes from file: %s\n", bufsiz, buf);

  // Send output to the output queue
  ret = cis_send(outq, buf, bufsiz);
  if (ret != 0) {
    printf("hello(C): ERROR QUEUE SEND\n");
    return -1;
  }
  printf("hello(C): Sent to outq\n");

  // Receive input form the input queue
  ret = cis_recv(inq, buf, BSIZE);
  if (ret < 0) {
    printf("hello(C): ERROR QUEUE RECV\n");
    return -1;
  }
  bufsiz = ret;
  printf("hello(C): Received %d bytes from queue: %s\n", bufsiz, buf);
  
  // Send output to a local file
  ret = cis_send(outf, buf, bufsiz);
  if (ret != 0) {
    printf("hello(C): ERROR FILE SEND\n");
    return -1;
  }
  printf("hello(C): Sent to outf\n");

  printf("Goodbye from C\n");
  return 0;
}

