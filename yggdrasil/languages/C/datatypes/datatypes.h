#ifndef DATATYPES_H_
#define DATATYPES_H_

#include <stdbool.h>

#include "../tools.h"

#define MSG_HEAD_SEP "YGG_MSG_HEAD"
/*! @brief Size of COMM buffer. */
#define COMMBUFFSIZ 2000
#define FMT_LEN 100


#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

static char prefix_char = '#';
#ifdef _OPENMP
#pragma omp threadprivate(prefix_char)
#endif
  
/*! @brief Bit flags. */
#define HEAD_FLAG_VALID      0x00000001  //!< Set if the header is valid.
#define HEAD_FLAG_MULTIPART  0x00000002  //!< Set if the header is for a multipart message
#define HEAD_META_IN_DATA    0x00000004  //!< Set if the type is stored with the data during serialization
#define HEAD_AS_ARRAY        0x00000008  //!< Set if messages will be serialized arrays

/*! @brief C-friendly definition of rapidjson::Document. */
typedef struct dtype_t {
  void *schema; //!< Pointer to rapidjson::Value for validation.
  void *metadata; //!< Pointer ot rapidjson::Document containing additional metadata.
} dtype_t;

/*! @brief C-friendly wrapper for rapidjson::Document. */
typedef struct generic_t {
  char prefix; //!< Prefix character for limited verification.
  void *obj; //!< Pointer to rapidjson::Document class.
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
  size_t bodysiz; //!< Size of body.
  size_t bodybeg; //!< Start of body in header.
  int flags; //!< Bit flags encoding the status of the header.
  int nargs_populated; //!< Number of arguments populated during deserialization.
  //
  size_t size; //!< Size of incoming message.
  char address[COMMBUFFSIZ]; //!< Address that message will comm in on.
  char id[COMMBUFFSIZ]; //!< Unique ID associated with this message.
  char response_address[COMMBUFFSIZ]; //!< Response address.
  char request_id[COMMBUFFSIZ]; //!< Request id.
  char zmq_reply[COMMBUFFSIZ]; //!< Reply address for ZMQ sockets.
  char zmq_reply_worker[COMMBUFFSIZ]; //!< Reply address for worker socket.
  char model[COMMBUFFSIZ]; //!< Name of model that sent the header.
  //
  void* dtype; //!< JSON schema for validating received data in rapidjson::Document.
  void* metadata; //!< Additional user defined options in rapidjson::Value.
} comm_head_t;


/*! @brief Obj structure. */
typedef struct obj_t {
  int nvert; //!< Number of vertices.
  int ntexc; //!< Number of texture coordinates.
  int nnorm; //!< Number of normals.
  int nparam; //!< Number of params.
  int npoint; //!< Number of points.
  int nline; //!< Number of lines.
  int nface; //!< Number of faces.
  int ncurve; //!< Number of curves.
  int ncurve2; //!< Number of curv2.
  int nsurf; //!< Number of surfaces.
  void* obj; //!< Pointer to rapidjson::ObjWavefront instance.
} obj_t;

/*! @brief Ply structure. */
typedef struct ply_t {
  int nvert; //!< Number of vertices.
  int nface; //!< Number of faces.
  int nedge; //!< Number of edges.
  void* obj; //!< Pointer to rapidjson::Ply instance.
} ply_t;
  
/*!
  @brief C wrapper for the C++ type_from_doc function.
  @param type_doc void* Pointer to const rapidjson::Value type doc.
  @returns void* Pointer to rapidjson::Document.
 */
void* type_from_doc_c(const void* type_doc);


/*!
  @brief C wrapper for the C++ type_from_pyobj function.
  @param pyobj void* Pointer to const rapidjson::Value type doc.
  @returns void* Pointer to rapidjson::Document.
 */
void* type_from_pyobj_c(PyObject* pyobj);


/*!
  @brief Determine if a datatype was created from a format.
  @param[in] type_struct dtype_t* Datatype structure.
  @returns int 1 if the datatype was created from a format, 0 if it
  was not, -1 if there is an error.
 */
