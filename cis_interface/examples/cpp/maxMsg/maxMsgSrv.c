
#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv: hello\n");
    psiRpc_t rpc = psiRpcServer("srv_input", "%s", "srv_output", "%s");
    char input[PSI_MSG_MAX];

    int ret = rpcRecv(rpc, &input);
    printf("rpcFibSrv:  rpcRecv returned %d, input %s\n", ret, input);
    rpcSend(rpc, input);

    printf("maxMsgSrv: goobye\n");
    
}

