#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/ndarrayobject.h>
#include <numpy/npy_common.h>
#define _DEBUG
#else
#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/ndarrayobject.h>
#include <numpy/npy_common.h>
#endif

int main(int argc,char *argv[]) {
  int out = 0;
  // Py_SetProgramName(L"/private/tmp/venv_20.0.15/bin/python");
  if (!(Py_IsInitialized())) {
    Py_Initialize();
    if (!(Py_IsInitialized())) {
      printf("Error initializing Python.\n");
      out = -1;
    }
  }
  if (Py_IsInitialized() && (PyArray_API == NULL)) {
    if (_import_array() < 0) {
      printf("Error initializing Numpy.\n");
      PyErr_Print();
      out = -1;
    }
  }
  if (out == 0) {
    printf("Successfully intialized.\n");
  }
  if (Py_IsInitialized()) {
    Py_Finalize();
  }
  return out;
}
