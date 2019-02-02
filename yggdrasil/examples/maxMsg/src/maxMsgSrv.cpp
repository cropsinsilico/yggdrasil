#include "YggInterface.hpp"
#include <stdio.h>


int main(int argc, char *argv[]) {  

    printf("maxMsgSrv(CPP): Hello!\n");
    YggRpcServer rpc("maxMsgSrv", "%s", "%s");
    size_t input_size = YGG_MSG_BUF;
    char *input = (char*)malloc(input_size);
    //char input[YGG_MSG_MAX];
    
    while (1) {
      int ret = rpc.recvRealloc(2, &input, &input_size);
      if (ret < 0)
	break;
      printf("maxMsgSrv(CPP): rpcRecv returned %d, input (size=%lu) %.10s...\n",
	     ret, input_size, input);
      ret = rpc.send(2, input, input_size);
      if (ret < 0) {
        printf("maxMsgSrv(CPP): SEND ERROR");
        break;
      }
    }

    printf("maxMsgSrv(CPP): Goodbye!\n");
    return 0;
}

