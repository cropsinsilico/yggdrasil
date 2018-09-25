#ifndef CISSERIALIZE_H_
#define CISSERIALIZE_H_

#include "../tools.h"
#include "SerializeBase.h"
#include "FormatSerialize.h"
#include "AsciiTableSerialize.h"
#include "PlySerialize.h"
#include "ObjSerialize.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*!
  @brief Create an empty serializer structure.
  @returns seri_t Empty serializer.
 */
static inline
seri_t empty_serializer() {
  seri_t s;
  s.type = DIRECT_SERI; // Can't be -1 (was that used?)
  s.info = NULL;
  s.size_info = 0;
  return s;
};

/*!
  @brief Update serializer with provided information.
  @param[in] s seri_t * Address of serializer that should be updated. If NULL,
  one is created.
  @param[in] type int Type that should be updated for the serializer. If
  negative, the type will be set depending on if info is NULL or not.
  @param[in] info void * Information that should be copied to the serializer.
  @returns int -1 if there is an error, 0 otherwise.
*/
static inline
int update_serializer(seri_t *s, int type, const void *info) {
  // Malloc if not initialized
  if (s == NULL) {
    cislog_error("update_serializer: Pointer to serializer is NULL.");
    return -1;
  }
  // Copy information
  if ((type == ASCII_TABLE_SERI) || (type == ASCII_TABLE_ARRAY_SERI)) {
    asciiTable_t *handle = (asciiTable_t*)malloc(sizeof(asciiTable_t));
    { // Limit content of format_str so double free not triggered
      char *format_str;
      if (info == NULL) {
	format_str = (char*)(s->info);
      } else {
	format_str = (char*)info;
      }
      if (handle == NULL) {
	cislog_error("update_serializer: Failed to allocate for asciiTable.");
	return -1;
      }
      handle[0] = asciiTable("seri", "0", format_str, NULL, NULL, NULL);
    }
    if (s->info != NULL) {
      free(s->info);
    }
    s->size_info = sizeof(asciiTable_t);
    s->info = (void*)handle;
  } else if (info == NULL) {
    if (type < 0) {
      type = DIRECT_SERI;
    }
  } else {
    char *format_str = (char*)info;
    s->size_info = 2*strlen(format_str) + 1;
    void *t_sinfo = (void*)realloc(s->info, s->size_info);
    if (t_sinfo == NULL) {
      cislog_error("update_serializer: Failed to reallocate for format string.");
      s->size_info = 0;
      free(s->info);
      return -1;
    }
    s->info = t_sinfo;
    strcpy((char*)(s->info), format_str);
    // size_t len_fmt = strlen(format_str);
    // memcpy(s->info, format_str, len_fmt + 1);
    // ((char*)(s->info))[len_fmt] = '\0';
    if (type < 0) {
      type = FORMAT_SERI;
    }
  }
  s->type = (seri_type)type;
  return 0;
};

/*! @brief Initialize serialier.
  @param[in] type seri_type Type of serializer. If -1, the type will
  be inferred from the info.
  @param[in] info void * Information for the serializer.
  @returns seri_t* Address of serializer.
*/
static inline
seri_t * init_serializer(int type, const void *info) {
  seri_t *s = (seri_t*)malloc(sizeof(seri_t));
  if (s == NULL) {
    cislog_error("init_serializer: Failed to allocate serializer.");
    return NULL;
  }
  s[0] = empty_serializer();
  int flag = update_serializer(s, type, info);
  if (flag != 0) {
    cislog_error("init_serializer: Failed to create serializer.");
    free(s);
    s = NULL;
  }
  return s;
};


/*! @brief Free serializer.
  @param[in] s seri_t* Serializer that should be freed.
  @returns int -1 if there was an error, 0 otherwise.
*/
static inline
int free_serializer(seri_t *s) {
  if (s->info != NULL) {
    free(s->info);
    s->info = NULL;
  }
  return 0;
};


/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[out] args_used int Number of arguments formatted.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize(const seri_t s, char **buf, const size_t buf_siz,
	      const int allow_realloc, int *args_used, va_list ap) {
  seri_type t = s.type;
  int ret = -1;
  va_list ap2;
  if (allow_realloc) {
    va_copy(ap2, ap);
  }
  if (t == DIRECT_SERI)
    ret = serialize_direct(s, *buf, buf_siz, args_used, ap);
  else if (t == FORMAT_SERI)
    ret = serialize_format(s, *buf, buf_siz, args_used, ap);
  else if (t == ASCII_TABLE_SERI)
    ret = serialize_ascii_table(s, *buf, buf_siz, args_used, ap);
  else if (t == ASCII_TABLE_ARRAY_SERI)
    ret = serialize_ascii_table_array(s, *buf, buf_siz, args_used, ap);
  else if (t == PLY_SERI)
    ret = serialize_ply(s, *buf, buf_siz, args_used, ap);
  else if (t == OBJ_SERI)
    ret = serialize_obj(s, *buf, buf_siz, args_used, ap);
  else {
    cislog_error("serialize: Unsupported seri_type %d", t);
  }
  if (ret > (int)buf_siz) {
    if (allow_realloc) {
      *buf = (char*)realloc(*buf, ret+1); 
      if (*buf == NULL) {
	cislog_error("serialize: Failed to realloc buffer.");
	ret = -1;
      } else {
	ret = serialize(s, buf, ret+1, 1, args_used, ap2);
      }
    } else {
      cislog_error("serialize: encoded message too large for the buffer. (buf_siz=%d, len=%d)",
		   buf_siz, ret);
      ret = -1;
    }
  }
  if (allow_realloc) {
    va_end(ap2);
  }
  return ret;
}

/*!
  @brief Deserialize message to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize(const seri_t s, const char *buf, const size_t buf_siz, va_list ap) {
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
  else if (t == PLY_SERI)
    ret = deserialize_ply(s, buf, buf_siz, ap);
  else if (t == OBJ_SERI)
    ret = deserialize_obj(s, buf, buf_siz, ap);
  else {
    cislog_error("deserialize: Unsupported seri_type %d", t);
  }
  return ret;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*CISSERIALIZE_H_*/
