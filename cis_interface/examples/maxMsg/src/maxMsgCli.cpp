#include "PsiInterface.hpp"
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
  
    printf("maxMsgCli(CPP): Hello PSI_MSG_MAX is %d.\n", PSI_MSG_MAX);

    char output[PSI_MSG_MAX];
    char input[PSI_MSG_MAX];
    char verify[PSI_MSG_MAX];
    
    // Create a max message, send/recv and verify
    PsiRpcClient rpc("maxMsgSrv_maxMsgCli", "%s", "%s");
    
    // Create a max message
    rand_str(output, PSI_MSG_MAX-1);
    output[PSI_MSG_MAX] == '\0';
    
    // Save a copy of the string
    memcpy(verify, output, PSI_MSG_MAX);

    // Call RPC server
    if (rpc.call(2, output, &input) < 0) {
      printf("maxMsgCli(CPP): RPC ERROR\n");
      exit(-1);
    }

    // Check to see if response matches
    if (memcmp(output, input, PSI_MSG_MAX)) {
        printf("maxMsgCli(CPP): ERROR: input/output do not match\n");
        exit(-1);
    } else {
        printf("maxMsgCli(CPP): CONFIRM\n");
    }

    // All done, say goodbye
    printf("maxMsgCli(CPP): Goodbye!\n");
    
}

