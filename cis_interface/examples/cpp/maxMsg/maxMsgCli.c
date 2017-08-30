
#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

void rand_str(char *dest, size_t length) {
    char charset[] = "0123456789"
                     "abcdefghijklmnopqrstuvwxyz"
                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    while (length-- > 0) {
        size_t index = (double) rand() / RAND_MAX * (sizeof charset - 1);
        *dest++ = charset[index];
    }
    *dest = '\0';
}


int main(int argc, char *argv[]) {
    printf("maxMsgCli: hello psiMaxMsgSize is %d\n", PSI_MSG_MAX);

    // create a max message, send/recv and verify
    psiRpc_t rpc = psiRpcClient("cli_output", "%s", "cli_input", "%s");
    
    int fib;

    char output[PSI_MSG_MAX];
    char input[PSI_MSG_MAX];
    char verify[PSI_MSG_MAX];

    rand_str(output, PSI_MSG_MAX-1);
    output[PSI_MSG_MAX] == '\0';
    
    // save a copy of the string
    memcpy(verify, output, PSI_MSG_MAX);

    if (rpcCall(rpc, output, &input)) {
            printf("RPC error");
            exit(-1);
    }
    if (memcmp(output, input, PSI_MSG_MAX)) {
        printf("input/output do not match");
        exit(-1);
    } else {
        printf("maxCliMsg: CONFIRM\n");
    }

    // all done, say goodbye
    printf("maxMsgCli: bye\n");
    
}