int is_dtype_format_array(dtype_t* type_struct);
  
/*!
  @brief Get the name of the type described by the datatype schema.
  @param[in] schema Datatype schema.
  @returns Name.
*/
const char* schema2name_c(void* schema);

/*!
  @brief Get the name of the type described by the datatype schema.
  @param[in] type_struct dtype_t* Datatype structure.
  @returns Name.
*/
const char* dtype2name(dtype_t* type_struct);
  
/*!
  @brief Initialize an empty generic object.
  @returns generic_t New generic object structure.
 */
generic_t init_generic();
  
/*!
  @brief Initialize an empty array of mixed types with generic wrappers.
  @returns generic_t New generic object structure containing an empty array.
*/
generic_t init_generic_array();

/*!
  @brief Initialize an empty map (JSON object) of mixed types with generic wrappers.
  @returns generic_t New generic object structure contaiing an empty map (JSON object).
 */
generic_t init_generic_map();

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
/* generic_t create_generic(dtype_t* type_class, void* data, size_t nbytes); */

  
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
/* generic_t get_generic_va(size_t nargs, va_list_t ap); */


/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list.
  @param[in] nargs size_t Number of argument present in ap.
  @param[in] ap va_list_t Variable argument list.
  @returns generic_t* Generic structure if one is present, NULL otherwise.
 */
/* generic_t* get_generic_va_ptr(size_t nargs, va_list_t ap); */


/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list by removing it.
  @param[in] nargs size_t* Pointer to number of arguments present in ap
  that will be decremented by 1.
  @param[in] ap va_list_t* Pointer to variable argument list.
  @returns generic_t Generic structure if one is present.
 */
/* generic_t pop_generic_va(size_t* nargs, va_list_t* ap); */


/*!
  @brief Return the recovered generic structure if one is present in
  the variable argument list by removing it.
  @param[in] nargs size_t* Pointer to number of arguments present in ap
  that will be decremented by 1.
  @param[in] ap va_list_t* Pointer to variable argument list.
  @returns generic_t* Generic structure if one is present, NULL otherwise.
 */
/* generic_t* pop_generic_va_ptr(size_t* nargs, va_list_t* ap); */

/*!
  @brief Add an element to the end of an array of generic elements.
  @param[in] arr generic_t Array to add element to.
  @param[in] x generic_t Element to add.
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int add_generic_array(generic_t arr, generic_t x);


/*!
  @brief Set an element in the array at a given index to a new value.
  @param[in] arr generic_t Array to add element to.
  @param[in] i size_t Index where element should be added.
  @param[in] x generic_t Element to add.
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int set_generic_array(generic_t arr, size_t i, generic_t x);


/*!
  @brief Get an element from an array.
  @param[in] arr generic_t Array to get element from.
  @param[in] i size_t Index of element to get.
  @param[out] x generic_t* Pointer to address where element should be
  stored.
  @param[in] copy If 1, the element will be copied, otherwise a reference
    will be returned.
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int get_generic_array(generic_t arr, size_t i, generic_t *x, int copy);


/*!
  @brief Set an element in the object at for a given key to a new value.
  @param[in] arr generic_t Object to add element to.
  @param[in] k const char* Key where element should be added.
  @param[in] x generic_t Element to add.
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int set_generic_object(generic_t arr, const char* k, generic_t x);


/*!
  @brief Get an element from an object.
  @param[in] arr generic_t Object to get element from.
  @param[in] k const char* Key of element to return.
  @param[out] x generic_t* Pointer to address where element should be
  stored.
  @param[in] copy If 1, the element will be copied, otherwise a reference
    will be returned.
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int get_generic_object(generic_t arr, const char* k, generic_t *x, int copy);


#define set_generic_map set_generic_object
#define get_generic_map get_generic_object


/*!
  @brief Get the number of elements in an array object.
  @param[in] x generic_t Generic object that is presumed to contain an array.
  @returns size_t Number of elements in array.
 */
