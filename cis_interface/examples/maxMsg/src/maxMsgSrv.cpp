#include "CisInterface.hpp"
#include <stdio.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv(CPP): Hello!\n");
    CisRpcServer rpc("maxMsgSrv", "%s", "%s");
    char *input = (char*)malloc(CIS_MSG_BUF);
    //char input[CIS_MSG_MAX];
    
    while (1) {
      int ret = rpc.recv(1, input);
      if (ret < 0)
	break;
      printf("maxMsgSrv(CPP): rpcRecv returned %d, input %.10s...\n", ret, input);
      ret = rpc.send(1, input);
      if (ret < 0) {
        printf("maxMsgSrv(CPP): SEND ERROR");
        break;
      }
    }

    printf("maxMsgSrv(CPP): Goodbye!\n");
    return 0;
}

