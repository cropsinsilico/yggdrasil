#ifndef DATATYPES_H_
#define DATATYPES_H_

#include <stdbool.h>

#include "../tools.h"
#include "PlyDict.h"
#include "ObjDict.h"

#define MSG_HEAD_SEP "YGG_MSG_HEAD"
#define COMMBUFFSIZ 2000
#define FMT_LEN 100


#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

static char prefix_char = '#';


/*! @brief C-friendly definition of MetaschemaType. */
typedef struct dtype_t {
  char type[COMMBUFFSIZ]; //!< Type name
  bool use_generic; //!< Flag for empty dtypes to specify generic in/out
  void *obj; //!< MetaschemaType Pointer
} dtype_t;

/*! @brief C-friendly defintion of YggGeneric. */
typedef struct generic_t {
  char prefix; //!< Prefix character for limited verification.
  void *obj; //!< Pointer to YggGeneric class.
} generic_t;

/*! @brief C-friendly definition of vector object. */
typedef generic_t json_array_t;

/*! @brief C-friendly definition of map object. */
typedef generic_t json_object_t;

/*! @brief C-friendly definition of schema object. */
typedef generic_t schema_t;

/*! @brief C-friendly defintion of Python class object. */
typedef python_t python_class_t;

/*! @brief C-friendly defintion of Python function object. */
typedef python_t python_function_t;

/*! @brief C-friendly defintion of Python instance object. */
typedef generic_t python_instance_t;

/*! @brief Macro wrapping call to PyObject_CallFunction. */
#define call_python(x, format, ...) PyObject_CallFunction(x.obj, format, __VA_ARGS__)

/*! @brief Aliases to allow differentiation in parsing model definition. */
typedef char* unicode_t;
typedef char* string_t;
typedef char* bytes_t;
  
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
  dtype_t* dtype; //!< Type structure.
} comm_head_t;


/*!
  @brief C wrapper for the C++ type_from_doc function.
  @param type_doc void* Pointer to const rapidjson::Value type doc.
  @returns void* Pointer to MetaschemaType class.
 */
void* type_from_doc_c(const void* type_doc, const bool use_generic);


/*!
  @brief C wrapper for the C++ type_from_pyobj function.
  @param type_doc void* Pointer to const rapidjson::Value type doc.
  @returns void* Pointer to MetaschemaType class.
 */
void* type_from_pyobj_c(PyObject* pyobj, const bool use_generic);


/*!
  @brief Initialize an empty generic object.
  @returns generic_t New generic object structure.
 */
generic_t init_generic();


/*!
  @brief Determine if the provided character matches the required generic prefix char.
  @param[in] x char Character to check.
  @returns int 1 if the character is the correct prefix, 0 otherwise.
 */
int is_generic_flag(char x);


/*!
  @brief Determine if a generic structure is initialized.
  @param[in] x generic_t Generic structure to test.
  @returns int 1 if the structure is initialized, 0 otherwise.
 */
int is_generic_init(generic_t x);


/*!
  @brief Create a generic object from the provided information.
  @param[in] type_class dtype_t* Type structure/class.
  @param[in] data void* Pointer to data.
  @param[in] nbytes size_t Size of data.
  @returns generic_t Pointer to new generic object structure.
 */
generic_t create_generic(dtype_t* type_class, void* data, size_t nbytes);

  
/*!
  @brief Destroy a generic object.
  @param[in] x generic_t* Pointer to generic object structure to destory.
  @returns int -1 if unsuccessful, 0 otherwise.
 */
int destroy_generic(generic_t* x);


/*!
  @brief Copy data from one generic object to the other.
  @param[in] src generic_t Generic structure that data should be copied from.
  @returns generic_t Copied structure.
 */
generic_t copy_generic(generic_t src);


/*!
  @brief Display information about the generic type.
  @param[in] x generic_t* Wrapper for generic object.
 */
