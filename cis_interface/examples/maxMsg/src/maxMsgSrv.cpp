#include "PsiInterface.hpp"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv(CPP): Hello!\n");
    PsiRpcServer rpc("maxMsgSrv", "%s", "%s");
    char input[PSI_MSG_MAX];

    int ret = rpc.recv(1, &input);
    printf("maxMsgSrv(CPP): rpcRecv returned %d, input %s\n", ret, input);
    rpc.send(1, input);

    printf("maxMsgSrv(CPP): Goodbye!\n");
    
}

