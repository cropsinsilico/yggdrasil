#include <stdio.h>
#include "YggInterface.hpp"

int main() {
  int ret = 0;
  int bufsiz = 512;
  char *buf = (char*)malloc(bufsiz);
  
  printf("Hello from C++ pipe_dst\n");

  // Ins/outs matching with the the model yaml
  YggInput inq("input_pipe");
  YggOutput outf("output_file");
  printf("pipe_dst(CPP): Created I/O channels\n");

  // Continue receiving input from the queue
  int count = 0;
  while (1) {
    ret = inq.recv_nolimit(&buf, bufsiz);
    if (ret < 0) {
      printf("pipe_dst(CPP): Input channel closed\n");
      break;
    }
    if (ret > (bufsiz - 1)) {
      bufsiz = ret + 1;
      printf("pipe_dst(CPP): Buffer increased to %d bytes\n", bufsiz);
    }
    ret = outf.send_nolimit(buf, ret);
    if (ret < 0) {
      printf("pipe_dst(CPP): SEND ERROR ON MSG %d\n", count);
      free(buf);
      return -1;
    }
    count++;
  }

  printf("Goodbye from C++ destination. Received %d messages.\n", count);

  free(buf);
  return 0;
}

