#include <../tools.h>
#include <SerializeBase.h>
#include <../dataio/AsciiTable.h>

#ifndef CISFORMATSERIALIZE_H_
#define CISFORMATSERIALIZE_H_


/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz int Size of memory allocated to buf.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize_format(const seri_t s, char *buf, const int buf_siz, va_list ap) {
  char *fmt = (char*)s.info;
  int ret = vsnprintf(buf, buf_siz, fmt, ap);
  cislog_debug("serialize_format: vsnprintf returns %d", ret);
  if (ret < 0) {
    cislog_error("serialize_format: vsnprintf encoding error");
    ret = -1;
  }
  return ret;
};

/*!
  @brief Deserialize message to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz int Size of buf.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_format(const seri_t s, const char *buf, const int buf_siz, va_list ap) {
  // Prevent C4100 warning on windows by referencing param
  buf_siz;
  // Simplify format
  char *fmt0 = (char*)s.info;
  char fmt[PSI_MSG_MAX];
  strcpy(fmt, fmt0);
  int sret = simplify_formats(fmt, PSI_MSG_MAX);
  if (sret < 0) {
    cislog_error("deserialize_format: simplify_formats returned %d", sret);
    return -1;
  }
  cislog_debug("deserialize_format: simplify_formats returns %d", sret);
  int nfmt = count_formats(fmt);
  // Interpret message
  sret = vsscanf(buf, fmt, ap);
  if (sret != nfmt) {
    cislog_error("deserialize_format: vsscanf filled %d variables, but there are %d formats",
		 sret, nfmt);
    return -1;
  }
  cislog_debug("deserialize_format: vsscanf returns %d", sret);
  return sret;
};


#endif /*CISFORMATSERIALIZE_H_*/
