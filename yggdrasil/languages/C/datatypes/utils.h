#ifndef DATATYPES_UTILS_H_
#define DATATYPES_UTILS_H_

#include "../tools.h"

#include <stdexcept>
#include <iostream>
#include <iomanip>
#include <map>
#include <vector>
#include <functional>
#include <cstring>


enum { T_BOOLEAN, T_INTEGER, T_NULL, T_NUMBER, T_STRING, T_ARRAY, T_OBJECT,
       T_DIRECT, T_1DARRAY, T_NDARRAY, T_SCALAR, T_FLOAT, T_UINT, T_INT, T_COMPLEX,
       T_BYTES, T_UNICODE, T_PLY, T_OBJ, T_ASCII_TABLE,
       T_CLASS, T_FUNCTION, T_INSTANCE, T_SCHEMA, T_ANY };


/*!
  @brief Throw an error and long it.
  @param[in] fmt char* Format string.
  @param[in] ... Parameters that should be formated using the format string.
 */
static inline
void ygglog_throw_error(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  yggError_va(fmt, ap);
  va_end(ap);
  throw std::exception();
};

/*!
  @brief Count the number of times a regular expression is matched in a string.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @return size_t Number of matches found.
*/
static inline
size_t count_matches_raise(const char *regex_text, const char *to_match) {
  int out = count_matches(regex_text, to_match);
  if (out < 0) {
    ygglog_throw_error("count_matches_raise: Error in count_matches. regex = '%s', string = '%s'",
                       regex_text, to_match);
  }
  return (size_t)out;
};

/*!
  @brief Find first match to regex and any sub-matches.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @param[out] sind size_t ** indices of where matches begin.
  @param[out] eind size_t ** indices of where matches ends.
  @return size_t Number of matches/submatches found.
*/
size_t find_matches_raise(const char *regex_text, const char *to_match,
        size_t **sind, size_t **eind) {
  int out = find_matches(regex_text, to_match, sind, eind);
  if (out < 0) {
    ygglog_throw_error("find_matches_raise: Error in find_matches. regex = '%s', string = '%s'",
                       regex_text, to_match);
  }
  return (size_t)out;
};

/*!
  @brief Find first match to regex.
  @param[in] regex_text constant character pointer to string that should be
  compiled into a regex.
  @param[in] to_match constant character pointer to string that should be
  checked for matches.
  @param[out] sind size_t index where match begins.
  @param[out] eind size_t index where match ends.
  @return size_t Number of matches found. -1 is returned if the regex could not be
  compiled.
*/
size_t find_match_raise(const char *regex_text, const char *to_match,
            size_t *sind, size_t *eind) {
  int out = find_match(regex_text, to_match, sind, eind);
  if (out < 0) {
    ygglog_throw_error("find_match_raise: Error in find_match. regex = '%s', string = '%s'",
                       regex_text, to_match);
  }
  return (size_t)out;
};

/*!
  @brief String comparison structure.
 */
struct strcomp : public std::binary_function<const char*, const char*, bool> 
{
  /*!
    @brief Comparison operator.
    @param[in] a char const * First string for comparison.
    @param[in] b char const * Second string for comparison.
    @returns bool true if the strings are equivalent, false otherwise.
   */
  bool operator()(const char *a, const char *b) const
  {
    return std::strcmp(a, b) < 0;
  }
};

/*! @brief Global type map to be filled. */
static std::map<const char*, int, strcomp> global_type_map;

