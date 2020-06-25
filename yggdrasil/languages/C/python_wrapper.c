#include "python_wrapper.h"

int PyObject_Print_STDOUT(PyObject* x) {
#if defined(_WIN32) && !defined(_MSC_VER)
  printf("This function was called from outside the MSVC CRT and will be"
  		 "skipped in order to avoid a segfault incurred due to the "
  		 "Python C API's use of the MSVC CRT (particularly the FILE* "
  		 "datatype). To fix this, please ensure "
  		 "that the MSVC compiler (cl.exe) is available and cleanup any "
  		 "remaining compilation products in order to trigger yggdrasil "
  		 "to recompile your model during the next run.\n");
  return 0;
#else
  return PyObject_Print(x, stdout, 0);
#endif
}
