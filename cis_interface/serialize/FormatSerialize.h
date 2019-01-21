#ifndef YGGFORMATSERIALIZE_H_
#define YGGFORMATSERIALIZE_H_

#include <../tools.h>
#include <SerializeBase.h>
#include <../dataio/AsciiTable.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize_format(const seri_t s, char *buf, const size_t buf_siz,
		     int *args_used, va_list ap) {
  args_used[0] = 0;
  char *fmt = (char*)s.info;
  int ret = vsnprintf(buf, buf_siz, fmt, ap);
  ygglog_debug("serialize_format: vsnprintf returns %d", ret);
  if (ret < 0) {
    ygglog_error("serialize_format: vsnprintf encoding error");
    ret = -1;
  } else {
    args_used[0] = count_formats(fmt);
  }
  return ret;
};

/*!
  @brief Deserialize message to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_format(const seri_t s, const char *buf, const size_t buf_siz,
		       va_list ap) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  buf_siz;
#endif
  // Simplify format
  char *fmt0 = (char*)s.info;
  size_t fmt_siz = 2*strlen(fmt0) + 1;
  char *fmt = (char*)malloc(sizeof(char) * fmt_siz);
  if (fmt == NULL) {
    ygglog_error("deserialize_format: Failed to allocate buffer for simplified format.");
    return -1;
  }
  strcpy(fmt, fmt0);
  int sret = simplify_formats(fmt, fmt_siz);
  if (sret < 0) {
    ygglog_error("deserialize_format: simplify_formats returned %d", sret);
    free(fmt);
    return -1;
  }
  ygglog_debug("deserialize_format: simplify_formats returns %d", sret);
  int nfmt = count_formats(fmt);
  ygglog_debug("deserialize_format: Simplified format contains %d fields", nfmt);
  // Interpret message
  sret = vsscanf(buf, fmt, ap);
  if (sret != nfmt) {
    ygglog_error("deserialize_format: vsscanf filled %d variables, but there are %d formats",
		 sret, nfmt);
    free(fmt);
    return -1;
  }
  ygglog_debug("deserialize_format: vsscanf returns %d", sret);
  free(fmt);
  return sret;
};


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGFORMATSERIALIZE_H_*/
