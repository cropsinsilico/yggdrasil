#include <stdio.h>
#include "CisInterface.h"

int main() {
  int exit_code = 0;
  int ret = 0;
  int bufsiz = 512;
  char *buf = (char*)malloc(bufsiz);
  
  printf("Hello from C pipe_dst\n");

  // Ins/outs matching with the the model yaml
  cisInput_t inq = cisInput("input_pipe");
  cisOutput_t outf = cisOutput("output_file");
  printf("pipe_dst(C): Created I/O channels\n");

  // Continue receiving input from the queue
  int count = 0;
  while (1) {
    ret = cis_recv_nolimit(inq, &buf, bufsiz);
    if (ret < 0) {
      printf("pipe_dst(C): Input channel closed\n");
      break;
    }
    if (ret > (bufsiz - 1)) {
      bufsiz = ret + 1;
      printf("pipe_dst(C): Buffer increased to %d bytes\n", bufsiz);
    }
    ret = cis_send_nolimit(outf, buf, ret);
    if (ret < 0) {
      printf("pipe_dst(C): SEND ERROR ON MSG %d\n", count);
      exit_code = -1;
      break;
    }
    count++;
  }

  printf("Goodbye from C destination. Received %d messages.\n", count);

  free(buf);
  return exit_code;
}

