#include <omp.h>
#include "YggInterface.h"
#include <stdio.h>


int model_function(char* in_buf, uint64_t length_in_buf,
		   char** out_buf, uint64_t* length_out_buf) {
  int nthreads = atoi(getenv("NTHREAD"));
  omp_set_num_threads(nthreads);
  #pragma omp parallel
  for (int i = 0; i < nthreads; ++i){
    char* out_temp = NULL;
    uint64_t length_out_temp = 0;
    char** out_buf_temp = &out_temp;
    uint64_t* length_out_buf_temp = &length_out_temp;
    if (i == 0) {
      out_buf_temp = out_buf;
      length_out_buf_temp = length_out_buf;
    }
    
    // The WITH_GLOBAL_SCOPE macro is required to ensure that the comm persists
    // between function calls
    WITH_GLOBAL_SCOPE(yggRpc_t rpc = yggRpcClient("server_client", "%s", "%s"));
    printf("client(C:%d): %s (length = %d)\n",
	   i, in_buf, (int)(length_in_buf));
    int ret = rpcCallRealloc(rpc, in_buf, length_in_buf,
			     out_buf_temp, length_out_buf_temp);
    if (ret < 0) {
      printf("client(C:%d): RPC CALL ERROR\n", i);
      return -1;
    }
  }
  return 0;
}