void display_generic(generic_t x);

  
/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list.
  @param[in] nargs size_t Number of argument present in ap.
  @param[in] ap va_list_t Variable argument list.
  @returns generic_t Generic structure if one is present.
 */
generic_t get_generic_va(size_t nargs, va_list_t ap);


/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list.
  @param[in] nargs size_t Number of argument present in ap.
  @param[in] ap va_list_t Variable argument list.
  @returns generic_t* Generic structure if one is present, NULL otherwise.
 */
generic_t* get_generic_va_ptr(size_t nargs, va_list_t ap);


/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list by removing it.
  @param[in] nargs size_t* Pointer to number of arguments present in ap
  that will be decremented by 1.
  @param[in] ap va_list_t* Pointer to variable argument list.
  @returns generic_t Generic structure if one is present.
 */
generic_t pop_generic_va(size_t* nargs, va_list_t* ap);


/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list by removing it.
  @param[in] nargs size_t* Pointer to number of arguments present in ap
  that will be decremented by 1.
  @param[in] ap va_list_t* Pointer to variable argument list.
  @returns generic_t* Generic structure if one is present, NULL otherwise.
 */
generic_t* pop_generic_va_ptr(size_t* nargs, va_list_t* ap);


/*!
  @brief Destroy a structure containing a Python object.
  @param[in] x python_t* Pointer to Python object structure that should be freed.
*/
void destroy_python(python_t *x);


/*!
  @brief Copy a Python object structure (NOTE: this dosn't copy the underlying Python object but does increment the reference count).
  @param[in] x python_t Structure containing Python object to copy.
  @returns python_t Copy of x.
 */
python_t copy_python(python_t x);


/*!
  @brief Display a Python object structure.
  @param[in] x python_t Structure containing Python object to display.
 */
void display_python(python_t x);

  
/*!
  @brief Destroy a structure containing a Python function object.
  @param[in] x python_function_t* Pointer to Python function structure that should be freed.
*/
void destroy_python_function(python_function_t *x);


/*!
  @brief Determine if a datatype is empty.
  @param[in] dtype dtype_t* Type structure to test.
  @returns int 1 if dtype is empty, 0 otherwise.
 */
int is_empty_dtype(const dtype_t* dtype);

  
/*!
  @brief Get the name of the type from the class.
  @param[in] type_class dtype_t* Type structure/class.
  @returns const char* Type name.
*/
const char* dtype_name(const dtype_t* type_class);


/*!
  @brief Get the subtype of the type.
  @param[in] type_class dtype_t* Type structure/class.
  @returns const char* The subtype of the class, "" if there is an error.
*/
const char* dtype_subtype(const dtype_t* type_class);


/*!
  @brief Get the precision of the type.
  @param[in] type_class dtype_t* Type structure/class.
  @returns const size_t The precision of the class, 0 if there is an error.
*/
const size_t dtype_precision(const dtype_t* type_class);

/*!
  @brief Initialize a datatype structure including setting the type string.
  @param[in] dtype dtype_t* Type structure/class.
  @returns dtype_t* Initialized type structure/class.
*/
dtype_t* complete_dtype(dtype_t *dtype, const bool use_generic);
  

