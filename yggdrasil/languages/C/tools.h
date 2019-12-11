#ifndef YGGTOOLS_H_
#define YGGTOOLS_H_

#ifdef _WIN32
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS 1
#endif
#endif

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <errno.h>
#include <time.h>


#ifdef _WIN32
#ifdef __cplusplus
#include <complex>
typedef std::complex<float> complex_float;
typedef std::complex<double> complex_double;
typedef std::complex<long double> complex_long_double;
#ifndef creal
#define creal(x) x.real()
#define crealf(x) x.real()
#define creall(x) x.real()
#define cimag(x) x.imag()
#define cimagf(x) x.imag()
#define cimagl(x) x.imag()
#endif
#else
#include <complex.h>
typedef _Fcomplex complex_float;
typedef _Dcomplex complex_double;
typedef _Lcomplex complex_long_double;
#endif
#else // Unix
#ifdef __cplusplus
#include <complex>
typedef std::complex<float> complex_float;
typedef std::complex<double> complex_double;
typedef std::complex<long double> complex_long_double;
#ifndef creal
#define creal(x) x.real()
#define crealf(x) x.real()
#define creall(x) x.real()
#define cimag(x) x.imag()
#define cimagf(x) x.imag()
#define cimagl(x) x.imag()
#endif
#else
#include <complex.h>
typedef float _Complex complex_float;
typedef double _Complex complex_double;
typedef long double _Complex complex_long_double;
#endif
#endif
#define print_complex(x) printf("%lf+%lfj\n", (double)creal(x), (double)cimag(x))


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
  
typedef struct complex_float_t {
  float re;
  float im;
} complex_float_t;
typedef struct complex_double_t {
  double re;
  double im;
} complex_double_t;
typedef struct complex_long_double_t {
  long double re;
  long double im;
} complex_long_double_t;
// Platform specific
#ifdef _WIN32
#include "regex/regex_win32.h"
#include "windows_stdint.h"  // Use local copy for MSVC support
// Prevent windows.h from including winsock.h
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include "getline_win32.h"
#include <process.h>
#define ygg_getpid _getpid
#define sleep(tsec) Sleep(1000*tsec)
#define usleep(usec) Sleep(usec/1000)
#else
#include "regex_posix.h"
#include <stdint.h>
#include <unistd.h>
#define ygg_getpid getpid
#endif

#define STRBUFF 100
  
/*! @brief Maximum message size. */
#ifdef IPCDEF
#define YGG_MSG_MAX 2048
#else
#define YGG_MSG_MAX 1048576
#endif
/*! @brief End of file message. */
#define YGG_MSG_EOF "EOF!!!"
/*! @brief Resonable size for buffer. */
#define YGG_MSG_BUF 2048
/*! @brief Sleep time in micro-seconds */
#define YGG_SLEEP_TIME 250000
/*! @brief Size for buffers to contain names of Python objects. */
#define PYTHON_NAME_SIZE 1000

/*! @brief Define old style names for compatibility. */
#define PSI_MSG_MAX YGG_MSG_MAX
#define PSI_MSG_BUF YGG_MSG_BUF
#define PSI_MSG_EOF YGG_MSG_EOF
#ifdef PSI_DEBUG
#define YGG_DEBUG PSI_DEBUG
#endif
static int _ygg_error_flag = 0;

/*! @brief Define macros to allow counts of variables. */
// https://codecraft.co/2014/11/25/variadic-macros-tricks/
#ifdef _WIN32
// https://stackoverflow.com/questions/48710758/how-to-fix-variadic-macro-related-issues-with-macro-overloading-in-msvc-mic
#define MSVC_BUG(MACRO, ARGS) MACRO ARGS  // name to remind that bug fix is due to MSVC :-)
#define _GET_NTH_ARG_2(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, N, ...) N
#define _GET_NTH_ARG(...) MSVC_BUG(_GET_NTH_ARG_2, (__VA_ARGS__))
#define COUNT_VARARGS(...) _GET_NTH_ARG("ignored", ##__VA_ARGS__, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
#define VA_MACRO(MACRO, ...) MSVC_BUG(CONCATE, (MACRO, COUNT_VARARGS(__VA_ARGS__)))(__VA_ARGS__)
#else
#define _GET_NTH_ARG(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, N, ...) N
#define COUNT_VARARGS(...) _GET_NTH_ARG("ignored", ##__VA_ARGS__, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
#endif
#define UNUSED(arg) ((void)&(arg))

