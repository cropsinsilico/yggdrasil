
#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


int main(int argc, char *argv[]) {

  float timeSleep = atof(argv[1]);
  printf("Hello from C rpcFibSrv: sleeptime = %f\n", timeSleep);
  
  // Create server-side rpc conneciton using model name
  psiRpc_t rpc = psiRpcServer("rpcFibSrv", "%d", "%d %d");

  // Continue receiving requests until error occurs (the connection is closed
  // by all clients that have connected).
  int input;
  while (1) {
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
    rpcSend(rpc, input, result);
  }

  printf("Goodbye from C rpcFibSrv\n");
  
}