/*!
  @brief Construct and empty type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_empty(const bool use_generic);


/*!
  @brief Create a datatype based on a JSON document.
  @param type_doc void* Pointer to const rapidjson::Value type doc.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_doc(void* type_doc, const bool use_generic);


/*!
  @brief Create a datatype based on a Python dictionary.
  @param[in] pyobj PyObject* Python dictionary.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_python(PyObject* pyobj, const bool use_generic);


/*!
  @brief Construct a Direct type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_direct(const bool use_generic);


  
/*!
  @brief Construct a type object for one of the default JSON types.
  @param[in] type char* Name of the type.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_default(const char* type,
			      const bool use_generic);


/*!
  @brief Construct a Scalar type object.
  @param[in] subtype char* Name of the scalar subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the scalar in bits.
  @param[in] units char* Units for scalar. (e.g. "cm", "g", "" for unitless)
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_scalar(const char* subtype, const size_t precision,
			     const char* units, const bool use_generic);


/*!
  @brief Construct a 1D array type object.
  @param[in] subtype char* Name of the array subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the array in bits.
  @param[in] length size_t Number of elements in the array.
  @param[in] units char* Units for array elements. (e.g. "cm", "g", "" for unitless)
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_1darray(const char* subtype, const size_t precision,
			      const size_t length, const char* units,
			      const bool use_generic);


/*!
  @brief Construct a ND array type object.
  @param[in] subtype char* Name of the array subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the array in bits.
  @param[in] ndim size_t Number of dimensions in the array (and therefore also the
  number of elements in shape).
  @param[in] shape size_t* Pointer to array where each element is the size of the
  array in that dimension.
  @param[in] units char* Units for array elements. (e.g. "cm", "g", "" for unitless)
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_ndarray(const char* subtype, const size_t precision,
			      const size_t ndim, const size_t* shape,
			      const char* units, const bool use_generic);

  
/*!
  @brief Construct a ND array type object.
  @param[in] subtype char* Name of the array subtype (e.g. int, uint, float, bytes).
  @param[in] precision size_t Precision of the array in bits.
  @param[in] ndim size_t Number of dimensions in the array (and therefore also the
  number of elements in shape).
  @param[in] shape[] size_t Array where each element is the size of the
  array in that dimension.
  @param[in] units char* Units for array elements. (e.g. "cm", "g", "" for unitless)
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_ndarray_arr(const char* subtype, const size_t precision,
				  const size_t ndim, const size_t shape[],
				  const char* units, const bool use_generic);

  
/*!
  @brief Construct a JSON array type object.
  @param[in] nitems size_t Number of types in items.
  @param[in] items dtype_t** Pointer to array of types describing the array
  elements.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_json_array(const size_t nitems, dtype_t** items,
				 const bool use_generic);


/*!
  @brief Construct a JSON object type object.
  @param[in] nitems size_t Number of keys/types in keys and values.
  @param[in] keys char** Pointer to array of keys for each type.
  @param[in] values dtype_t** Pointer to array of types describing the values
  for each key.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_json_object(const size_t nitems, char** keys,
				  dtype_t** values, const bool use_generic);

/*!
  @brief Construct a Ply type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_ply(const bool use_generic);


/*!
  @brief Construct a Obj type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_obj(const bool use_generic);


/*!
  @brief Construct an AsciiTable type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_ascii_table(const char *format_str, const int as_array,
				  const bool use_generic);


/*!
  @brief Construct a type object based on the provided format string.
  @param[in] format_str const char* C-style format string that will be used to determine
  the type of elements in arrays that will be serialized/deserialized using
  the resulting type.
  @param[in] as_array int If 1, the types will be arrays. Otherwise they will be
  scalars.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_format(const char *format_str, const int as_array,
			     const bool use_generic);

  
/*!
  @brief Construct a type object for Python objects.
  @param[in] type char* Type string.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_pyobj(const char* type, const bool use_generic);
  

/*!
  @brief Construct a type object for Python object instances.
  @param[in] class_name char* Python class name.
  @param[in] args_dtype dtype_t* Datatype describing the arguments
  creating the instance.
  @param[in] kwargs_dtype dtype_t* Datatype describing the keyword 
  arguments creating the instance.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_pyinst(const char* class_name,
			     const dtype_t* args_dtype,
			     const dtype_t* kwargs_dtype,
			     const bool use_generic);

  
/*!
  @brief Construct a type object for a schema.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_schema(const bool use_generic);


/*!
  @brief Construct a type object for receiving any type.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be YggGeneric classes.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_any(const bool use_generic);


/*!
  @brief Wrapper for freeing MetaschemaType class wrapper struct.
  @param[in] dtype dtype_t** Wrapper struct for C++ Metaschema type class.
  @returns: int 0 if free was successfull, -1 if there was an error.
*/
int destroy_dtype(dtype_t** dtype);

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
  // Parameters that will be removed
  out.serializer_type = -1;
  out.format_str[0] = '\0';
  out.as_array = 0;
  // Parameters used for type
  out.dtype = NULL;
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
  // Split buffer into head and body
  int ret;
  size_t sind, eind, sind_head, eind_head;
  sind = 0;
  eind = 0;
#ifdef _WIN32
  // Windows regex of newline is buggy
  UNUSED(buf_siz);
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
    ygglog_error("split_head_body: Could not find header in '%.1000s'", buf);
    return -1;
  } else if (ret == 0) {
    ygglog_debug("split_head_body: No header in '%.1000s...'", buf);
    sind_head = 0;
    eind_head = 0;
  } else {
    sind_head = sind + strlen(MSG_HEAD_SEP);
    eind_head = eind - strlen(MSG_HEAD_SEP);
  }
  headsiz[0] = (eind_head - sind_head);
  char* temp = (char*)realloc(*head, *headsiz + 1);
  if (temp == NULL) {
    ygglog_error("split_head_body: Failed to reallocate header.");
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
  @brief Get the ascii table data structure.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
  @returns: void* Cast pointer to ascii table.
*/
void* dtype_ascii_table(const dtype_t* dtype);


/*!
  @brief Get a copy of a type structure.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
  @returns: dtype_t* Type class.
*/
dtype_t* copy_dtype(const dtype_t* dtype);


/*!
  @brief Wrapper for updating a type object with information from another.
  @param[in] dtype1 dtype_t* Wrapper struct for C++ Metaschema type class that should be updated.
  @param[in] dtype2 dtype_t* Wrapper struct for C++ Metaschema type class that should be updated from.
  @returns: int 0 if successfull, -1 if there was an error.
*/
int update_dtype(dtype_t* dtype1, dtype_t* dtype2);


/*!
  @brief Wrapper for updatining a type object with information from
  the provided variable arguments if a generic structure is present.
  @param[in] dtype1 dtype_t* Wrapper struct for C++ Metaschema type class that should be updated.
  @param[in] nargs size_t Number of arguments in ap.
  @param[in] ap va_list_t Variable argument list.
  @returns: int 0 if successfull, -1 if there was an error.
 */
int update_dtype_from_generic_ap(dtype_t* dtype1, size_t nargs, va_list_t ap);

  
/*!
  @brief Wrapper for updating the precision of a bytes or unicode scalar type.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
  @param[in] new_precision size_t New precision.
  @returns: int 0 if free was successfull, -1 if there was an error.
*/
int update_precision_dtype(const dtype_t* dtype,
			   const size_t new_precision);

/*!
  @brief Wrapper for deserializing from a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
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
int deserialize_dtype(const dtype_t *dtype, const char *buf, const size_t buf_siz,
		      const int allow_realloc, size_t *nargs, va_list_t ap);


/*!
  @brief Wrapper for serializing from a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[in, out] nargs int Number of arguments remaining in argument list.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
*/
int serialize_dtype(const dtype_t *dtype, char **buf, size_t *buf_siz,
		    const int allow_realloc, size_t *nargs, va_list_t ap);


/*!
  @brief Wrapper for displaying a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
  @param[in] indent char* Indentation to add to display output.
*/
  void display_dtype(const dtype_t *dtype, const char* indent);


/*!
  @brief Wrapper for determining how many arguments a data type expects.
  @param[in] dtype dtype_t* Wrapper struct for C++ Metaschema type class.
*/
size_t nargs_exp_dtype(const dtype_t *dtype);


#define free_generic destroy_generic
#define init_json_object init_generic
#define init_json_array init_generic
#define init_schema init_generic
#define free_json_object free_generic
#define free_json_array free_generic
#define free_schema free_generic
#define copy_json_object copy_generic
#define copy_json_array copy_generic
#define copy_schema copy_generic
#define display_json_object display_generic
#define display_json_array display_generic
#define display_schema display_generic

  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*DATATYPES_H_*/
