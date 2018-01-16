#include <../tools.h>

#ifndef CISSERIALIZEBASE_H_
#define CISSERIALIZEBASE_H_


/*! @brief Serializer types. */
enum seri_enum { DIRECT_SERI, FORMAT_SERI,
		 ASCII_TABLE_SERI, ASCII_TABLE_ARRAY_SERI };
typedef enum seri_enum seri_type;

/*!
  @brief Serializer structure.
*/
typedef struct seri_t {
  seri_type type; //!< Serializer type.
  void *info; //!< Pointer to any extra info serializer requires.
} seri_t;


/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to memory where serialized message should be
  stored.
  @param[in] buf_siz int Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error. 
 */
static inline
int serialize_direct(const seri_t s, char *buf, const int buf_siz, va_list ap) {
  if (s.type != DIRECT_SERI)
    return -1;
  char *msg = va_arg(ap, char*);
  int ret = (int)strlen(msg);
  if ((ret + 1) < buf_siz)
    strcpy(buf, msg);
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
int deserialize_direct(const seri_t s, const char *buf, const int buf_siz,
		       va_list ap) {
  if (s.type != DIRECT_SERI)
    return -1;
  char **msg = va_arg(ap, char**);
  *msg = (char*)realloc(*msg, buf_siz + 1);
  memcpy(*msg, buf, buf_siz);
  (*msg)[buf_siz] = '\0';
  return 1;
};
  

#endif /*CISSERIALIZEBASE_H_*/
