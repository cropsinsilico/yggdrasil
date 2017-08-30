
#include "PsiInterface.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>


/*
* Read file, send to queue, read back from queue, store to file
*/

void sig_handler(int signo) {
    printf("received signal %d\n", signo);
}


int main(int argc, char *argv[]) {
    const int bufsz=8192;
    char buf[bufsz];

    signal(SIGINT, sig_handler);

    printf("hello from C\n");

    /* Matching with the the model yaml */
    PsiInput in = psi_input("input"); 
    PsiOutput out = psi_output("output");
    printf("hello_c: created I/Os, %d, %d\n", in, out);

    int ret;
    ret = psi_recv(in, buf, bufsz);
    if (ret < 0)
        perror("psi_recv");
    printf("hello_c received %d bytes: %s\n", ret, buf );
    sleep(5);
    ret = psi_send(out, buf, ret);
    if (ret < 0)
        perror("psi_send:");
    printf("hello_c: send returns %d\n", ret);

    printf("bye\n");
    
}

