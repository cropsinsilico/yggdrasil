#ifndef YGGSERIALIZEBASE_H_
#define YGGSERIALIZEBASE_H_

#include <../tools.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief Serializer types. */
enum seri_enum { DIRECT_SERI, FORMAT_SERI, ARRAY_SERI,
		 ASCII_TABLE_SERI, ASCII_TABLE_ARRAY_SERI,
		 PLY_SERI, OBJ_SERI};
typedef enum seri_enum seri_type;

/*!
  @brief Serializer structure.
*/
typedef struct seri_t {
  seri_type type; //!< Serializer type.
  void *info; //!< Pointer to any extra info serializer requires.
  size_t size_info; //!< Size of allocate space for info.
} seri_t;


/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to memory where serialized message should be
  stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error. 
 */
static inline
int serialize_direct(const seri_t s, char *buf, const size_t buf_siz,
		     int *args_used, va_list ap) {
  args_used[0] = 0;
  if (s.type != DIRECT_SERI)
    return -1;
  char *msg = va_arg(ap, char*);
  args_used[0] = 1;
  int ret = (int)strlen(msg);
  if ((ret + 1) < (int)buf_siz)
    strcpy(buf, msg);
  return ret;
};

/*!
  @brief Deserialize message to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[out] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize_direct(const seri_t s, const char *buf, const size_t buf_siz,
		       va_list ap) {
  if (s.type != DIRECT_SERI)
    return -1;
  char **msg = va_arg(ap, char**);
  *msg = (char*)realloc(*msg, buf_siz + 1);
  memcpy(*msg, buf, buf_siz);
  (*msg)[buf_siz] = '\0';
  return 1;
};
  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGSERIALIZEBASE_H_*/
