
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
    char *host = getenv("PSI_HOST");
    if (host == NULL) host = notset;

    printf("Pfibcli(C): hello, system %s, PSI_NAMESPACE %s, PSI_RANK %s\n", host, ns, rank);
    int iterations = atoi(argv[1]);
    printf("running %d iterations\n", iterations);
    

    // send fibbonacci via RPC
    // create the rpc object to make the calls
    psiRpc_t rpc = psiRpcClient("cli_par_fib", "%d", "cli_par_fib", "%d %d");
    
    // a place for the return value
    int fib = -1;
    int fibNo = -1;

    // make a bunch of rpc's and display the results
    for (int i = 1; i <= iterations; i++) {
      printf("Pfibcli(C): fib(->%2d) ::: ", i);
      if (rpcSend(rpc, i)) {
	printf("RPC send error");
	exit(-1);
      }
    }
    printf("\n");
    for (int i = 1; i <= iterations; i++) {
      if (rpcRecv(rpc, &fibNo, &fib)) {
	printf("RPC recv error");
	exit(-1);
      }
      printf("Pfibcli(C) : fib(%2d<-) = %-2d<-\n", fibNo, fib);
    }

    // all done, say goodbye
    printf("Pfibcli(C) says bye\n");
    exit(0);
    
}

