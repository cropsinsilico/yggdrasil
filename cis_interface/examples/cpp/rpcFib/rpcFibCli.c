
#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


int main(int argc, char *argv[]) {
    char *notset = "NOT SET";
    char *ns = getenv("PSI_NAMESPACE");
    if (ns == NULL) ns = notset;
    char *rank = getenv("PSI_RANK");
    if (rank == NULL) rank = notset;
    char *hostname = getenv("PSI_HOST");
    if (hostname == NULL) hostname = notset;

   
    printf("fibcli(C): hello, on host %s with PSI_NAMESPACE %s and PSI_RANK %s\n", hostname, ns, rank);
    int iterations = atoi(argv[1]);
    printf("running %d iterations\n", iterations);

    // send fibbonacci via RPC
    // create the rpc object to make the calls
    psiRpc_t rpc = psiRpcClient("cli_fib", "%d", "cli_fib", "%d %d");
    
    // a place for the return value
    int fib = -1;
    int fibNo = -1;

    // make a bunch of rpc's and display the results
    for (int i = 1; i <= iterations; i++) {
        printf("fibcli(C): fib(->%-2d) ::: ", i);
        if (rpcCall(rpc, i, &fibNo, &fib) < 0) {
            printf("RPC error, exit");
            exit(-1);
        }
        printf("fib(%2d<-) = %-2d<-\n", fibNo, fib);
    }

    // all done, say goodbye
    printf("fibcli(C) says bye\n");
    exit(0);
    
}

