#include "YggInterface.h"
#include <stdio.h>


void rand_str(char *dest, size_t length) {
  char charset[] = "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  while (length-- > 1) {
    size_t index = (size_t)((double) rand() / RAND_MAX * (sizeof charset - 1));
    *dest++ = charset[index];
  }
  *dest = '\0';
}


int main(int argc, char *argv[]) {

  //char output[YGG_MSG_BUF];
  //char input[YGG_MSG_BUF];
  size_t msg_size_output = YGG_MSG_BUF;
  size_t msg_size_input = YGG_MSG_BUF;
  char *output = (char*)malloc(msg_size_output);
  char *input = (char*)malloc(msg_size_input);

  printf("maxMsgCli(C): Hello message size is %d.\n", (int)msg_size_output);
  
  // Create a max message, send/recv and verify
  yggRpc_t rpc = yggRpcClient("maxMsgSrv_maxMsgCli", "%s", "%s");
    
  // Create a max message
  rand_str(output, msg_size_output);
  printf("maxMsgCli(C): sending %.10s...\n", output);
    
  // Call RPC server
  if (rpcCallRealloc(rpc, output, msg_size_output-1,
		     &input, &msg_size_input) < 0) {
    printf("maxMsgCli(C): RPC ERROR\n");
    free(output);
    free(input);
    return -1;
  }
  printf("maxMsgCli(C): received %lu bytes: %.10s...\n", msg_size_input, input);

  // Check to see if response matches
  if (strncmp(output, input, msg_size_output-1)) {
    printf("maxMsgCli(C): ERROR: input/output do not match\n");
    free(output);
    free(input);
    return -1;
  } else {
    printf("maxMsgCli(C): CONFIRM\n");
  }

  // All done, free and say goodbye
  printf("maxMsgCli(C): Goodbye!\n");
  free(output);
  free(input);
  return 0;
}