/*!
  @brief Get an unsigned long seed from the least significant 32bits of a pointer.
  @param[in] ptr Pointer that should be turned into a seed.
  @return Unsigned long seed.
 */
static inline
unsigned long ptr2seed(void *ptr) {
  uint64_t v = (uint64_t)ptr;
  unsigned long seed = (unsigned long)(v & 0xFFFFFFFFLL);
  return seed;
};


/*! @brief Structure used to wrap va_list and allow pointer passing.
@param va va_list Wrapped variable argument list.
*/
typedef struct va_list_t {
  va_list va;
} va_list_t;


/*! @brief Structure used to wrap Python objects. */
typedef struct python_t {
  char name[PYTHON_NAME_SIZE];
  void *args;
  void *kwargs;
  PyObject *obj;
} python_t;


/*!
  @brief Initialize a structure to contain a Python object.
  @returns python_t New Python object structure.
 */
static inline
python_t init_python() {
  python_t out;
  out.name[0] = '\0';
  out.args = NULL;
  out.kwargs = NULL;
  out.obj = NULL;
  return out;
};

  
/*!
  @brief Initialize Numpy arrays if it is not initalized.
  @returns int 0 if successful, other values indicate errors.
 */
static inline
int init_numpy_API() {
  if (PyArray_API == NULL) {
    if (_import_array() < 0) {
      return -2;
    }
  }
  return 0;
};


/*!
  @brief Initialize Python if it is not initialized.
  @returns int 0 if successful, other values indicate errors.
 */
static inline
int init_python_API() {
  if (!(Py_IsInitialized())) {
    Py_Initialize();
    if (!(Py_IsInitialized()))
      return -1;
  }
  return init_numpy_API();
};


//==============================================================================
/*!
  Logging

  Alliases are set at compile-time based on the value of YGG_CLIENT_DEBUG. If 
  set to INFO, only messages logged with info or error alias are printed. If
  set to DEBUG, messages logged with error, info or debug aliases are printed.
  Otherwise, only error messages are printed. If the YGG_CLIENT_DEBUG is
  changed, any code including this header must be recompiled for the change to
  take effect.

*/
//==============================================================================

/*!
  @brief Print a log message.
  Prints a formatted message, prepending it with the process id and appending
  it with a newline.
  @param[in] prefix a constant character pointer to the prefix that should
  preceed the message and process id.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ap va_list of arguments to be formatted in the format string.
 */
static inline
void yggLog(const char* prefix, const char* fmt, va_list ap) {
  fprintf(stdout, "%s: %d: ", prefix, ygg_getpid());
  vfprintf(stdout, fmt, ap);
  fprintf(stdout, "\n");
  fflush(stdout);
};

/*!
  @brief Print an info log message.
  Prints a formatted message, prepending it with INFO and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void yggInfo(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  yggLog("INFO", fmt, ap);
  va_end(ap);
};
  
/*!
  @brief Print an debug log message.
  Prints a formatted message, prepending it with DEBUG and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void yggDebug(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  yggLog("DEBUG", fmt, ap);
  va_end(ap);
};
  
/*!
  @brief Print an error log message from a variable argument list.
  Prints a formatted message, prepending it with ERROR and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ap va_list Variable argument list.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void yggError_va(const char* fmt, va_list ap) {
  yggLog("ERROR", fmt, ap);
  _ygg_error_flag = 1;
};

/*!
  @brief Print an error log message.
  Prints a formatted message, prepending it with ERROR and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void yggError(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  yggError_va(fmt, ap);
  va_end(ap);
};

#ifdef YGG_DEBUG
#if YGG_DEBUG <= 10
#define ygglog_error yggError
#define ygglog_info yggInfo
#define ygglog_debug yggDebug
#elif YGG_DEBUG <= 20
#define ygglog_error yggError
#define ygglog_info yggInfo
#define ygglog_debug while (0) yggDebug
#elif YGG_DEBUG <= 40
#define ygglog_error yggError
#define ygglog_info while (0) yggInfo
#define ygglog_debug while (0) yggDebug
#else
#define ygglog_error while (0) yggError
#define ygglog_info while (0) yggInfo
#define ygglog_debug while (0) yggDebug
#endif
#else
#define ygglog_error yggError
#define ygglog_info while (0) yggInfo
#define ygglog_debug while (0) yggDebug
#endif

/*!
  @brief Get the length (in bytes) of a character array containing 4 byte
  unicode characters.
  @param[in] strarg char* Pointer to character array.
  @returns size_t Length of strarg in bytes.
 */
