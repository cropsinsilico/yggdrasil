#include <iostream>
// Include methods for input/output channels
#include "YggInterface.hpp"

#define MYBUFSIZ 1000

int main(int argc, char *argv[]) {
  // This must be set to prevent dialog box on windows for unhandled exception
#ifdef _WIN32
  SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
  _set_abort_behavior(0,_WRITE_ABORT_MSG);
#endif
  // Throw an error or return a non-zero value to indicate an error
  throw "Test error";
  return -1;
}
