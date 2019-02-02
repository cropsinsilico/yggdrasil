#include <stdio.h>
#include <stdlib.h>
#include "YggInterface.hpp"

#define BSIZE 1000


int main() {
    int ret;
    char adata[BSIZE];
    char bdata[BSIZE];
    char outbuf[BSIZE];

    // Get input and output channels matching yaml
    YggInput in1("input1_cpp");
    YggInput in2("static_cpp");
    YggOutput out1("output_cpp");
    printf("SaM(CPP): Set up I/O channels\n");

    // Get input from input1 channel
    ret = in1.recv(adata, BSIZE);
    if (ret < 0) {
      printf("SaM(CPP): ERROR RECV from input1\n");
      return -1;
    }
    int a = atoi(adata);
    printf("SaM(CPP): Received %d from input1\n", a);

    // Get input from static channel
    ret = in2.recv(bdata, BSIZE);
    if (ret < 0) {
      printf("SaM(CPP): ERROR RECV from static\n");
      return -1;
    }
    int b = atoi(bdata);
    printf("SaM(CPP): Received %d from static\n", b);

    // Compute sum and send message to output channel
    int sum = a + b;
    sprintf(outbuf, "%d", sum);
    ret = out1.send(outbuf, strlen(outbuf));
    if (ret != 0) {
      printf("SaM(CPP): ERROR SEND to output\n");
      return -1;
    }
    printf("SaM(CPP): Sent to output\n");
    
    return 0;
}