size_t generic_array_get_size(generic_t x);

/*!
  @brief Get an item from an array for types that don't require additional parameters.
  @param[in] x generic_t Generic object that is presumed to contain an array.
  @param[in] index size_t Index for value that should be returned.
  @param[in] type const char* Type of value expected.
  @returns void* Pointer to data for array item.
 */
void* generic_array_get_item(generic_t x, const size_t index,
			     const char *type);

/*!
  @brief Set an item in an array for types that don't require additional parameters.
  @param[in] x generic_t Generic object that is presumed to contain an array.
  @param[in] index size_t Index for value that should be set.
  @param[in] type const char* Type of value expected.
  @param[in] value Pointer to data for array item.
  @returns -1 if there is an error, 0 otherwise.
 */
int generic_array_set_item(generic_t x, const size_t index,
			   const char *type, void* value);
  
/*!
  @brief Get the number of elements in an map object.
  @param[in] x generic_t Generic object that is presumed to contain a map.
  @returns size_t Number of elements in map.
 */
size_t generic_map_get_size(generic_t x);
/*!
  @brief Determine if a map object has a certain key.
  @param[in] x generic_t Generic object that is presumed to contain a map.
  @param[in] key char* Key to check for.
  @returns int 1 if the key is present, 0 otherwise.
 */
int generic_map_has_key(generic_t x, char* key);
/*!
  @brief Get the keys in a map object.
  @param[in] x generic_t Generic object that is presumed to contain a map.
  @param[out] keys char*** Pointer to memory where array of keys should be stored.
  @returns size_t Number of keys in map.
 */
size_t generic_map_get_keys(generic_t x, char*** keys);

// TODO: Copy docs

void* generic_array_get_scalar(generic_t x, const size_t index,
			       const char * subtype, const size_t precision);
size_t generic_array_get_1darray(generic_t x, const size_t index,
				 const char* subtype, const size_t precision, void** data);
size_t generic_array_get_ndarray(generic_t x, const size_t index,
				 const char* subtype, const size_t precision,
				 void** data, size_t** shape);
int generic_array_set_scalar(generic_t x, const size_t index, void* value,
			     const char* subtype, const size_t precision,
			     const char *units);
int generic_array_set_1darray(generic_t x, const size_t index, void* value,
			      const char* subtype, const size_t precision,
			      const size_t length, const char *units);
int generic_array_set_ndarray(generic_t x, const size_t index, void* value,
			      const char* subtype, const size_t precision,
			      const size_t ndim, const size_t* shape,
			      const char *units);
void* generic_get_item(generic_t x, const char *type);
void* generic_map_get_item(generic_t x, const char* key, const char *type);
void* generic_map_get_scalar(generic_t x, const char* key,
			     const char * subtype, const size_t precision);
size_t generic_map_get_1darray(generic_t x, const char* key,
			       const char* subtype, const size_t precision,
			       void** data);
size_t generic_map_get_ndarray(generic_t x, const char* key,
			       const char* subtype, const size_t precision,
			       void** data, size_t** shape);
int generic_set_item(generic_t x, const char *type, void* value);
int generic_map_set_item(generic_t x, const char* key,
			 const char* type, void* value);
int generic_map_set_scalar(generic_t x, const char* key, void* value,
			   const char* subtype, const size_t precision,
			   const char *units);
int generic_map_set_1darray(generic_t x, const char* key, void* value,
			    const char* subtype, const size_t precision,
			    const size_t length, const char *units);
int generic_map_set_ndarray(generic_t x, const char* key, void* value,
			    const char* subtype, const size_t precision,
			    const size_t ndim, const size_t* shape,
			    const char *units);
  
#define NESTED_BASE_SET_(base, idx, idxType, name, ...)			\
  int generic_ ## base ## _set_ ## name(generic_t x, idxType idx, __VA_ARGS__)
#define NESTED_BASE_GET_(base, idx, idxType, name, type, ...)		\
  type generic_ ## base ## _get_ ## name(generic_t x, idxType idx, __VA_ARGS__)
