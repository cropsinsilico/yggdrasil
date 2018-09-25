#include <stdio.h>
#include <stdlib.h>
#include "CisInterface.h"

#define BSIZE 1000


int main() {
    int ret;
    char adata[BSIZE];
    char bdata[BSIZE];
    char outbuf[BSIZE];

    // Get input and output channels matching yaml
    cisInput_t in1 = cisInput("input1_c");
    cisInput_t in2 = cisInput("static_c");
    cisOutput_t out1 = cisOutput("output_c");
    printf("SaM(C): Set up I/O channels\n");

    // Get input from input1 channel
    ret = cis_recv(in1, adata, BSIZE);
    if (ret < 0) {
      printf("SaM(C): ERROR RECV from input1\n");
      return -1;
    }
    int a = atoi(adata);
    printf("SaM(C): Received %d from input1\n", a);

    // Get input from static channel
    ret = cis_recv(in2, bdata, BSIZE);
    if (ret < 0) {
      printf("SaM(C): ERROR RECV from static\n");
      return -1;
    }
    int b = atoi(bdata);
    printf("SaM(C): Received %d from static\n", b);

    // Compute sum and send message to output channel
    int sum = a + b;
    sprintf(outbuf, "%d", sum);
    ret = cis_send(out1, outbuf, strlen(outbuf));
    if (ret != 0) {
      printf("SaM(C): ERROR SEND to output\n");
      return -1;
    }
    printf("SaM(C): Sent to output\n");

    return 0;
}
