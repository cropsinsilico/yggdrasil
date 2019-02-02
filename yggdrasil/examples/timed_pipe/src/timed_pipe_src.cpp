#include <stdio.h>
#include "YggInterface.hpp"

int main(int argc, char *argv[]) {
  if (argc != 3) {
    printf("Error in C++ pipe_src: The message count and size must be provided as input arguments.\n");
    return -1;
  }
  int exit_code = 0;
  int ret = 0;

  int msg_count = atoi(argv[1]);
  int msg_size = atoi(argv[2]);
  printf("Hello from C++ pipe_src: msg_count = %d, msg_size = %d\n",
	 msg_count, msg_size);

  // Ins/outs matching with the the model yaml
  YggOutput outq("output_pipe");
  printf("pipe_src(CPP): Created I/O channels\n");

  // Create test message
  char *test_msg = (char*)malloc(msg_size + 1);
  int i;
  for (i = 0; i < msg_size; i++)
    test_msg[i] = '0';
  test_msg[i] = '\0';

  // Send test message multiple times
  int count = 0;
  for (i = 0; i < msg_count; i++) {
    ret = outq.send(test_msg, msg_size);
    if (ret < 0) {
      printf("pipe_src(CPP): SEND ERROR ON MSG %d\n", i);
      exit_code = -1;
      break;
    }
    count++;
  }

  printf("Goodbye from C++ source. Sent %d messages.\n", count);
  free(test_msg);
  return exit_code;
}