/*!
  @brief Return the global type map, populating it as necessary.
  @returns std::map<const char*, int, strcomp> mapping  from type name to code.
*/
std::map<const char*, int, strcomp> get_type_map() {
  if (global_type_map.empty()) {
    // Standard types
    global_type_map["boolean"] = T_BOOLEAN;
    global_type_map["integer"] = T_INTEGER;
    global_type_map["null"] = T_NULL;
    global_type_map["number"] = T_NUMBER;
    global_type_map["string"] = T_STRING;
    // Enhanced types
    global_type_map["array"] = T_ARRAY;
    global_type_map["object"] = T_OBJECT;
    // Non-standard types
    global_type_map["direct"] = T_DIRECT;
    global_type_map["1darray"] = T_1DARRAY;
    global_type_map["ndarray"] = T_NDARRAY;
    global_type_map["scalar"] = T_SCALAR;
    global_type_map["float"] = T_FLOAT;
    global_type_map["uint"] = T_UINT;
    global_type_map["int"] = T_INT;
    global_type_map["complex"] = T_COMPLEX;
    global_type_map["bytes"] = T_BYTES;
    global_type_map["unicode"] = T_UNICODE;
    global_type_map["ply"] = T_PLY;
    global_type_map["obj"] = T_OBJ;
    global_type_map["ascii_table"] = T_ASCII_TABLE;
    global_type_map["class"] = T_CLASS;
    global_type_map["function"] = T_FUNCTION;
    global_type_map["instance"] = T_INSTANCE;
    global_type_map["schema"] = T_SCHEMA;
    global_type_map["any"] = T_ANY;
  }
  return global_type_map;
};


// Forward declaration
class MetaschemaType;


/*!
  @brief Generic class.
  The YggGeneric provides a wrapper for any type.
 */
class YggGeneric {
private:
  MetaschemaType *type;
  void *data;
  size_t nbytes;
public:
  YggGeneric();
  /*!
    @brief Constructor.
    @param[in] in_type MetaschemaType* Pointer to type class describing data.
    @param[in] in_data void* Pointer to data.
    @param[in] in_nbytes size_t Number of bytes at the address provided
    by data. Defaults to 0 and will be set by type->nbytes().
   */
  YggGeneric(const MetaschemaType* in_type, void* in_data, size_t in_nbytes=0);
  /*!
    @brief Copy constructor.
    @param[in] other YggGeneric Instance of class to copy.
   */
  YggGeneric(const YggGeneric &other);
  /*!
    @brief Desctructor.
   */
  ~YggGeneric();
  /*!
    @brief Display the data.
   */
  void display(const char* indent="") const;
  /*!
    @brief Get a copy of the data.
    @returns void* Pointer to copy of data.
  */
  void* copy_data(void* orig_data=NULL) const;
  /*!
    @brief Free the memory used by the data.
   */
  void free_data();
  /*!
    @brief Free the memory used by the type.
   */
  void free_type();
  /*!
    @brief Get a copy.
    @returns YggGeneric* Copy of this class.
   */
  YggGeneric* copy() const;
  /*!
    @brief Set the data type.
    @param[in] new_type MetaschemaType* Pointer to new type.
   */
  void set_type(const MetaschemaType* new_type);
  /*!
    @brief Get the data type.
    @returns MetaschemaType* Pointer to data type.
   */
  MetaschemaType* get_type() const;
  /*!
    @brief Set the data size.
    @param[in] new_nbytes size_t New data size.
   */
  void set_nbytes(size_t new_nbytes);
  /*!
    @brief Get the data size.
    @returns size_t Number of bytes in the data object.
   */
  size_t get_nbytes() const;
  /*!
    @brief Get a pointer to the data size.
    @returns size_t* Pointer to number of bytes in the data object.
   */
  size_t* get_nbytes_pointer();
  /*!
    @brief Get the number of elements in the data.
    @returns size_t Number of elements in the data.
   */
  size_t get_nelements() const;
  /*!
    @brief Set data.
    @param[in] new_data void* New data.
   */
  void set_data(void *new_data);
  /*!
    @brief Extract data.
    @returns void* Pointer to data.
   */
  void* get_data() const;
  /*!
    @brief Get the data pointer.
    @returns void** Pointer to data object pointer.
   */
  void** get_data_pointer();
  /*!
    @brief Extract data and copy into the provided variable.
    @param[out] obj T* Pointer to existing variable where data should be copied.
    @param[in] nelements size_t Number of elements in the provided array.
    Defaults to 1 if not provided.
    @param[in] is_char bool If True, the input array is treated as a
    charater array and need only be larger than the size of the data.
    Defaults to false if not provided.
   */
  template <typename T>
  void get_data(T* obj, size_t nelements=1, bool is_char=false) const;
  /*!
    @brief Extract data and assign the value to the provided variable.
    @param[out] obj T Existing variable where data should be stored.
   */
  template <typename T>
  void get_data(T &obj) const;
  /*!
    @brief Extract data, realloc provided array, and copy data into it.
    @param[out] obj T** Pointer to existing array where data should be copied.
    @param[in, out] nelements size_t* Pointer to number of elements in
    the provided array. The number of elements in teh array after
    reallocation is stored at this address. Defaults to NULL if not
    provided.
   */
  template <typename T>
  void get_data_realloc(T** obj, size_t* nelements=NULL) const;
  /*!
    @brief Extract data and copy into the provided variable.
    @param[out] obj T* Pointer to existing variable where data should be copied.
    @param[in] nelements size_t Number of elements in the provided array.
    Defaults to 1 if not provided.
   */
  void get_data(char* obj, size_t nelements) const;
};


