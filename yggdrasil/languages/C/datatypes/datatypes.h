#ifndef DATATYPES_H_
#define DATATYPES_H_

#include <stdbool.h>

#include "../tools.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief C-friendly definition of rapidjson::Document. */
typedef struct dtype_t {
  void *metadata; //!< Pointer ot rapidjson::Document containing additional metadata.
} dtype_t;

/*! @brief C-friendly wrapper for rapidjson::Document. */
typedef struct generic_t {
  void *obj; //!< Pointer to rapidjson::Document.
} generic_t;

/*! @brief C-friendly wrapper for rapidjson::Value. */
typedef struct generic_ref_t {
  void *obj; //!< Pointer to rapidjson::Value.
  void *allocator; //!< Pointer to rapidjson Allocator used to allocated obj.
} generic_ref_t;

/*! @brief Structure used to wrap va_list and allow pointer passing.
@param va va_list Wrapped variable argument list.
*/
typedef struct va_list_t {
  void* va;
} va_list_t;

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
#ifdef YGGDRASIL_DISABLE_PYTHON_C_API
#define call_python(x, format, ...) NULL
#else // YGGDRASIL_DISABLE_PYTHON_C_API
#define call_python(x, format, ...) PyObject_CallFunction(x.obj, format, __VA_ARGS__)
#endif // YGGDRASIL_DISABLE_PYTHON_C_API

/*! @brief Aliases to allow differentiation in parsing model definition. */
typedef char* unicode_t;
typedef char* string_t;
typedef char* bytes_t;
  
/*! @brief Header information passed by comms for multipart messages. */
typedef struct comm_head_t {
  size_t* size_data; //!< Size of incoming message.
  size_t* size_buff; //!< Size of message buffer;
  size_t* size_curr; //!< Size of current message.
  size_t* size_head; //!< Size of header in incoming message.
  uint16_t* flags; //!< Bit flags encoding the status of the header.
  /* int nargs_populated; //!< Number of arguments populated during deserialization. */
  void* head; //!< C++ header structure.
  void* metadata; //!< Additional user defined options in rapidjson::Value.
  /* void* schema; //!< JSON schema for validating received data in rapidjson::Document. */
} comm_head_t;


/*! @brief Obj structure. */
typedef struct obj_t {
  void* obj; //!< Pointer to rapidjson::ObjWavefront instance.
} obj_t;

/*! @brief Ply structure. */
typedef struct ply_t {
  void* obj; //!< Pointer to rapidjson::Ply instance.
} ply_t;
  

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
  @brief Initialize an empty generic object with a null JSON document
  @returns generic_t New generic object structure.
 */
generic_t init_generic_null();
  
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
  @brief Copy data from one generic object into another.
  @param[in,out] dst Pointer to destination object.
  @param[in] src Source object.
  @returns int -1 if unsuccessful, 0 otherwise.
*/
int copy_generic_into(generic_t* dst, generic_t src);


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


#define NESTED_BASICS_(base, idx, idxType)	\
  void* generic_ ## base ## _get_item(generic_t x, idxType idx, const char *type); \
  int generic_ ## base ## _get_item_nbytes(generic_t x, idxType idx, const char *type); \
  void* generic_ ## base ## _get_scalar(generic_t x, idxType idx, const char *subtype, const size_t precision); \
  size_t generic_ ## base ## _get_1darray(generic_t x, idxType idx, const char *subtype, const size_t precision, void** data); \
  size_t generic_ ## base ## _get_ndarray(generic_t x, idxType idx, const char *subtype, const size_t precision, void** data, size_t** shape); \
  int generic_ ## base ## _set_item(generic_t x, idxType idx, const char *type, void* value); \
  int generic_ ## base ## _set_scalar(generic_t x, idxType idx,		\
				      void* value,			\
				      const char *subtype,		\
				      const size_t precision,		\
				      const char *units);		\
  int generic_ ## base ## _set_1darray(generic_t x, idxType idx,	\
				       void* value,			\
				       const char *subtype,		\
				       const size_t precision,		\
				       const size_t length,		\
				       const char *units);		\
  int generic_ ## base ## _set_ndarray(generic_t x, idxType idx,	\
				       void* value,			\
				       const char *subtype,		\
				       const size_t precision,		\
				       const size_t ndim,		\
				       const size_t* shape,		\
				       const char *units);
  
  NESTED_BASICS_(array, index, const size_t)
  NESTED_BASICS_(map, key, const char*)

#undef NESTED_BASICS_
    
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
int set_generic_array(generic_t arr, const size_t i, generic_t x);


/*!
  @brief Get an element from an array.
  @param[in] arr generic_t Array to get element from.
  @param[in] i size_t Index of element to get.
  @param[out] x generic_t* Pointer to address where element should be
    stored.
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int get_generic_array(generic_t arr, const size_t i, generic_t *x);
int get_generic_array_ref(generic_t arr, const size_t i, generic_ref_t *x);


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
  @returns int Flag that is 1 if there is an error and 0 otherwise.
 */