#define NESTED_BASE_GET_NOARGS_(base, idx, idxType, name, type)	\
  type generic_ ## base ## _get_ ## name(generic_t x, idxType idx)
#define NESTED_SET_(name, ...)						\
  NESTED_BASE_SET_(array, index, const size_t, name, __VA_ARGS__);	\
  NESTED_BASE_SET_(map, key, const char*, name, __VA_ARGS__)
#define NESTED_GET_(name, type, ...)					\
  NESTED_BASE_GET_(array, index, const size_t, name, type, __VA_ARGS__); \
  NESTED_BASE_GET_(map, key, const char*, name, type, __VA_ARGS__)
#define NESTED_GET_NOARGS_(name, type)		\
  NESTED_BASE_GET_NOARGS_(array, index, const size_t, name, type);	\
  NESTED_BASE_GET_NOARGS_(map, key, const char*, name, type)
#define STD_JSON_NESTED_(name)						\
  generic_t generic_array_get_ ## name(generic_t x, const size_t index); \
  generic_t generic_map_get_ ## name(generic_t x, const char* key);	\
  int generic_array_set_ ## name(generic_t x, const size_t index, generic_t item); \
  int generic_map_set_ ## name(generic_t x, const char* key, generic_t item)
#define STD_JSON_(name, type)						\
  type generic_get_ ## name(generic_t x);				\
  int generic_set_ ## name(generic_t x, type value);			\
  NESTED_GET_NOARGS_(name, type);					\
  NESTED_SET_(name, type value)
#define STD_UNITS_(name, type)			\
  type generic_get_ ## name(generic_t x);				\
  int generic_set_ ## name(generic_t x, type value, const char* units); \
  NESTED_GET_NOARGS_(name, type);					\
  NESTED_SET_(name, type value, const char* units)
#define GEOMETRY_(name, type)			\
  STD_JSON_(name, type)
