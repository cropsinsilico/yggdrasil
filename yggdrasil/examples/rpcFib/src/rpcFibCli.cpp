
#include "YggInterface.hpp"
#include <stdio.h>


int count_lines(const char* str, const char* substr) {
  int c = 0;
  int inc = strlen(substr);
  if (strlen(substr) == 0) return -1;
  for (char* s = (char*)str; (s = strstr(s, substr)); s += inc)
    c++;
  return c;
}


int main(int argc, char *argv[]) {
   
  int iterations = atoi(argv[1]);
  printf("Hello from C++ rpcFibCli: iterations %d\n", iterations);
  
  // Set up connections matching yaml
  // RPC client-side connection will be $(server_name)_$(client_name)
  YggInput ymlfile("yaml_in");
  YggRpcClient rpc("rpcFibSrv_rpcFibCli", "%d", "%d %d");
  YggOutput log("output_log");
  
  // Read entire contents of yaml
  char *ycontent = (char*)malloc(YGG_MSG_MAX*sizeof(char));
  int ret = ymlfile.recv(ycontent, YGG_MSG_MAX);
  if (ret < 0) {
    printf("rpcFibCli(CPP): RECV ERROR\n");
    free(ycontent);
    exit(-1);
  }
  printf("rpcFibCli: yaml has %d lines\n", count_lines(ycontent, "\n") + 1);
  free(ycontent);
  
  int fib = -1;
  int fibNo = -1;
  char *logmsg = (char*)malloc(YGG_MSG_MAX*sizeof(char));
  for (int i = 1; i <= iterations; i++) {
    
    // Call the server and receive response
    printf("rpcFibCli(CPP): fib(->%-2d) ::: ", i);
    ret = rpc.call(3, i, &fibNo, &fib);
    if (ret < 0) {
      printf("rpcFibCli(CPP): RPC CALL ERROR\n");
      free(logmsg);
      return -1;
    }

    // Log result by sending it to the log connection
    sprintf(logmsg, "fib(%2d<-) = %-2d<-\n", fibNo, fib);
    printf(logmsg);
    ret = log.send(logmsg, strlen(logmsg));
    if (ret < 0) {
      printf("rpcFibCli(CPP): SEND ERROR\n");
      free(logmsg);
      return -1;
    }
  }

  printf("Goodbye from C++ rpcFibCli\n");
  free(logmsg);
  return 0;
}

