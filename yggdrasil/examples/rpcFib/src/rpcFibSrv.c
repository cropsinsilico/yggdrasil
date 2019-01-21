
#include "YggInterface.h"
#include <stdio.h>


int main(int argc, char *argv[]) {

  float timeSleep = atof(argv[1]);
  printf("Hello from C rpcFibSrv: sleeptime = %f\n", timeSleep);
  
  // Create server-side rpc conneciton using model name
  yggRpc_t rpc = yggRpcServer("rpcFibSrv", "%d", "%d %d");

  // Continue receiving requests until error occurs (the connection is closed
  // by all clients that have connected).
  int input;
  while (1) {
    printf("rpcFibSrv(C): receiving...\n");
    int ret = rpcRecv(rpc, &input);
    if (ret < 0) {
      printf("rpcFibSrv(C): end of input\n");
      break;
    }

    // Compute fibonacci number
    printf("rpcFibSrv(C): <- input %d", input);
    int result = 1;
    int prevResult = 1;
    int prevPrev = 0;
    int idx = 1;
    while(idx++ < input){
      result = prevResult + prevPrev;
      prevPrev = prevResult;
      prevResult = result;
    }
    printf(" ::: ->(%2d %2d)\n", input, result);

    // Sleep and then send response back
    if (timeSleep) 
      sleep(timeSleep);
    int flag = rpcSend(rpc, input, result);
    if (flag < 0) {
      printf("rpcFibSrv(C): ERROR sending\n");
      break;
    }
  }

  printf("Goodbye from C rpcFibSrv\n");
  return 0;
}

