#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <errno.h>
#include <time.h>
#include "c_wrappers.h"
void * ygg_input_ff(const char *name) {
  printf("here!\n");
  fflush(stdout);
  sleep(10000000000);
  return (void*)yggInput(name);
};
