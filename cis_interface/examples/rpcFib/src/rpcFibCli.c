
#include "CisInterface.h"
#include <stdio.h>


int count_lines(const char* str, const char* substr) {
  int c = 0;
  int inc = strlen(substr);
  if (strlen(substr) == 0) return -1;
  char *s;
  for (s = (char*)str; (s = strstr(s, substr)); s += inc)
    c++;
  return c;
}


int main(int argc, char *argv[]) {
   
  int iterations = atoi(argv[1]);
  printf("Hello from C rpcFibCli: iterations %d\n", iterations);
  
  // Set up connections matching yaml
  // RPC client-side connection will be $(server_name)_$(client_name)
  cisInput_t ymlfile = cisInput("yaml_in");
  cisRpc_t rpc = cisRpcClient("rpcFibSrv_rpcFibCli", "%d", "%d %d");
  cisOutput_t log = cisOutput("output_log");
  int ret;

  // Read entire contents of yaml
  char *ycontent = (char*)malloc(CIS_MSG_MAX*sizeof(char));
  ret = cis_recv(ymlfile, ycontent, CIS_MSG_MAX);
  if (ret < 0) {
    printf("rpcFibCli(C): RECV ERROR\n");
    free(ycontent);
    exit(-1);
  }
  printf("rpcFibCli: yaml has %d lines\n", count_lines(ycontent, "\n") + 1);
  ret = cis_recv(ymlfile, ycontent, CIS_MSG_MAX);
  free(ycontent);
  
  int fib = -1;
  int fibNo = -1;
  char *logmsg = (char*)malloc(CIS_MSG_MAX*sizeof(char));
  int i;
  for (i = 1; i <= iterations; i++) {
    
    // Call the server and receive response
    printf("rpcFibCli(C): fib(->%-2d) ::: ", i);
    ret = rpcCall(rpc, i, &fibNo, &fib);
    if (ret < 0) {
      printf("rpcFibCli(C): RPC CALL ERROR\n");
      free(logmsg);
      exit(-1);
    }

    // Log result by sending it to the log connection
    sprintf(logmsg, "fib(%2d<-) = %-2d<-\n", fibNo, fib);
    printf("%s", logmsg);
    ret = cis_send(log, logmsg, strlen(logmsg));
    if (ret < 0) {
      printf("rpcFibCli(C): SEND ERROR\n");
      free(logmsg);
      exit(-1);
    }
  }

  free(logmsg);
  printf("Goodbye from C rpcFibCli\n");
  exit(0);
    
}

