// Author Venkatraman Srinivasan
#include <stdio.h>
#include <stdlib.h>

#include "PsiInterface.h"

int main(int argc,char *argv[]){
    const uint BSIZE = 8192; // the max
    char buf1[BSIZE];
    char buf2[BSIZE];
    char outbuf[BSIZE];

    printf("start");
    PsiInput Static = psi_input("static");
    PsiInput Qin = psi_input("qin");
    PsiOutput Qout = psi_output("qout");
    PsiOutput Output = psi_output("output");

    
    psi_recv(Static, buf1, BSIZE);
    psi_send(Qout, buf1, strlen(buf1));
    psi_recv(Qin, buf2, BSIZE);
    sprintf(outbuf,"Sum = %d", atoi(buf1) + atoi(buf2));
    psi_send(Output, outbuf, strlen(outbuf));
    return 0;
}