int get_generic_object(generic_t arr, const char* k, generic_t *x);
int get_generic_object_ref(generic_t arr, const char* k, generic_ref_t *x);


#define set_generic_map set_generic_object
#define get_generic_map get_generic_object
#define get_generic_map_ref get_generic_object_ref


/*!
  @brief Get the number of elements in an array object.
  @param[in] x generic_t Generic object that is presumed to contain an array.
  @returns size_t Number of elements in array.
 */
size_t generic_array_get_size(generic_t x);

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

void* generic_ref_get_item(generic_ref_t x, const char *type);
void* generic_get_item(generic_t x, const char *type);
int generic_set_item(generic_t x, const char *type, void* value);
  
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
  type generic_ref_get_ ## name(generic_ref_t x);			\
  type generic_get_ ## name(generic_t x);				\
  int generic_set_ ## name(generic_t x, type value);			\
  NESTED_GET_NOARGS_(name, type);					\
  NESTED_SET_(name, type value)
#define STD_UNITS_(name, type)			\
  type generic_ref_get_ ## name(generic_ref_t x);			\
  type generic_get_ ## name(generic_t x);				\
  int generic_set_ ## name(generic_t x, type value, const char* units); \
  NESTED_GET_NOARGS_(name, type);					\
  NESTED_SET_(name, type value, const char* units)
#define GEOMETRY_(name, type)			\
  STD_JSON_(name, type)
// TODO: Allow units when calling "get" methods?
#define ARRAY_(name, type)						\
  size_t generic_ref_get_1darray_ ## name(generic_ref_t x, type** data); \
  size_t generic_get_1darray_ ## name(generic_t x, type** data);	\
  size_t generic_ref_get_ndarray_ ## name(generic_ref_t x, type** data, size_t** shape); \
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
  @param[in] set If true, the skipped arguments are assumed to be
    pointers for setting.
  @returns int 1 if there are no errors, 0 otherwise.
 */
int skip_va_elements(const dtype_t* dtype, va_list_t *ap, bool set);


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
  @brief Construct a type object from a JSON schema.
  @param[in] schema Serialized JSON schema.
  @param[in] use_generic If true, serialized/deserialized objects will
    be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
 */
dtype_t* create_dtype_from_schema(const char* schema,
				  const bool use_generic);


/*!
  @brief Construct and empty type object.
  @param[in] use_generic bool If true, serialized/deserialized
  objects will be expected to be generic_t instances.
  @returns dtype_t* Type structure/class.
*/
dtype_t* create_dtype_empty(const bool use_generic);


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
			     dtype_t* args_dtype,
			     dtype_t* kwargs_dtype,
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
  @returns comm_head_t Structure with provided information, char arrays
  correctly initialized to empty strings if NULLs provided.
 */
comm_head_t init_header();

  
/*!
  @brief Create a header for sending messages.
  @param[in] datatype Datatype for messages that will be sent.
  @returns initialized header.
*/
comm_head_t create_send_header(dtype_t *datatype, const char* msg, const size_t len);
			       

/*!
  @brief Create a header for receiving messages.
  @param[in] data Pointer to string containing serialized header.
  @param[in] len Length of buffer containing serialized message.
  @param[in] msg_len Length of message in buffer.
  @param[in] allow_realloc If true, data target can be reallocated.
  @param[in] temp If true, the header is temporary.
*/
comm_head_t create_recv_header(char** data, const size_t len,
			       size_t msg_len, int allow_realloc,
			       int temp);
			       

#define HEADER_GET_SET_METHOD_(type, method)			\
  int header_GetMeta ## method(comm_head_t head,		\
			       const char* name, type* x);	\
  int header_SetMeta ## method(comm_head_t* head,		\
			       const char* name, type x)
  HEADER_GET_SET_METHOD_(int, Int);
  HEADER_GET_SET_METHOD_(bool, Bool);
  HEADER_GET_SET_METHOD_(const char*, String);
#undef HEADER_GET_SET_METHOD_
int header_SetMetaID(comm_head_t* head, const char* name,
		     const char** id);
       
/*!
  @brief Destroy a header object.
  @param[in] x comm_head_t* Pointer to the header that should be destroyed.
  @returns int 0 if successful, -1 otherwise.
*/
int destroy_header(comm_head_t* x);

/*!
  @brief Set flags to mark header as invalid.
  @param[in] x Header to modify.
*/
void invalidate_header(comm_head_t* x);
  
/*!
  @brief Check if a header is valid.
  @param[in] head Header to check.
  @returns 1 if valid, 0 otherwise.
*/
int header_is_valid(const comm_head_t head);

/*!
  @brief Check if a header is for a multipart message.
  @param[in] head Header to check.
  @returns 1 if multipart, 0 otherwise.
*/
int header_is_multipart(const comm_head_t head);

