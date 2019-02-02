#include "CisInterface.h"
#include <stdio.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv(C): Hello!\n");
    cisRpc_t rpc = cisRpcServer("maxMsgSrv", "%s", "%s");
    size_t input_size = CIS_MSG_BUF;
    char *input = (char*)malloc(input_size);
    //char input[CIS_MSG_BUF];

    while (1) {
      // Reset to size of buffer if not all utilized
      if (input_size < CIS_MSG_BUF)
	input_size = CIS_MSG_BUF;
      
      int ret = rpcRecvRealloc(rpc, &input, &input_size);
      if (ret < 0)
        break;
      printf("maxMsgSrv(C): rpcRecv returned %d, input (size=%lu) %.10s...\n",
	     ret, input_size, input);
      ret = rpcSend(rpc, input, input_size);
      if (ret < 0) {
        printf("maxMsgSrv(C): SEND ERROR\n");
        break;
      }
    }

    printf("maxMsgSrv(C): Goodbye!\n");
    free(input);
    return 0;
}

