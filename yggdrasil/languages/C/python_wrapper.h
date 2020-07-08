#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

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

#include <stdio.h>


#ifdef _MSC_VER
__declspec(dllexport) int PyObject_Print_STDOUT(PyObject* x);
#else
int PyObject_Print_STDOUT(PyObject* x);
#endif

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif