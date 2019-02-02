#ifndef DATATYPES_H_
#define DATATYPES_H_

#include "../../tools.h"
#include "PlyDict.h"
#include "ObjDict.h"

#define MSG_HEAD_SEP "CIS_MSG_HEAD"
#define COMMBUFFSIZ 2000
#define FMT_LEN 100


#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif


/*! @brief C-friendly definition of MetaschemaType. */
typedef struct MetaschemaType MetaschemaType;


/*! @brief Header information passed by comms for multipart messages. */
typedef struct comm_head_t {
  int multipart; //!< 1 if message is multipart, 0 if it is not.
  size_t bodysiz; //!< Size of body.
  size_t bodybeg; //!< Start of body in header.
  int valid; //!< 1 if the header is valid, 0 otherwise.
  int nargs_populated; //!< Number of arguments populated during deserialization.
  //
  size_t size; //!< Size of incoming message.
  char address[COMMBUFFSIZ]; //!< Address that message will comm in on.
  char id[COMMBUFFSIZ]; //!< Unique ID associated with this message.
  char response_address[COMMBUFFSIZ]; //!< Response address.
  char request_id[COMMBUFFSIZ]; //!< Request id.
  char zmq_reply[COMMBUFFSIZ]; //!< Reply address for ZMQ sockets.
  char zmq_reply_worker[COMMBUFFSIZ]; //!< Reply address for worker socket.
  // These should be removed once JSON fully implemented
  int serializer_type; //!< Code indicating the type of serializer.
  char format_str[COMMBUFFSIZ]; //!< Format string for serializer.
  char field_names[COMMBUFFSIZ]; //!< String containing field names.
  char field_units[COMMBUFFSIZ]; //!< String containing field units.
  int as_array; //!< 1 if messages will be serialized arrays.
  //
  char type[COMMBUFFSIZ]; //!< Type name
  void *serializer_info; //!< JSON type
} comm_head_t;


/*!
  @brief Get the name of the type from the class.
  @param[in] type_class MetaschemaType* Type structure/class.
  @returns const char* Type name.
*/
const char* get_type_name(MetaschemaType* type_class);


/*!
  @brief Get the subtype of the type.
  @param[in] type_class MetaschemaType* Type structure/class.
  @returns const char* The subtype of the class, "" if there is an error.
*/
const char* get_type_subtype(MetaschemaType* type_class);


/*!
  @brief Get the precision of the type.
  @param[in] type_class MetaschemaType* Type structure/class.
  @returns const size_t The precision of the class, 0 if there is an error.
*/
const size_t get_type_precision(MetaschemaType* type_class);


/*!
  @brief Construct a Direct type object.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_direct_type();


/*!
  @brief Construct a Scalar type object.
  @param[in] subtype char* Name of the scalar subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the scalar in bits.
  @param[in] units char* Units for scalar. (e.g. "cm", "g", "" for unitless)
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_scalar_type(const char* subtype, const size_t precision,
				const char* units);


/*!
  @brief Construct a 1D array type object.
  @param[in] subtype char* Name of the array subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the array in bits.
  @param[in] length size_t Number of elements in the array.
  @param[in] units char* Units for array elements. (e.g. "cm", "g", "" for unitless)
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_1darray_type(const char* subtype, const size_t precision,
				 const size_t length, const char* units);


/*!
  @brief Construct a ND array type object.
  @param[in] subtype char* Name of the array subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the array in bits.
  @param[in] ndim size_t Number of dimensions in the array (and therefore also the
  number of elements in shape).
  @param[in] shape size_t* Pointer to array where each element is the size of the
  array in that dimension.
  @param[in] units char* Units for array elements. (e.g. "cm", "g", "" for unitless)
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_ndarray_type(const char* subtype, const size_t precision,
				 const size_t ndim, const size_t* shape,
				 const char* units);

/*!
  @brief Construct a JSON array type object.
  @param[in] nitems size_t Number of types in items.
  @param[in] items MetaschemaType** Pointer to array of types describing the array
  elements.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_json_array_type(const size_t nitems, MetaschemaType** items);


/*!
  @brief Construct a JSON object type object.
  @param[in] nitems size_t Number of keys/types in keys and values.
  @param[in] keys char** Pointer to array of keys for each type.
  @param[in] values MetaschemaType** Pointer to array of types describing the values
  for each key.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_json_object_type(const size_t nitems, const char** keys,
				     MetaschemaType** values);

/*!
  @brief Construct a Ply type object.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_ply_type();


/*!
  @brief Construct a Obj type object.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_obj_type();


/*!
  @brief Construct an AsciiTable type object.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_ascii_table_type(const char *format_str, const int as_array);


/*!
  @brief Construct a type object based on the provided format string.
  @param[in] format_str const char* C-style format string that will be used to determine
  the type of elements in arrays that will be serialized/deserialized using
  the resulting type.
  @param[in] as_array int If 1, the types will be arrays. Otherwise they will be
  scalars.
  @returns MetaschemaType* Type structure/class.
*/
MetaschemaType* get_format_type(const char *format_str, const int as_array);


/*!
  @brief Construct a type object based on the type name and a pointer cast to void*.
  @param[in] type_name char* Name of the type represented.
  @param[in] type void* Pointer to location where type information is stored.
  @returns MetaschemaType* Type structure/class.
 */
MetaschemaType* type_from_void(const char *type_name, const void *type);


/*!
  @brief Initialize a header struct.
  @param[in] size size_t Size of message to be sent.
  @param[in] address char* Address that should be used for remainder of 
  message following this header if it is a multipart message.
  @param[in] id char* Message ID.
  @returns comm_head_t Structure with provided information, char arrays
  correctly initialized to empty strings if NULLs provided.
 */
static inline
comm_head_t init_header(const size_t size, const char *address, const char *id) {
  comm_head_t out;
  // Parameters set during read
  out.multipart = 0;
  out.bodysiz = 0;
  out.bodybeg = 0;
  out.valid = 1;
  out.nargs_populated = 0;
  // Parameters sent in header
  out.size = size;
  if (address == NULL)
    out.address[0] = '\0';
  else
    strncpy(out.address, address, COMMBUFFSIZ);
  if (id == NULL)
    out.id[0] = '\0';
  else
    strncpy(out.id, id, COMMBUFFSIZ);
  out.response_address[0] = '\0';
  out.request_id[0] = '\0';
  out.zmq_reply[0] = '\0';
  out.zmq_reply_worker[0] = '\0';
  /* if (response_address == NULL) */
  /*   out.response_address[0] = '\0'; */
  /* else */
  /*   strncpy(out.response_address, response_address, COMMBUFFSIZ); */
  // Parameters that will be removed
  out.serializer_type = -1;
  out.format_str[0] = '\0';
  out.as_array = 0;
  // Parameters used for type
  out.type[0] = '\0';
  out.serializer_info = NULL;
  return out;
};


/*!
  @brief Split header and body of message.
  @param[in] buf const char* Message that should be split.
  @param[in] buf_siz size_t Size of buf.
  @param[out] head const char** pointer to buffer where the extracted header
  should be stored.
  @param[out] headsiz size_t reference to memory where size of extracted header
  should be stored.
  @returns: int 0 if split is successful, -1 if there was an error.
*/
static inline
int split_head_body(const char *buf, const size_t buf_siz,
		    char **head, size_t *headsiz) {
  // size_t bodysiz = 0;
  // Split buffer into head and body
  int ret;
  size_t sind, eind, sind_head, eind_head, sind_body, eind_body;
  sind = 0;
  eind = 0;
#ifdef _WIN32
  // Windows regex of newline is buggy
  size_t sind1, eind1, sind2, eind2;
  char re_head_tag[COMMBUFFSIZ];
  sprintf(re_head_tag, "(%s)", MSG_HEAD_SEP);
  ret = find_match(re_head_tag, buf, &sind1, &eind1);
  if (ret > 0) {
    sind = sind1;
    ret = find_match(re_head_tag, buf + eind1, &sind2, &eind2);
    if (ret > 0)
      eind = eind1 + eind2;
  }
#else
  // Extract just header
  char re_head[COMMBUFFSIZ] = MSG_HEAD_SEP;
  strcat(re_head, "(.*)");
  strcat(re_head, MSG_HEAD_SEP);
  // strcat(re_head, ".*");
  ret = find_match(re_head, buf, &sind, &eind);
#endif
  if (ret < 0) {
    cislog_error("split_head_body: Could not find header in '%.1000s'", buf);
    return -1;
  } else if (ret == 0) {
    cislog_debug("split_head_body: No header in '%.1000s...'", buf);
    sind_head = 0;
    eind_head = 0;
    sind_body = 0;
    eind_body = buf_siz;
  } else {
    sind_head = sind + strlen(MSG_HEAD_SEP);
    eind_head = eind - strlen(MSG_HEAD_SEP);
    sind_body = eind;
    eind_body = buf_siz;
  }
  headsiz[0] = (eind_head - sind_head);
  // bodysiz = (eind_body - sind_body);
  char* temp = (char*)realloc(*head, *headsiz + 1);
  if (temp == NULL) {
    cislog_error("split_head_body: Failed to reallocate header.");
    return -1;
  }
  *head = temp;
  memcpy(*head, buf + sind_head, *headsiz);
  (*head)[*headsiz] = '\0';
  return 0;
};


/*!
  @brief Format header to a string.
  @param[in] head comm_head_t Header to be formatted.
  @param[out] buf char * Buffer where header should be written.
  @param[in] buf_siz size_t Size of buf.
  @returns: int Size of header written.
*/
int format_comm_header(const comm_head_t head, char *buf, const size_t buf_siz);


/*!
  @brief Extract header information from a string.
  @param[in] buf const char* Message that header should be extracted from.
  @param[in] buf_siz size_t Size of buf.
  @returns: comm_head_t Header information structure.
*/
comm_head_t parse_comm_header(const char *buf, const size_t buf_siz);


/*!
  @brief Get the ascii table data structure from void.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
  @returns: void* Cast pointer to ascii table.
*/
void* get_ascii_table_from_void(const char* name, const void* info);


/*!
  @brief Get the type name from pointer cast as void*.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
  @returns: const char * Name of type class.
*/
const char* get_type_name_from_void(const char* name, const void* info);


/*!
  @brief Get a copy of the type from pointer cast as void*.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
  @returns: MetaschemaType* Type class.
*/
MetaschemaType* copy_from_void(const char* name, const void* info);


/*!
  @brief Wrapper for updating the precision of a bytes or unicode scalar type.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
  @param[in] new_precision size_t New precision.
  @returns: int 0 if free was successfull, -1 if there was an error.
*/
int update_precision_from_void(const char* name, void* info,
			       const size_t new_precision);

/*!
  @brief Wrapper for freeing MetaschemaType class from pointer cast as void*
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
  @returns: int 0 if free was successfull, -1 if there was an error.
*/
int free_type_from_void(const char* name, void* info);


/*!
  @brief Wrapper for deserializing from a data type cast as void*.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
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
int deserialize_from_void(const char* name, const void* info,
			  const char *buf, const size_t buf_siz,
			  const int allow_realloc, size_t *nargs, va_list_t ap);


/*!
  @brief Wrapper for serializing from a data type cast as void*.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[in, out] nargs int Number of arguments remaining in argument list.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
*/
int serialize_from_void(const char* name, const void* info,
			char **buf, size_t *buf_siz,
			const int allow_realloc, size_t *nargs, va_list_t ap);


/*!
  @brief Wrapper for displaying a data type.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
*/
void display_from_void(const char* name, const void* info);


/*!
  @brief Wrapper for determining how many arguments a data type expects.
  @param[in] name char* Name of the type.
  @param[in] info void* Pointer to type class.
*/
size_t nargs_exp_from_void(const char* name, const void* info);



#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*DATATYPES_H_*/
