// Author Venkatraman Srinivasan
#include <stdio.h>
#include <stdlib.h>

#include "PsiInterface.h"

int main(int argc,char *argv[]){
    const uint BSIZE = 8192; // the max
    char buf1[BSIZE];
    char buf2[BSIZE];
    char outbuf[BSIZE];

    PsiInput Input = psi_input("input1");
    PsiInput Static = psi_input("static");
    PsiOutput Output = psi_output("output");

    psi_recv(Input, buf1, BSIZE);
    psi_recv(Static, buf2, BSIZE);
    sprintf(outbuf,"Sum = %d", atoi(buf1) + atoi(buf2));
    psi_send(Output, outbuf, strlen(outbuf));
    return 0;
}