// TODO: Allow units when calling "get" methods?
#define ARRAY_(name, type)						\
  size_t generic_get_1darray_ ## name(generic_t x, type** data);	\
  size_t generic_get_ndarray_ ## name(generic_t x, type** data, size_t** shape); \
  NESTED_GET_(1darray_ ## name, size_t, type** data);			\
  NESTED_GET_(ndarray_ ## name, size_t, type** data, size_t** shape);	\
  NESTED_SET_(1darray_ ## name, type* value, const size_t length, const char* units); \
  NESTED_SET_(ndarray_ ## name, type* data, const size_t ndim, const size_t* shape, const char* units)
#define SCALAR_(name, type)		\
  STD_UNITS_(name, type);		\
  ARRAY_(name, type)
#define COMPLEX_(name, type)			\
  SCALAR_(name, type)
#define PYTHON_(name)				\
  STD_JSON_(name, python_t)
  
  STD_JSON_(bool, bool);
  STD_JSON_(integer, int);
  STD_JSON_(null, void*);
  STD_JSON_(number, double);
  STD_JSON_(string, const char*);
  STD_JSON_NESTED_(object);
  STD_JSON_NESTED_(array);
  STD_JSON_NESTED_(any);
  STD_JSON_NESTED_(schema);
  SCALAR_(int8, int8_t);
  SCALAR_(int16, int16_t);
  SCALAR_(int32, int32_t);
  SCALAR_(int64, int64_t);
  SCALAR_(uint8, uint8_t);
  SCALAR_(uint16, uint16_t);
  SCALAR_(uint32, uint32_t);
  SCALAR_(uint64, uint64_t);
  SCALAR_(float, float);
  SCALAR_(double, double);
  COMPLEX_(complex_float, complex_float_t);
  COMPLEX_(complex_double, complex_double_t);
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
  SCALAR_(long_double, long double);
  COMPLEX_(complex_long_double, complex_long_double_t);
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
  /* SCALAR_(bytes, const char*); */
  /* SCALAR_(unicode, const char*); */
  PYTHON_(python_class);
  PYTHON_(python_function);
  PYTHON_(python_instance);
  GEOMETRY_(obj, obj_t);
  GEOMETRY_(ply, ply_t);

#undef GEOMETRY_
#undef COMPLEX_
#undef PYTHON_
#undef SCALAR_
#undef ARRAY_
#undef STD_UNITS_
#undef STD_JSON_
#undef STD_JSON_NESTED_
#undef NESTED_SET_
#undef NESTED_GET_
#undef NESTED_GET_NOARGS_
#undef NESTED_BASE_SET_
#undef NESTED_BASE_GET_
#undef NESTED_BASE_GET_NOARGS_
#undef GENERIC_ERROR_
#undef GENERIC_SUCCESS_
  
  
/*!
>>>>>>> topic/timesync
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
  @brief Skip datatype arguments.
  @param[in] dtype dtype_t* Type structure to skip arguments for.
  @param[in, out] ap va_list_t Variable argument list.
  @param[in] pointers If true, the skipped arguments are assumed to be pointers.
  @returns int 1 if there are no errors, 0 otherwise.
 */
int skip_va_elements(const dtype_t* dtype, va_list_t *ap, bool pointers);


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
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Initialized type structure/class.
*/
dtype_t* complete_dtype(dtype_t *dtype, const bool use_generic);
  

/*!
  @brief Construct and empty type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_empty(const bool use_generic);


/*!
  @brief Create a datatype based on a JSON document.
  @param type_doc void* Pointer to const rapidjson::Value type doc.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_doc(void* type_doc, const bool use_generic);


/*!
  @brief Create a datatype based on a Python dictionary.
  @param[in] pyobj PyObject* Python dictionary.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_python(PyObject* pyobj, const bool use_generic);


/*!
  @brief Construct a Direct type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_direct(const bool use_generic);


  
/*!
  @brief Construct a type object for one of the default JSON types.
  @param[in] type char* Name of the type.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_ndarray_arr(const char* subtype, const size_t precision,
				  const size_t ndim, const int64_t shape[],
				  const char* units, const bool use_generic);

  
/*!
  @brief Construct a JSON array type object.
  @param[in] nitems size_t Number of types in items.
  @param[in] items dtype_t** Pointer to array of types describing the array
  elements.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_json_object(const size_t nitems, char** keys,
				  dtype_t** values, const bool use_generic);

/*!
  @brief Construct a Ply type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_ply(const bool use_generic);


/*!
  @brief Construct a Obj type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_obj(const bool use_generic);


/*!
  @brief Construct an AsciiTable type object.
  @param[in] format_str const char* C-style format string that will be used to determine
  the type of elements in arrays that will be serialized/deserialized using
  the resulting type.
  @param[in] as_array int If 1, the types will be arrays. Otherwise they will be
  scalars.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_format(const char *format_str, const int as_array,
			     const bool use_generic);

  
/*!
  @brief Construct a type object for Python objects.
  @param[in] type char* Type string.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
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
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_pyinst(const char* class_name,
			     const dtype_t* args_dtype,
			     const dtype_t* kwargs_dtype,
			     const bool use_generic);

  
/*!
  @brief Construct a type object for a schema.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_schema(const bool use_generic);


/*!
  @brief Construct a type object for receiving any type.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_any(const bool use_generic);


/*!
  @brief Wrapper for freeing rapidjson::Document class.
  @param[in] obj Pointer to rapidjson::Document.
  @returns int 0 if free was successfull, -1 if there was an error.
*/
int destroy_document(void** obj);
  
/*!
  @brief Wrapper for freeing rapidjson::Document class wrapper struct.
  @param[in] dtype dtype_t** Wrapper struct for C++ rapidjson::Document.
  @returns int 0 if free was successfull, -1 if there was an error.
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
  out.bodysiz = 0;
  out.bodybeg = 0;
  out.flags = HEAD_FLAG_VALID;
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
  out.model[0] = '\0';
  // Parameters used for type
  out.dtype = NULL;
  out.metadata = NULL;
  return out;
};

static inline
comm_head_t create_send_header(const char * data, const size_t len,
			       dtype_t *datatype) {
  /* printf("create_send_header: %d\n", len); */
  comm_head_t head = init_header(len, NULL, NULL);
  sprintf(head.id, "%d", rand());
  char *model_name = getenv("YGG_MODEL_NAME");
  if (model_name != NULL) {
    strcpy(head.model, model_name);
  }
  char *model_copy = getenv("YGG_MODEL_COPY");
  if (model_copy != NULL) {
    strcat(head.model, "_copy");
    strcat(head.model, model_copy);
  }
  head.flags = head.flags | HEAD_FLAG_VALID | HEAD_FLAG_MULTIPART;
  // Add datatype information to header
  head.dtype = datatype->schema;
  head.metadata = datatype->metadata;
  return head;
};

/*!
  @brief Destroy a header object.
  @param[in] x comm_head_t* Pointer to the header that should be destroyed.
  @returns int 0 if successful, -1 otherwise.
*/
static inline
int destroy_header(comm_head_t* x) {
  int ret = 0;
  if (x->metadata != NULL) {
    ret = destroy_document(&(x->metadata));
    x->metadata = NULL;
    x->dtype = NULL;
  }
  return ret;
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
  @param[in] head comm_head_t* Pointer to header to be formatted.
  @param[out] buf char ** Pointer to buffer where header should be written.
  @param[in] buf_siz size_t Size of buf.
  @param[in] max_header_size size_t Maximum size that header can occupy
  before the type should be moved to the data portion of the message.
  @param[in] no_type int If 1, type information will not be added to
  the header. If 0, it will be.
  @returns: int Size of header written.
*/
int format_comm_header(comm_head_t *head, char **buf, size_t buf_siz,
		       const size_t max_header_size, const int no_type);


/*!
  @brief Extract type from data and updated header.
  @param[in] buf char** Pointer to data containing type.
  @param[in] buf_siz size_t Size of buf.
  @param[in,out] head comm_head_t* Pointer to header structure that
  should be updated.
  @returns: int -1 if there is an error, size of adjusted data that
  dosn't include type otherwise.
 */
int parse_type_in_data(char **buf, const size_t buf_siz,
		       comm_head_t* head);

  
/*!
  @brief Extract header information from a string.
  @param[in] buf const char* Message that header should be extracted from.
  @param[in] buf_siz size_t Size of buf.
  @returns: comm_head_t Header information structure.
*/
comm_head_t parse_comm_header(const char *buf, const size_t buf_siz);


/*!
  @brief Get the ascii table data structure.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @returns: void* Cast pointer to ascii table.
*/
/* void* dtype_ascii_table(const dtype_t* dtype); */


/*!
  @brief Get a copy of a type structure.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @returns: dtype_t* Type class.
*/
dtype_t* copy_dtype(const dtype_t* dtype);


/*!
  @brief Wrapper for updating a type object with information from another.
  @param[in] dtype1 Wrapper struct for C++ rapidjson::Document that should be updated.
  @param[in] schema2 C++ rapidjson::Document that should be updated from.
  @returns: int 0 if successfull, -1 if there was an error.
*/
int update_dtype(dtype_t* dtype1, void* schema2);


/*!
  @brief Wrapper for updatining a type object with information from
  the provided variable arguments if a generic structure is present.
  @param[in] dtype1 dtype_t* Wrapper struct for C++ rapidjson::Document that should be updated.
  @param[in] ap va_list_t Variable argument list.
  @returns: int 0 if successfull, -1 if there was an error.
 */
int update_dtype_from_generic_ap(dtype_t* dtype1, va_list_t ap);

  
/*!
  @brief Wrapper for updating the precision of a bytes or unicode scalar type.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @param[in] new_precision size_t New precision.
  @returns: int 0 if free was successfull, -1 if there was an error.
*/
int update_precision_dtype(const dtype_t* dtype,
			   const size_t new_precision);

/*!
  @brief Wrapper for deserializing from a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] allow_realloc int If 1, variables being filled are assumed to be
  pointers to pointers for heap memory. If 0, variables are assumed to be pointers
  to stack memory. If allow_realloc is set to 1, but stack variables are passed,
  a segfault can occur.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
*/
int deserialize_dtype(const dtype_t *dtype, const char *buf, const size_t buf_siz,
		      const int allow_realloc, va_list_t ap);


/*!
  @brief Wrapper for serializing from a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @param[in] buf character pointer to pointer to memory where serialized message
  should be stored.
  @param[in] buf_siz size_t Size of memory allocated to buf.
  @param[in] allow_realloc int If 1, buf will be realloced if it is not big
  enough to hold the serialized emssage. If 0, an error will be returned.
  @param[in] ap va_list Arguments to be formatted.
  returns: int The length of the serialized message or -1 if there is an error.
*/
int serialize_dtype(const dtype_t *dtype, char **buf, size_t *buf_siz,
		    const int allow_realloc, va_list_t ap);


/*!
  @brief Wrapper for displaying a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @param[in] indent char* Indentation to add to display output.
*/
  void display_dtype(const dtype_t *dtype, const char* indent);


/*!
  @brief Wrapper for determining how many arguments a data type expects.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
*/
size_t nargs_exp_dtype(const dtype_t *dtype);


#define free_generic destroy_generic
#define init_json_object init_generic_map
#define init_json_array init_generic_array
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

// ObjWavefront wrapped methods

/*!
  @brief Initialize empty obj structure.
  @returns obj_t Obj structure.
*/
obj_t init_obj();

/*!
  @brief Set parameters from a rapidjson::ObjWavefront object.
  @param[in,out] x Structure to modify.
  @param[in] obj rapidjson::ObjWavefront object to copy.
  @param[in] copy If 1, the provided object will be copied, otherwise the
    pointer will be added to the structured directly and it will be freed on
    destruction.
*/
void set_obj(obj_t* x, void* obj, int copy);
  
/*!
  @brief Free obj structure.
  @param[in] p *obj_t Pointer to obj structure.
*/
void free_obj(obj_t *p);

/*!
  @brief Copy an obj structure.
  @param[in] src obj_t Obj structure that should be copied.
  @returns Copy of obj structure.
*/
obj_t copy_obj(obj_t src);

/*!
  @brief Display the information contained by an Obj struct.
  @param[in] p obj_t Obj structure.
  @param[in] indent const char* Indentation that should be added to each line.
 */
void display_obj_indent(obj_t p, const char* indent);

/*!
  @brief Display the information contained by an Obj struct.
  @param[in] p obj_t Obj structure.
 */
void display_obj(obj_t p);

  
// Ply wrapped methods

/*!
  @brief Initialize empty ply structure.
  @returns ply_t Ply structure.
 */
ply_t init_ply();

/*!
  @brief Set parameters from a rapidjson::Ply object.
  @param[in,out] x Structure to modify.
  @param[in] obj rapidjson::Ply object to copy.
  @param[in] copy If 1, the provided object will be copied, otherwise the
    pointer will be added to the structured directly and it will be freed on
    destruction.
*/
void set_ply(ply_t* x, void* obj, int copy);
  
/*!
  @brief Free ply structure.
  @param[in] p *ply_t Pointer to ply structure.
 */
void free_ply(ply_t *p);

/*!
  @brief Copy a ply structure.
  @param[in] src ply_t Ply structure that should be copied.
  @returns Copy of ply structure.
*/
ply_t copy_ply(ply_t src);

/*!
  @brief Display the information contained by a Ply struct.
  @param[in] p ply_t Ply structure.
  @param[in] indent const char* Indentation that should be added to each line.
 */
void display_ply_indent(ply_t p, const char* indent);

/*!
  @brief Display the information contained by a Ply struct.
  @param[in] p ply_t Ply structure.
 */
void display_ply(ply_t p);

  
#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*DATATYPES_H_*/
