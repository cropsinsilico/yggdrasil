#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <regex.h>
#include <../tools.h>
#include <SerializeBase.h>
#include <FormatSerialize.h>
#include <AsciiTableSerialize.h>

#ifndef CISSERIALIZE_H_
#define CISSERIALIZE_H_


/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz int Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize(const seri_t s, char **buf, const int buf_siz,
	      const int allow_realloc, va_list ap) {
  seri_type t = s.type;
  int ret = -1;
  if (t == DIRECT_SERI)
    ret = serialize_direct(s, *buf, buf_siz, ap);
  else if (t == FORMAT_SERI)
    ret = serialize_format(s, *buf, buf_siz, ap);
  else if (t == ASCII_TABLE_SERI)
    ret = serialize_ascii_table(s, *buf, buf_siz, ap);
  else if (t == ASCII_TABLE_ARRAY_SERI)
    ret = serialize_ascii_table_array(s, *buf, buf_siz, ap);
  else {
    cislog_error("serialize: Unsupported seri_type %d", t);
  }
  if (ret > buf_siz) {
    if (allow_realloc) {
      *buf = (char*)realloc(*buf, ret+1); 
      ret = serialize(s, buf, ret+1, 0, ap);
    } else {
      cislog_error("serialize: encoded message too large for the buffer. (buf_siz=%d, len=%d)",
		   buf_siz, ret);
      ret = -1;
    }
  }
  return ret;
}

/*!
  @brief Deserialize message to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz int Size of buf.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize(const seri_t s, const char *buf, const int buf_siz, va_list ap) {
  seri_type t = s.type;
  int ret = -1;
  if (t == DIRECT_SERI)
    ret = deserialize_direct(s, buf, buf_siz, ap);
  else if (t == FORMAT_SERI)
    ret = deserialize_format(s, buf, buf_siz, ap);
  else if (t == ASCII_TABLE_SERI)
    ret = deserialize_ascii_table(s, buf, buf_siz, ap);
  else if (t == ASCII_TABLE_ARRAY_SERI)
    ret = deserialize_ascii_table_array(s, buf, buf_siz, ap);
  else {
    cislog_error("deserialize: Unsupported seri_type %d", t);
  }
};


#endif /*CISSERIALIZE_H_*/
