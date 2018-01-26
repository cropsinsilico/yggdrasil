#include "PsiInterface.h"
#include <stdio.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv(C): Hello!\n");
    psiRpc_t rpc = psiRpcServer("maxMsgSrv", "%s", "%s");
    char *input = (char*)malloc(10);
    //char input[PSI_MSG_BUF];

    while (1) {
      int ret = rpcRecv(rpc, input);
      if (ret < 0)
        break;
      printf("maxMsgSrv(C): rpcRecv returned %d, input %.10s...\n", ret, input);
      rpcSend(rpc, input);
    }

    printf("maxMsgSrv(C): Goodbye!\n");
    free(input);
    return 0;
}

