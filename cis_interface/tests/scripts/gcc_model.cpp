#include <stdio.h>
#include <PsiInterface.hpp>
extern "C" {
#include <hellofunc.h>
}

int main() {
  sleep(1);
  myPrint("GCC Model");
  return 0;
}
