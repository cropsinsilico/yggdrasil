#ifndef YGGTOOLS_H_
#define YGGTOOLS_H_

#include "datatypes/datatypes.h"

#ifdef _OPENMP
#include <omp.h>
#endif

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <errno.h>
#include <time.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

// Platform specific
#ifdef _WIN32
#include "regex/regex_win32.h"
#include "getline_win32.h"
#else
#include "regex_posix.h"
#endif
#ifdef _MSC_VER
// Prevent windows.h from including winsock.h
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <process.h>
#define ygg_getpid _getpid
#define sleep(tsec) Sleep(1000*tsec)
#define usleep(usec) Sleep(usec/1000)
#else
#include <unistd.h>
#define ygg_getpid getpid
#endif

#include "constants.h"

#define STRBUFF 100
#ifdef PSI_DEBUG
#define YGG_DEBUG PSI_DEBUG
#endif
  
static int _ygg_error_flag = 0;

/*! @brief Define macros to allow counts of variables. */
// https://codecraft.co/2014/11/25/variadic-macros-tricks/
#ifdef _MSC_VER
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

#define YGG_BEGIN_VAR_ARGS_CPP(name, first_arg, nargs, realloc)	\
  va_list_t name = init_va_list(&nargs, realloc, 0);		\
  va_list* name ## _va = get_va_list(name);			\
  va_start(*name ## _va, first_arg)
#define YGG_BEGIN_VAR_ARGS(name, first_arg, nargs, realloc)	\
  va_list_t name = init_va_list(&nargs, realloc, 1);		\
  va_list* name ## _va = get_va_list(name);			\
  va_start(*name ## _va, first_arg)
#define YGG_END_VAR_ARGS(name)			\
  end_va_list(&name)

/*! @brief Memory to allow thread association to be set via macro. */
static int global_thread_id = -1;
#define ASSOCIATED_WITH_THREAD(COMM, THREAD) global_thread_id = THREAD; COMM; global_thread_id = -1;
#ifdef _OPENMP
#pragma omp threadprivate(global_thread_id)
#endif

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


/*!
  @brief Get the ID for the current thread (if inside one).
  @returns int Thread ID.
 */
static inline
int get_thread_id() {
  int out = 0;
  if (global_thread_id >= 0)
    return global_thread_id;
#ifdef _OPENMP
  if (omp_in_parallel())
    out = omp_get_thread_num();
/* #elif defined pthread_self */
/*   // TODO: Finalize/test support for pthread */
/*   out = pthread_self(); */
#endif
  return out;
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
  fprintf(stdout, "%s: %d:%d ", prefix, ygg_getpid(), get_thread_id());
  char *model_name = getenv("YGG_MODEL_NAME");
  if (model_name != NULL) {
    fprintf(stdout, "%s", model_name);
    char *model_copy = getenv("YGG_MODEL_COPY");
    if (model_copy != NULL) {
      fprintf(stdout, "_copy%s", model_copy);
    }
    fprintf(stdout, " ");
  }
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

#ifndef DOXYGEN_SHOULD_SKIP_THIS
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
#endif // DOXYGEN_SHOULD_SKIP_THIS

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

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGTOOLS_H_*/