/*! @brief Vector of void pointers. */
typedef std::vector<void*> void_vector_t;

/*! @brief Map of void pointers. */
typedef std::map<const char*, void*, strcomp> void_map_t;

/*! @brief Vector of generic types. */
typedef std::vector<YggGeneric*> YggGenericVector;

/*! @brief Map of generic types. */
typedef std::map<std::string, YggGeneric*> YggGenericMap;
//typedef std::map<const char*, YggGeneric*, strcomp> YggGenericMap;


/*!
  @brief Initialize Python if it is not initialized.
  @param[in] error_prefix char* Prefix that should be added to error messages.
 */
void initialize_python(const char* error_prefix="") {
  int ret = init_python_API();
  if (ret == -1) {
    ygglog_throw_error("%sinitialize_python: Python not initialized.", error_prefix);
  } else if (ret != 0) {
    ygglog_throw_error("%sinitialize_python: Numpy not initialized.", error_prefix);
  }
};

/*!
  @brief Try to import a Python module, throw an error if it fails.
  @param[in] module_name const char* Name of the module to import (absolute path).
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @returns PyObject* Pointer to the Python module object.
 */
PyObject* import_python_module(const char* module_name,
			       const char* error_prefix="") {
  initialize_python(error_prefix);
  PyObject* out = PyImport_ImportModule(module_name);
  if (out == NULL) {
    ygglog_throw_error("%simport_python_module: Failed to import Python module '%s'.",
		       error_prefix, module_name);
  }
  return out;
};


/*!
  @brief Try to import a Python class, throw an error if it fails.
  @param[in] module_name const char* Name of the module to import (absolute path).
  @param[in] class_name const char* Name of the class to import from the specified module.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @returns PyObject* Pointer to the Python class object.
 */
PyObject* import_python_class(const char* module_name, const char* class_name,
			      const char* error_prefix="") {
  PyObject *py_module = import_python_module(module_name,
					     error_prefix);
  PyObject *out = PyObject_GetAttrString(py_module, class_name);
  Py_DECREF(py_module);
  if (out == NULL) {
    ygglog_throw_error("import_python_class: Failed to import Python class '%s'.", class_name);
  }
  return out;
};


/*!
  @brief Check that a Python object is the correct type, throw errors if it is not.
  @param[in] pyobj PyObject* Python object.
  @param[in] type_code int Type code.
  @param[in] prefix char* Prefix string that should be prepended to error messages. Defaults to "".
 */
