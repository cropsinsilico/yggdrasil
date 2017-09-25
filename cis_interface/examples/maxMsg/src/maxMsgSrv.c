#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv(C): Hello!\n");
    psiRpc_t rpc = psiRpcServer("maxMsgSrv", "%s", "%s");
    char input[PSI_MSG_MAX];

    int ret = rpcRecv(rpc, &input);
    printf("maxMsgSrv(C): rpcRecv returned %d, input %s\n", ret, input);
    rpcSend(rpc, input);

    printf("maxMsgSrv(C): Goodbye!\n");
    
}

