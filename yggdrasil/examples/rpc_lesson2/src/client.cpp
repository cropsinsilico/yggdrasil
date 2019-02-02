#include "YggInterface.hpp"
#include <stdio.h>


int main(int argc, char *argv[]) {
   
  int iterations = atoi(argv[1]);
  int client_index = atoi(argv[2]);
  int exit_code = 0;
  printf("Hello from C++ client%d: iterations %d\n",
	 client_index, iterations);
  
  // Set up connections matching yaml
  // RPC client-side connection will be $(server_name)_$(client_name)
  char rpc_name[100];
  char log_name[100];
  sprintf(rpc_name, "server_client%d", client_index);
  sprintf(log_name, "output_log%d", client_index);
  YggRpcClient rpc(rpc_name, "%d", "%d");
  YggOutput log(log_name, "fib(%-2d) = %-2d\n");
  
  // Initialize variables
  int ret = 0;
  int fib = -1;
  char *logmsg = (char*)malloc(YGG_MSG_MAX*sizeof(char));
  int i;

  // Iterate over Fibonacci sequence
  for (i = 1; i <= iterations; i++) {
    
    // Call the server and receive response
    printf("client%d(C++): Calling fib(%d)\n", client_index, i);
    ret = rpc.call(2, i, &fib);
    if (ret < 0) {
      printf("client%d(C++): RPC CALL ERROR\n", client_index);
      exit_code = -1;
      break;
    }
    printf("client%d(C++): Response fib(%d) = %d\n", client_index, i, fib);

    // Log result by sending it to the log connection
    ret = log.send(2, i, fib);
    if (ret < 0) {
      printf("client%d(C++): SEND ERROR\n", client_index);
      exit_code = -1;
      break;
    }
  }

  free(logmsg);
  printf("Goodbye from C++ client%d\n", client_index);
  return exit_code;
}

