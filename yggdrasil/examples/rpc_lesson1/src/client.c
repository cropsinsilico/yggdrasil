#include "YggInterface.h"
#include <stdio.h>


int main(int argc, char *argv[]) {
   
  int iterations = atoi(argv[1]);
  int exit_code = 0;
  printf("Hello from C client: iterations %d\n", iterations);
  
  // Set up connections matching yaml
  // RPC client-side connection will be $(server_name)_$(client_name)
  yggRpc_t rpc = yggRpcClient("server_client", "%d", "%d");
  yggOutput_t log = yggOutputFmt("output_log", "fib(%-2d) = %-2d\n");

  // Initialize variables
  int ret = 0;
  int fib = -1;
  char *logmsg = (char*)malloc(YGG_MSG_MAX*sizeof(char));
  int i;

  // Iterate over Fibonacci sequence
  for (i = 1; i <= iterations; i++) {
    
    // Call the server and receive response
    printf("client(C): Calling fib(%d)\n", i);
    ret = rpcCall(rpc, i, &fib);
    if (ret < 0) {
      printf("client(C): RPC CALL ERROR\n");
      exit_code = -1;
      break;
    }
    printf("client(C): Response fib(%d) = %d\n", i, fib);

    // Log result by sending it to the log connection
    ret = yggSend(log, i, fib);
    if (ret < 0) {
      printf("client(C): SEND ERROR\n");
      exit_code = -1;
      break;
    }
  }

  free(logmsg);
  printf("Goodbye from C client\n");
  return exit_code;
    
}