static inline
size_t strlen4(char* strarg) {
  if(!strarg)
    return 0; //strarg is NULL pointer
  char* str = strarg;
  for(;*str;str+=4)
    ; // empty body
  return (str - strarg);
}

/*!
  @brief Called snprintf and realloc buffer if the formatted string is
  larger than the provided buffer.
  @param[in] dst char** Pointer to buffer where formatted message
  should be stored.
  @param[in,out] max_len size_t* Pointer to maximum size of buffer
  that will be modified when the buffer is reallocated.
  @param[in,out] offset size_t* Pointer to offset in buffer where the
  formatted message should be stored. This will be updated to the end
  of the updated message.
  @param[in] format_str const char* Format string that should be used.
  @param[in] ... Additional arguments are passed to snprintf as
  parameters for formatting.
  @returns int -1 if there is an error, otherwise the number of new
  characters written to the buffer.
 */
static inline
int snprintf_realloc(char** dst, size_t* max_len, size_t* offset,
		     const char* format_str, ...) {
  va_list arglist;
  va_start(arglist, format_str);
  int fmt_len = 0;
  while (1) {
    va_list arglist_copy;
    va_copy(arglist_copy, arglist);
    fmt_len = vsnprintf(dst[0] + offset[0],
			max_len[0] - offset[0],
			format_str, arglist_copy);
    if (fmt_len > (int)(max_len[0] - offset[0])) {
      max_len[0] = max_len[0] + fmt_len + 1;
      char* temp = (char*)realloc(dst[0], max_len[0]);
      if (temp == NULL) {
	ygglog_error("snprintf_realloc: Error reallocating buffer.");
	fmt_len = -1;
	break;
      }
      dst[0] = temp;
    } else {
      offset[0] = offset[0] + fmt_len;
      break;
    }
  }
  va_end(arglist);
  return fmt_len;
};

/*!
  @brief Check if a character array matches a message and is non-zero length.
  @param[in] pattern constant character pointer to string that should be checked.
  @param[in] buf constant character pointer to string that should be checked.
  @returns int 1 if buf matches pattern, 0 otherwise.
 */
static inline
int not_empty_match(const char *pattern, const char *buf) {
  if (buf == NULL)
    return 0;
  if (buf[0] == '\0')
    return 0;
  if (strcmp(buf, pattern) == 0) {
    return 1;
  } else {
    return 0;
  }
};

/*!
  @brief Check if a character array matches the internal EOF message.
  @param[in] buf constant character pointer to string that should be checked.
  @returns int 1 if buf is the EOF message, 0 otherwise.
 */
static inline
int is_eof(const char *buf) {
  return not_empty_match(YGG_MSG_EOF, buf);
};

/*!
  @brief Check if a character array matches "recv".
  @param[in] buf constant character pointer to string that should be checked.
  @returns int 1 if buf is the "recv" message, 0 otherwise.
 */
static inline
int is_recv(const char *buf) {
  return not_empty_match("recv", buf);
};

/*!
  @brief Check if a character array matches "send".
  @param[in] buf constant character pointer to string that should be checked.
  @returns int 1 if buf is the "send" message, 0 otherwise.
 */
static inline
int is_send(const char *buf) {
  return not_empty_match("send", buf);
};

  
/*! @brief Method for skipping a number of bytes in the argument list.
  @param[in] ap va_list_t* Structure containing variable argument list.
  @param[in] nbytes size_t Number of bytes that should be skipped.
 */
static inline
void va_list_t_skip(va_list_t *ap, size_t nbytes) {
  if (nbytes == sizeof(void*)) {
    va_arg(ap->va, void*);
  } else if (nbytes == sizeof(size_t)) {
    va_arg(ap->va, size_t);
  } else {
    printf("WARNING: Cannot get argument of size %zd.\n", nbytes);
    va_arg(ap->va, void*);
    // va_arg(ap->va, char[nbytes]);
  }
};

  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGTOOLS_H_*/