void check_python_object(PyObject *pyobj, int type_code=-1,
			 const char* prefix="") {
  char type_name[100] = "";
  int result = 0;
  if (type_code < 0)
    return;
  switch (type_code) {
  case T_ARRAY: {
    result = PyList_Check(pyobj);
    strcat(type_name, "list");
    break;
  }
  case T_OBJECT: {
    result = PyDict_Check(pyobj);
    strcat(type_name, "dict");
    break;
  }
  case T_NUMBER:
  case T_FLOAT: {
    result = PyFloat_Check(pyobj);
    strcat(type_name, "float");
    break;
  }
  case T_INTEGER:
  case T_INT:
  case T_UINT: {
    result = PyLong_Check(pyobj);
    strcat(type_name, "long");
    break;
  }
  case T_BOOLEAN: {
    result = PyBool_Check(pyobj);
    strcat(type_name, "bool");
    break;
  }
  case T_COMPLEX: {
    result = PyComplex_Check(pyobj);
    strcat(type_name, "complex");
    break;
  }
  case T_STRING:
  case T_BYTES: {
    result = PyBytes_Check(pyobj);
    strcat(type_name, "bytes");
    break;
  }
  case T_UNICODE: {
    result = PyUnicode_Check(pyobj);
    strcat(type_name, "unicode");
    break;
  }
  default: {
    ygglog_throw_error("%scheck_python_object: Unsupported type code: %d", prefix, type_code);
  }
  }
  if (!(result)) {
    ygglog_throw_error("%scheck_python_object: Python object is not %s.", prefix, type_name);
  }
  if (PyErr_Occurred() != NULL) {
    ygglog_throw_error("%scheck_python_object: Python error.", prefix);
  }
};


/*!
  @brief Convert a Python object into the C representation.
  @param[in] pyobj PyObject* Python object.
  @param[in, out] dst void* Pointer to memory where C representation should be stored.
  @param[in] type_code int Code indicating type of data that should be in pyobj.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] precision size_t Size (in bits) of the C type. Defaults to 0.
 */
