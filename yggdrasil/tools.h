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


#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

// Platform specific
#ifdef _WIN32
#include "regex/regex_win32.h"
#include "stdint.h"  // Use local copy for MSVC support
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
