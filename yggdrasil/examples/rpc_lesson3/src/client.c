#include "YggInterface.h"
#include <stdio.h>


int model_function(char* in_buf, uint64_t length_in_buf,
		   char** out_buf, uint64_t* length_out_buf) {
  // The WITH_GLOBAL_SCOPE macro is required to ensure that the comm persists
  // between function calls
  WITH_GLOBAL_SCOPE(yggRpc_t rpc = yggRpcClient("server_client", "%s", "%s"));
  printf("client(C): %s (length = %d)\n", in_buf, (int)(length_in_buf));
  int ret = rpcCallRealloc(rpc, in_buf, length_in_buf, out_buf, length_out_buf);
  if (ret < 0) {
    printf("client(C): RPC CALL ERROR\n");
    return -1;
  }
  return 0;
}
