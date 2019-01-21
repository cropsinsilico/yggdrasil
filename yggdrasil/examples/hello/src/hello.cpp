#include "YggInterface.hpp"
#include <string>
#include <iostream>
using namespace std;

#define BSIZE 512 // the max

int main(int argc, char *argv[]) {
  int ret = 1;
  char buf[BSIZE];

  cout << "Hello from C++\n";
  
  /* Matching with the the model yaml */
  YggInput inf("inFile"); 
  YggOutput outf("outFile");
  YggInput inq("helloQueueIn");
  YggOutput outq("helloQueueOut");
  cout << "hello(CPP): Created I/O channels\n";

  // Receive input from the local file
  ret = inf.recv(buf, BSIZE);
  if (ret < 0) {
    printf("hello(CPP): ERROR FILE RECV\n");
    return -1;
  }
  int bufsiz = ret;
  printf("hello(CPP): Received %d bytes from file: %s\n", bufsiz, buf);

  // Send output to queue
  ret = outq.send(buf, bufsiz);
  if (ret != 0) {
    printf("hello(CPP): ERROR QUEUE SEND\n");
    return -1;
  }
  printf("hello(CPP): Sent to outq\n");

  // Receive input from queue
  ret = inq.recv(buf, BSIZE);
  if (ret < 0) {
    printf("hello(CPP): ERROR QUEUE RECV\n");
    return -1;
  }
  bufsiz = ret;
  printf("hello(CPP): Received %d bytes from queue: %s\n", bufsiz, buf);

  // Send output to local file
  ret = outf.send(buf, bufsiz);
  if (ret != 0) {
    printf("hello(CPP): ERROR FILE SEND\n");
    return -1;
  }
  printf("hello(CPP): Sent to outf\n");

  cout << "Goodbye from C++\n";
  return 0;
}