void convert_python2c(PyObject *pyobj, void *dst, int type_code,
		      const char* error_prefix="",
		      size_t precision=0) {
  if (type_code < 0)
    return;
  if (dst == NULL) {
    ygglog_throw_error("%sconvert_python2c: Destination is NULL.", error_prefix);
  }
  // check_python_object(pyobj, type_code, error_prefix);
  char type_name[100] = "";
  switch (type_code) {
  case T_ARRAY: {
  case T_OBJECT:
    PyObject **dst_ptr = (PyObject**)dst;
    dst_ptr[0] = pyobj;
    strcat(type_name, "list/dict");
    break;
  }
  case T_NUMBER:
  case T_FLOAT: {
    double dst_cast = PyFloat_AsDouble(pyobj);
    if ((precision == 0) || (sizeof(double) == precision/8)) {
      double *dst_ptr = (double*)dst;
      dst_ptr[0] = dst_cast;
    } else if (sizeof(float) == precision/8) {
      float *dst_ptr = (float*)dst;
      dst_ptr[0] = (float)dst_cast;
    } else if (sizeof(long double) == precision/8) {
      long double *dst_ptr = (long double*)dst;
      dst_ptr[0] = (long double)dst_cast;
    } else {
      ygglog_throw_error("%sconvert_python2c: Float precision of %lu unsupported.",
			 error_prefix, precision);
    }
    strcat(type_name, "float");
    break;
  }
  case T_INTEGER:
  case T_INT: {
    long dst_cast = PyLong_AsLong(pyobj);
    switch (precision) {
    case 8: {
      int8_t *dst_ptr = (int8_t*)dst;
      dst_ptr[0] = (int8_t)dst_cast;
      break;
    }
    case 16: {
      int16_t *dst_ptr = (int16_t*)dst;
      dst_ptr[0] = (int16_t)dst_cast;
      break;
    }
    case 32: {
      int32_t *dst_ptr = (int32_t*)dst;
      dst_ptr[0] = (int32_t)dst_cast;
      break;
    }
    case 64: {
      int64_t *dst_ptr = (int64_t*)dst;
      dst_ptr[0] = (int64_t)dst_cast;
      break;
    }
    default: {
      if ((precision == 0) || (sizeof(long) == precision/8)) {
	long *dst_ptr = (long*)dst;
	dst_ptr[0] = dst_cast;
      } else {
	ygglog_throw_error("%sconvert_python2c: Int precision of %lu unsupported.",
			   error_prefix, precision);
      }
    }
    }
    strcat(type_name, "long");
    break;
  }
  case T_UINT: {
    long dst_cast = PyLong_AsLong(pyobj);
    switch (precision) {
    case 8: {
      uint8_t *dst_ptr = (uint8_t*)dst;
      dst_ptr[0] = (uint8_t)dst_cast;
      break;
    }
    case 16: {
      uint16_t *dst_ptr = (uint16_t*)dst;
      dst_ptr[0] = (uint16_t)dst_cast;
      break;
    }
    case 32: {
      uint32_t *dst_ptr = (uint32_t*)dst;
      dst_ptr[0] = (uint32_t)dst_cast;
      break;
    }
    case 64: {
      uint64_t *dst_ptr = (uint64_t*)dst;
      dst_ptr[0] = (uint64_t)dst_cast;
      break;
    }
    default: {
      if ((precision == 0) || (sizeof(long) == precision/8)) {
	long *dst_ptr = (long*)dst;
	dst_ptr[0] = dst_cast;
      } else {
	ygglog_throw_error("%sconvert_python2c: Uint precision of %lu unsupported.",
			   error_prefix, precision);
      }
    }
    }
    strcat(type_name, "long");
    break;
  }
  case T_BOOLEAN: {
    bool *dst_ptr = (bool*)dst;
    long res = PyLong_AsLong(pyobj);
    if (res) {
      dst_ptr[0] = true;
    } else {
      dst_ptr[0] = false;
    }
    strcat(type_name, "bool");
    break;
  }
  case T_NULL: {
    void **dst_ptr = (void**)dst;
    dst_ptr[0] = NULL;
    break;
  }
  case T_COMPLEX: {
    double real_cast = PyComplex_RealAsDouble(pyobj);
    double imag_cast = PyComplex_ImagAsDouble(pyobj);
    if ((precision == 0) || (sizeof(complex_double_t) == precision/8)) {
      complex_double_t *dst_ptr = (complex_double_t*)dst;
      dst_ptr->re = real_cast;
      dst_ptr->im = imag_cast;
    } else if (sizeof(complex_float_t) == precision/8) {
      complex_float_t *dst_ptr = (complex_float_t*)dst;
      dst_ptr->re = (float)real_cast;
      dst_ptr->im = (float)imag_cast;
    } else if (sizeof(complex_long_double_t) == precision/8) {
      complex_long_double_t *dst_ptr = (complex_long_double_t*)dst;
      dst_ptr->re = (long double)real_cast;
      dst_ptr->im = (long double)imag_cast;
    } else {
      ygglog_throw_error("%sconvert_python2c: Complex precision of %lu unsupported.",
			 error_prefix, precision);
    }
    strcat(type_name, "complex");
    break;
  }
  case T_STRING:
  case T_BYTES: {
    char **dst_ptr = (char**)dst;
    char *res = PyBytes_AsString(pyobj);
    if (precision != 0) {
      if ((size_t)(PyBytes_Size(pyobj)) > precision/8) {
	ygglog_throw_error("%sconvert_python2c: String has size (%lu bytes) larger than the size of the buffer (%lu bytes).",
			   error_prefix, PyBytes_Size(pyobj), precision/8);
      }
    }
    strcpy(dst_ptr[0], res);
    strcat(type_name, "bytes");
    break;
  }
  case T_UNICODE: {
    char **dst_ptr = (char**)dst;
#ifdef PyUnicode_DATA
    char *res = (char*)PyUnicode_DATA(pyobj);
#else
    const char *res = PyUnicode_AS_DATA(pyobj);
#endif
    if (precision != 0) {
      if (strlen(res) > precision/8) {
	ygglog_throw_error("%sconvert_python2c: String has size (%lu bytes) larger than the size of the buffer (%lu bytes).",
			   error_prefix, strlen(res), precision/8);
      }
    }
    strcpy(dst_ptr[0], res);
    strcat(type_name, "unicode");
    break;
  }
  default: {
    ygglog_throw_error("%sconvert_python2c: Unsupported type code: %d", error_prefix, type_code);
  }
  }
  if (PyErr_Occurred() != NULL) {
    ygglog_throw_error("%sconvert_python2c: Python error.", error_prefix);
  }
};

/*!
  @brief Convert a C object into a Python representation.
  @param[in] src void* Pointer to C variable.
  @param[in] type_code int Code indicating type of data contained in src.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] precision size_t Size (in bits) of the C type. Defaults to 0.
  @returns PyObject* Python object.
 */
