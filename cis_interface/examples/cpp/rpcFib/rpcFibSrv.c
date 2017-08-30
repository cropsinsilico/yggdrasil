
#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


int main(int argc, char *argv[]) {
    printf("hello\n");
    char *notset = "NOT SET";
    char *ns = getenv("PSI_NAMESPACE");
    if (ns == NULL) ns = notset;
    char *rank = getenv("PSI_RANK");
    if (rank == NULL) rank = notset;
    char *host = getenv("PSI_HOST");
    if (host == NULL) host = notset;

    int timeSleep = atoi(argv[1]);
    printf("fibsrv(C): hello, on system %s, PSI_NAMESPACE %s, PSI_RANK %s, sleep %d\n",
        host, ns, rank, timeSleep);
  

    // send fibbonacci via RPC
    // create the rpc object to make the calls
    psiRpc_t rpc = psiRpcServer("srv_fib", "%d", "srv_fib", "%d %d");

    // loop serving calls, break loop on error
    // client exit will close the channel and recv will fail
    int input;
    while (1) {
        printf("fibsrv(C) <- ");
        int ret = rpcRecv(rpc, &input);
        if (ret < 0) {
            printf("fibsrv(C): end of input\n");
            break;
        }
        printf("%-2d ::: ", input);
        
        // received a value, compute the fib(input), loop style
        int result = 1;
        int prevResult = 1;
        int prevPrev = 0;
        int idx = 1;
        while(idx++ < input){
            result = prevResult + prevPrev;
            prevPrev = prevResult;
            prevResult = result;
        }
        if (timeSleep) 
            sleep(timeSleep);
        printf("-> (%-2d, %d)\n", input, result);
        rpcSend(rpc, input, result);
    }

    printf("fibsrv(C) says goobye\n");
}

