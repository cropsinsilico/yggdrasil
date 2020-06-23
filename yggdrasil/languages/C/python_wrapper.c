#include "python_wrapper.h"

int PyObject_Print_STDOUT(PyObject* x) {
  return PyObject_Print(x, stdout, 0);
}