PyObject* convert_c2python(const void *src, int type_code,
			   const char* error_prefix="",
			   size_t precision=0) {
  initialize_python(error_prefix);
  PyObject *dst = NULL;
  if (type_code < 0)
    return dst;
  if (src == NULL) {
    ygglog_throw_error("%sconvert_c2python: C pointer is NULL.", error_prefix);
  }
  char type_name[100] = "";
  switch (type_code) {
  case T_ARRAY: {
  case T_OBJECT:
    dst = Py_BuildValue("O", (const PyObject*)src);
    strcat(type_name, "list/dict");
    break;
  }
  case T_NUMBER:
  case T_FLOAT: {
    double src_cast = 0.0;
    if ((precision == 0) || (sizeof(double) == precision/8)) {
      double *src_ptr = (double*)src;
      src_cast = src_ptr[0];
    } else if (sizeof(float) == precision/8) {
      float *src_ptr = (float*)src;
      src_cast = (double)(src_ptr[0]);
    } else if (sizeof(long double) == precision/8) {
      long double *src_ptr = (long double*)src;
      src_cast = (double)(src_ptr[0]);
    } else {
      ygglog_throw_error("%sconvert_c2python: Float precision of %lu unsupported.",
			 error_prefix, precision);
    }
    dst = PyFloat_FromDouble(src_cast);
    strcat(type_name, "float");
    break;
  }
  case T_INTEGER:
  case T_INT: {
    long src_cast = 0;
    switch (precision) {
    case 8: {
      int8_t *src_ptr = (int8_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    case 16: {
      int16_t *src_ptr = (int16_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    case 32: {
      int32_t *src_ptr = (int32_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    case 64: {
      int64_t *src_ptr = (int64_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    default: {
      if ((precision == 0) || (sizeof(long) == precision/8)) {
	long *src_ptr = (long*)src;
	src_cast = src_ptr[0];
      } else {
	ygglog_throw_error("%sconvert_c2python: Int precision of %lu unsupported.",
			   error_prefix, precision);
      }
    }
    }
    dst = PyLong_FromLong(src_cast);
    strcat(type_name, "int");
    break;
  }
  case T_BOOLEAN:
  case T_UINT: {
    long src_cast = 0;
    switch (precision) {
    case 8: {
      uint8_t *src_ptr = (uint8_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    case 16: {
      uint16_t *src_ptr = (uint16_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    case 32: {
      uint32_t *src_ptr = (uint32_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    case 64: {
      uint64_t *src_ptr = (uint64_t*)src;
      src_cast = (long)(src_ptr[0]);
      break;
    }
    default: {
      ygglog_throw_error("%sconvert_c2python: Uint precision of %lu unsupported.",
			 error_prefix, precision);
    }
    }
    if (type_code == T_BOOLEAN) {
      dst = PyBool_FromLong(src_cast);
    } else {
      dst = PyLong_FromLong(src_cast);
    }
    strcat(type_name, "uint");
    break;
  }
  case T_COMPLEX: {
    Py_complex src_cast = {0, 0};
    if ((precision == 0) || (sizeof(complex_double_t) == precision/8)) {
      complex_double_t *src_ptr = (complex_double_t*)src;
      src_cast.real = src_ptr->re;
      src_cast.imag = src_ptr->im;
    } else if (sizeof(complex_float_t) == precision/8) {
      complex_float_t *src_ptr = (complex_float_t*)src;
      src_cast.real = (double)(src_ptr->re);
      src_cast.imag = (double)(src_ptr->im);
    } else if (sizeof(complex_long_double_t) == precision/8) {
      complex_long_double_t *src_ptr = (complex_long_double_t*)src;
      src_cast.real = (double)(src_ptr->re);
      src_cast.imag = (double)(src_ptr->im);
    } else {
      ygglog_throw_error("%sconvert_c2python: Complex precision of %lu unsupported.",
			 error_prefix, precision);
    }
    dst = PyComplex_FromCComplex(src_cast);
    strcat(type_name, "complex");
    break;
  }
  case T_NULL: {
    dst = Py_None;
    break;
  }
  case T_STRING:
  case T_BYTES: {
    char **src_ptr = (char**)src;
    dst = PyBytes_FromString(src_ptr[0]);
    strcat(type_name, "bytes");
    break;
  }
  case T_UNICODE: {
    char **src_ptr = (char**)src;
    dst = PyUnicode_FromString(src_ptr[0]);
    strcat(type_name, "unicode");
    break;
  }
  default: {
    ygglog_throw_error("%sconvert_c2python: Unsupported type code: %d", error_prefix, type_code);
  }
  }
  if (dst == NULL) {
    ygglog_throw_error("%sconvert_c2python: Error getting type '%s'.",
		       error_prefix, type_name);
  }
  if (PyErr_Occurred() != NULL) {
    ygglog_throw_error("%sconvert_c2python: Python error.", error_prefix);
  }
  return dst;
};

/*!
  @brief Create a new Python list and raise an error if it fails.
  @param[in] N int Number of elements list should be initialized with.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @returns Python list.
 */
PyObject* new_python_list(int N, const char* error_prefix="") {
  initialize_python(error_prefix);
  PyObject *out = PyList_New(N);
  if (out == NULL) {
    ygglog_throw_error("%sFailed to initialize Python list.");
  }
  return out;
};

/*!
  @brief Create a new Python dict and raise an error if it fails.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @returns Python dict.
 */
PyObject* new_python_dict(const char* error_prefix="") {
  initialize_python(error_prefix);
  PyObject *out = PyDict_New();
  if (out == NULL) {
    ygglog_throw_error("%sFailed to initialize Python dict.");
  }
  return out;
};

/*!
  @brief Set an item in a Python list to a Python object, throw an error if it fails or the provided objects do not have the right type.
  @param[in] pyobj PyObject* Python list.
  @param[in] index size_t Index in Python list of item that should be set.
  @param[in] item PyObject* Object to assign to the Python list item.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
 */
void set_item_python_list(PyObject *pyobj, size_t index,
			  PyObject *item, const char* error_prefix="",
			  int type_code=-1) {
  check_python_object(pyobj, (int)T_ARRAY, error_prefix);
  check_python_object(item, type_code, error_prefix);
  if (PyList_SetItem(pyobj, index, item) < 0) {
    ygglog_throw_error("%sFailed to set element %zu.",
		       error_prefix, index);
  }
};

/*!
  @brief Set an item in a Python list to a C object, throw an error if it fails or the provided objects do not have the right type.
  @param[in] pyobj PyObject* Python list.
  @param[in] index size_t Index in Python list of item that should be set.
  @param[in] item void* Pointer to C object to convert to a Python object and assign to the Python list item.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
  @param[in] precision size_t Size (in bits) of the C type. Defaults to 0.
 */
void set_item_python_list_c(PyObject *pyobj, size_t index, const void *item,
			    const char* error_prefix="",
			    int type_code=-1, size_t precision=0) {
  PyObject *py_item = convert_c2python(item, type_code, error_prefix,
				       precision);
  return set_item_python_list(pyobj, index, py_item,
			      error_prefix, type_code);
};

/*!
  @brief Set an item in a Python dict to a Python object, throw an error if it fails or the provided objects do not have the right type.
  @param[in] pyobj PyObject* Python dict.
  @param[in] key char* Key in Python dict for item that should be set.
  @param[in] item PyObject* Object to assign to the Python dict item.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
 */
void set_item_python_dict(PyObject *pyobj, const char* key,
			  PyObject *item, const char* error_prefix="",
			  int type_code=-1) {
  check_python_object(pyobj, T_OBJECT, error_prefix);
  check_python_object(item, type_code, error_prefix);
  if (PyDict_SetItemString(pyobj, key, item) < 0) {
    ygglog_throw_error("%sFailed to set element %s.",
		       error_prefix, key);
  }
};

/*!
  @brief Set an item in a Python dict to a Python object, throw an error if it fails or the provided objects do not have the right type.
  @param[in] pyobj PyObject* Python dict.
  @param[in] key char* Key in Python dict for item that should be set.
  @param[in] item void* Pointer to C object to convert to a Python object and assign to the Python list item.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
  @param[in] precision size_t Size (in bits) of the C type. Defaults to 0.
 */
void set_item_python_dict_c(PyObject *pyobj, const char* key,
			    const void *item, const char* error_prefix="",
			    int type_code=-1, size_t precision=0) {
  PyObject *py_item = convert_c2python(item, type_code, error_prefix,
				       precision);
  return set_item_python_dict(pyobj, key, py_item,
			      error_prefix, type_code);
};

/*!
  @brief Get a Python object from a Python list.
  @param[in] pyobj PyObject* Python list.
  @param[in] index size_t Index in Python list of item that should be returned.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
  @param[in] allow_null bool If true, no error will be raised if the item cannot be found.
  @returns PyObject* Python object.
 */
PyObject *get_item_python_list(PyObject *pyobj, size_t index,
			       const char* error_prefix="",
			       int type_code=-1,
			       bool allow_null=false) {
  PyObject *out = PyList_GetItem(pyobj, index);
  if ((out == NULL) && (!(allow_null))) {
    ygglog_throw_error("%sFailed to get element %zu.",
		       error_prefix, index);
  }
  if (out != NULL) {
    check_python_object(pyobj, type_code, error_prefix);
  }
  return out;
};

/*!
  @brief Get a C object from a Python list.
  @param[in] pyobj PyObject* Python list.
  @param[in] index size_t Index in Python list of item that should be returned.
  @param[in,out] dst Pointer to C variable where converted data should be stored.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
  @param[in] precision size_t Size (in bits) of the C type. Defaults to 0.
  @param[in] allow_null bool If true, no error will be raised if the item cannot be found.
 */
void get_item_python_list_c(PyObject *pyobj, size_t index, void *dst,
			    const char* error_prefix="",
			    int type_code=-1, size_t precision=0,
			    bool allow_null=false) {
  PyObject *out = get_item_python_list(pyobj, index, error_prefix,
				       type_code, allow_null);
  if (out != NULL) {
    convert_python2c(out, dst, type_code, error_prefix, precision);
  }
};

/*!
  @brief Get a Python object from a Python dict.
  @param[in] pyobj PyObject* Python dict.
  @param[in] key char* Key in Python dict for item that should be returned.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
  @param[in] allow_null bool If true, no error will be raised if the item cannot be found.
  @returns PyObject* Python object.
 */
PyObject *get_item_python_dict(PyObject *pyobj, const char* key,
			       const char* error_prefix="",
			       int type_code=-1,
			       bool allow_null=false) {
  PyObject *out = PyDict_GetItemString(pyobj, key);
  if ((out == NULL) && (!(allow_null))) {
    ygglog_throw_error("%sFailed to get element for key '%s'.",
		       error_prefix, key);
  }
  if (out != NULL) {
    check_python_object(pyobj, type_code, error_prefix);
  }
  return out;
};

/*!
  @brief Get a C object from a Python dict.
  @param[in] pyobj PyObject* Python dict.
  @param[in] key char* Key in Python dict for item that should be returned.
  @param[in,out] dst Pointer to C variable where converted data should be stored.
  @param[in] error_prefix char* Prefix that should be added to error messages.
  @param[in] type_code int Code specifying type that item should contain.
  @param[in] precision size_t Size (in bits) of the C type. Defaults to 0.
  @param[in] allow_null bool If true, no error will be raised if the item cannot be found.
 */
void get_item_python_dict_c(PyObject *pyobj, const char* key,
			    void *dst, const char* error_prefix="",
			    int type_code=-1, size_t precision=0,
			    bool allow_null=false) {
  PyObject *out = get_item_python_dict(pyobj, key, error_prefix,
				       type_code, allow_null);
  if (out != NULL) {
    convert_python2c(out, dst, type_code, error_prefix, precision);
  }
};


#endif /*DATATYPES_UTILS_H_*/
// Local Variables:
// mode: c++
// End:
