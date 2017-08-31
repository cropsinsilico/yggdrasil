// Author Venkatraman Srinivasan
#include <stdio.h>
#include <stdlib.h>

#include "PsiInterface.h"

int main(int argc,char *argv[]){
  printf("Hello from C!\n");
  const uint BSIZE = 8192; // the max
  char buf1[BSIZE];
  char buf2[BSIZE];
  char outbuf[BSIZE];
  char finalbuf[BSIZE];
  
  PsiInput Input = psi_input("cinput1");
  PsiInput Static = psi_input("cstatic");
  PsiOutput Output = psi_output("coutput");
  PsiInput inFinal = psi_input("cfinal");
  PsiOutput outFinal = psi_output("finalOut");
  
  psi_recv(Input, buf1, BSIZE);
  printf("C received %s from cinput1\n", buf1);
  psi_recv(Static, buf2, BSIZE);
  printf("C received %s from cstatic\n", buf2);
  sprintf(outbuf,"%d", atoi(buf1) + atoi(buf2));
  psi_send(Output, outbuf, strlen(outbuf));
  printf("C sent %s to coutput\n", outbuf);
  
  psi_recv(inFinal, finalbuf, BSIZE);
  printf("C received %s from cfinal\n", finalbuf);
  sprintf(outbuf, "%s", finalbuf);
  psi_send(outFinal, outbuf, strlen(outbuf));
  printf("C sent %s to finalOut\n", outbuf);

  printf("Goodbye from C!\n");
  return 0;
}
