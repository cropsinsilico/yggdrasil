#ifndef YGGSERIALIZE_H_
#define YGGSERIALIZE_H_

#include "../tools.h"
/*
#include "SerializeBase.h"
#include "FormatSerialize.h"
#include "AsciiTableSerialize.h"
#include "PlySerialize.h"
#include "ObjSerialize.h"
*/
#include "../metaschema/datatypes/datatypes.h"


#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif


/*!
  @brief Serializer structure.
*/
typedef struct seri_t {
  char type[COMMBUFFSIZ]; //!< Type name
  void *info; //!< JSON type
} seri_t;


/*!
  @brief Create an empty serializer structure.
  @returns seri_t Empty serializer.
 */
static inline
seri_t empty_serializer() {
  seri_t s;
  s.type[0] = '\0';
  s.info = NULL;
  return s;
};


/*! @brief Free serializer.
  @param[in] s seri_t* Serializer that should be freed.
  @returns int -1 if there was an error, 0 otherwise.
*/
static inline
int free_serializer(seri_t *s) {
  free_type_from_void(s->type, s->info);
  s->type[0] = '\0';
  s->info = NULL;
  return 0;
};


/*!
  @brief Update serializer with precision from provided information.
  @param[in] s seri_t * Address of serializer that should be updated. If NULL,
  one is created.
  @param[in] type char* Type that should be updated for the serializer.
  @param[in] info void * Information about serializer type. Assumes that any necessary
  copy has taken place and mearly assigns the pointer.
  @returns int -1 if there is an error, 0 otherwise.
*/
static inline
int update_precision(seri_t *s, const char* type, void *info) {
  if (s == NULL) {
    ygglog_error("update_precision: Pointer to serializer is NULL.");
    return -1;
  }
  if (strcmp(type, "scalar") == 0) {
    MetaschemaType* new_info = type_from_void(type, info);
    if (new_info == NULL) {
      ygglog_error("update_precision: Error getting type class.");
      return -1;
    }
    const char *subtype = get_type_subtype(new_info);
    printf("subtype = %s\n", subtype);
    if (strcmp(subtype, "") == 0) {
      ygglog_error("update_precision: Error getting subtype.");
      return -1;
    }
    if ((strcmp(subtype, "bytes") != 0) && (strcmp(subtype, "unicode") != 0)) {
      return 0;
    }
    const size_t new_prec = get_type_precision(new_info);
    if (new_prec == 0) {
      ygglog_error("update_precision: Error getting new precision.");
      return -1;
    }
    return update_precision_from_void(s->type, s->info, new_prec);
  }
  return 0;
};

/*!
  @brief Update serializer with provided information.
  @param[in] s seri_t * Address of serializer that should be updated. If NULL,
  one is created.
  @param[in] type char* Type that should be updated for the serializer.
  @param[in] info void * Information about serializer type. Assumes that any necessary
  copy has taken place and mearly assigns the pointer.
  @returns int -1 if there is an error, 0 otherwise.
*/
static inline
int update_serializer(seri_t *s, const char* type, void *info) {
  if (s == NULL) {
    ygglog_error("update_serializer: Pointer to serializer is NULL.");
    return -1;
  }
  // Free before transfering information
  free_serializer(s);
  if ((strlen(type) == 0) && (info != NULL)) {
    MetaschemaType* new_info = type_from_void(type, info);
    if (new_info == NULL) {
      ygglog_error("update_serializer: Error getting type.");
      return -1;
    }
    const char* new_type = get_type_name(new_info);
    strncpy(s->type, new_type, COMMBUFFSIZ);
    s->info = new_info;
  } else {
    strncpy(s->type, type, COMMBUFFSIZ);
    s->info = info;
  }
  return 0;
};


/*! @brief Initialize serialier.
  @param[in] type char* Type that should be updated for the serializer.
  @param[in] info void * Information for the serializer.
  @returns seri_t* Address of serializer.
*/
static inline
seri_t * init_serializer(const char* type, void *info) {
  seri_t *s = (seri_t*)malloc(sizeof(seri_t));
  if (s == NULL) {
    ygglog_error("init_serializer: Failed to allocate serializer.");
    return NULL;
  }
  s[0] = empty_serializer();
  int flag = update_serializer(s, type, info);
  if (flag != 0) {
    ygglog_error("init_serializer: Failed to create serializer.");
    free(s);
    s = NULL;
  }
  return s;
};


/*!
  @brief Serialize arguments to create a message.
  @param[in] s seri_t Structure sepcifying how to serialize arguments.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[in, out] nargs int Number of arguments remaining in argument list.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
 */
static inline
int serialize(const seri_t s, char **buf, size_t *buf_siz,
	      const int allow_realloc, size_t *nargs, va_list_t ap) {
  if (s.info == NULL) {
    ygglog_error("serialize: Serializer type not initialized.");
    return -1;
  }
  return serialize_from_void(s.type, s.info, buf, buf_siz,
			     allow_realloc, nargs, ap); 
};

/*!
  @brief Deserialize message to populate arguments.
  @param[in] s seri_t Structure sepcifying how to deserialize message.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] allow_realloc int If 1, variables being filled are assumed to be
  pointers to pointers for heap memory. If 0, variables are assumed to be pointers
  to stack memory. If allow_realloc is set to 1, but stack variables are passed,
  a segfault can occur.
  @param[in, out] nargs int Number of arguments remaining in argument list.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
 */
static inline
int deserialize(const seri_t s, const char *buf, const size_t buf_siz,
		const int allow_realloc, size_t *nargs, va_list_t ap) {
  if (s.info == NULL) {
    ygglog_error("deserialize: Serializer type not initialized.");
    return -1;
  }
  return deserialize_from_void(s.type, s.info, buf, buf_siz,
			       allow_realloc, nargs, ap);
};


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGSERIALIZE_H_*/
