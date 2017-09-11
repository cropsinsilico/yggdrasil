#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>


/*
* Read file, send to queue, read back from queue, store to file
*/

int main(int argc, char *argv[]) {
    const int bufsz=8192;
    char buf[bufsz];
  
    printf("Hello from C\n");

    /* Matching with the the model yaml */
    PsiInput in = psi_input("input"); 
    PsiOutput out = psi_output("output");
    printf("hello_c: Created I/Os, %d, %d\n", in, out);

    // Receive input
    int ret;
    ret = psi_recv(in, buf, bufsz);
    if (ret < 0)
        perror("psi_recv");
    printf("hello_c: Received %d bytes: %s\n", ret, buf );

    // Send output
    ret = psi_send(out, buf, ret);
    if (ret < 0)
        perror("psi_send:");
    printf("hello_c: Send returns %d\n", ret);

    printf("Goodbye from C\n");
    
}