/*!
  @brief Get schema from header.
  @param[in] head Header to get schema from.
  @returns Header schema.
*/
void* header_schema(comm_head_t head);
  
/*!
  @brief Format header to a string.
  @param[in] head Pointer to header to be formatted.
  @param[out] headbuf Pointer to buffer where header should be written.
  @param[in] buf Message being sent.
  @param[in] buf_siz Size of buf.
  @param[in] max_size Maximum size that header can occupy before the type
    should be moved to the data portion of the message.
  @param[in] no_type If 1, type information will not be added to the
    header. If 0, it will be.
  @returns: Size of header written.
*/
int format_comm_header(comm_head_t *head, char **headbuf,
		       const char* buf, size_t buf_siz,
		       const size_t max_size, const int no_type);


/*!
  @brief Finalize header from complete data.
  @param[in,out] head Header structure that should be finalized.
  @param[in,out] dtype Datatype to update if type information is contained
    in the data.
  @returns: int -1 if there is an error, 0 otherwise.
 */
int finalize_header_recv(comm_head_t head, dtype_t* dtype);
		       

  
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
int update_precision_dtype(dtype_t* dtype,
			   const size_t new_precision);

/*!
  @brief Wrapper for deserializing from a data type.
  @param[in] dtype dtype_t* Wrapper struct for C++ rapidjson::Document.
  @param[in] buf character pointer to serialized message.
  @param[in] buf_siz size_t Size of buf.
  @param[in] ap va_list Arguments to be parsed from message.
  returns: int The number of populated arguments. -1 indicates an error.
*/
int deserialize_dtype(const dtype_t *dtype, const char *buf,
		      const size_t buf_siz, va_list_t ap);


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
  @param[in] dtype Wrapper struct for C++ rapidjson::Document.
  @param[in] for_fortran_recv If 1, additional variables passed by the 
     Fortran interface during receive calls will be considered.
*/
size_t nargs_exp_dtype(const dtype_t *dtype, const int for_fortran_recv);


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

/*!
  @brief Get the number of elements of a certain type in the structure.
  @param[in] p obj_t ObjWavefront structure.
  @param[in] name Name of element type to count.
*/
int nelements_obj(obj_t p, const char* name);
  
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

/*!
  @brief Get the number of elements of a certain type in the structure.
  @param[in] p ply_t Ply structure.
  @param[in] name Name of element type to count.
*/
int nelements_ply(ply_t p, const char* name);
  
/*!
  @brief Initialize Python if it is not initialized.
  @returns int 0 if successful, other values indicate errors.
 */
int init_python_API();

/*!
  @brief Initialize a variable argument list from an existing va_list.
  @param[in] nargs Pointer to argument count.
  @param[in] allow_realloc If int, arguments in va will be reallocated
    as necessary to receiving message contents.
  @param[in] for_c If 1, the arguments are treated as coming from C with
    C++ classes wrapped in structures.
  @returns va_list_t New variable argument list structure.
 */
va_list_t init_va_list(size_t *nargs, int allow_realloc, int for_c);

/*! Initialize a variable argument list from an array of pointers.
  @param[in] nptrs Number of pointers.
  @param[in] ptrs Array of pointers.
  @param[in] allow_realloc If int, arguments in va will be reallocated
    as necessary to receiving message contents.
  @param[in] for_fortran If 1, it is assumed that the passed pointers are
    passed from the fortran interface.
  @returns va_list_t New variable argument list structure.
*/
va_list_t init_va_ptrs(const size_t nptrs, void** ptrs,
		       int allow_realloc, int for_fortran);

/*! Get pointer to va_list.
  @param[in] ap Variable argument list.
  @returns Pointer to variable argument list.
 */
va_list* get_va_list(va_list_t ap);
  

/*! Finalize a variable argument list.
  @param[in] ap va_list_t Variable argument list.
*/
void end_va_list(va_list_t *ap);

/*!
  @brief Clear argument list.
  @param[in, out] ap Variable argument list to clear.
*/
void clear_va_list(va_list_t *ap);

/*! Get the number of arguments remaining in a variable argument list.
  @param[in] ap Variable argument list.
  @returns Number of arguments remaining.
 */
size_t size_va_list(va_list_t va);

/*! Set the size of the variable argument list.
  @param[in] ap Variable argument list.
  @param[in] nargs Pointer to argument count.
 */
void set_va_list_size(va_list_t va, size_t* nargs);

/*! Copy a variable argument list.
  @param[in] ap va_list_t Variable argument list structure to copy.
  @returns va_list_t New variable argument list structure.
*/
va_list_t copy_va_list(va_list_t ap);
  
/*! @brief Method for skipping a number of bytes in the argument list.
  @param[in] ap va_list_t* Structure containing variable argument list.
  @param[in] nbytes size_t Number of bytes that should be skipped.
 */
void va_list_t_skip(va_list_t *ap, const size_t nbytes);

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*DATATYPES_H_*/
