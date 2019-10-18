#ifndef PYOBJ_METASCHEMA_TYPE_H_
#define PYOBJ_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Base class for pyobj type definition.

  The PyObjMetaschemaType provides basic functionality for encoding/decoding
  pyobj datatypes from/to JSON style strings.
 */
class PyObjMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for PyObjMetaschemaType.
    @param[in] subtype const character pointer to the name of the subtype.
    @param[in] precision size_t Type precision in bits.
    @param[in] units const char * (optional) Type units.
   */
  PyObjMetaschemaType(const char* type) :
    MetaschemaType(type) {}
  /*!
    @brief Constructor for PyObjMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  PyObjMetaschemaType(const rapidjson::Value &type_doc) :
    MetaschemaType(type_doc) {}
  /*!
    @brief Display data.
    @param[in] x YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(YggGeneric* x, const char* indent="") const override {
    // TODO
  }
  /*!
    @brief Get the size of the type in bytes.
    @returns size_t Type size.
   */
  const size_t nbytes() const override {
    return PYTHON_NAME_SIZE;
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  virtual size_t nargs_exp() const override {
    return 1;
  }    

  // Encoding
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in,out] nargs size_t * Pointer to the number of arguments contained in
    ap. On return it will be set to the number of arguments used.
    @param[in] ap va_list_t Variable number of arguments that should be encoded
    as a JSON string.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) const override {
    size_t bytes_precision = nbytes();
    python_t arg0 = va_arg(ap.va, python_t);
    if (strlen(arg0.name) < bytes_precision) {
      bytes_precision = strlen(arg0.name);
    }
    (*nargs)--;
    bool out = writer->String(arg0.name, bytes_precision);
    return out;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGeneric* x) const override {
    size_t nargs = 1;
    size_t bytes_precision = nbytes();
    python_t arg;
    x->get_data(arg);
    return MetaschemaType::encode_data(writer, &nargs, arg);
  }

  // Decoding
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[in] allow_realloc int If 1, the passed variables will be reallocated
    to contain the deserialized data.
    @param[in,out] nargs size_t Number of arguments contained in ap. On return,
    the number of arguments assigned from the deserialized data will be assigned
    to this address.
    @param[out] ap va_list_t Reference to variable argument list containing
    address where deserialized data should be assigned.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) const override {
    if ((data.IsArray()) && (data.Size() == 1)) {
      data = data[0];
    }
    if (!(data.IsString())) {
      ygglog_error("PyObjMetaschemaType::decode_data: Raw data is not a string.");
      return false;
    }
    unsigned char* encoded_bytes = (unsigned char*)data.GetString();
    size_t encoded_len = data.GetStringLength();
    size_t nbytes_expected = nbytes();
    if (encoded_len > nbytes_expected) {
      ygglog_error("PyObjMetaschemaType::decode_data: Python object name has a length %lu, but the max is %lu.",
		   encoded_len, nbytes_expected);
    }
    // Decode the object
    python_t *arg;
    python_t **p;
    if (allow_realloc) {
      p = va_arg(ap.va, python_t**);
      python_t *temp = (python_t *)realloc(p[0], sizeof(python_t));
      if (temp == NULL) {
	ygglog_throw_error("PyObjMetaschemaType::decode_data: Failed to realloc variable.");
      }
      p[0] = temp;
      arg = *p;
    } else {
      arg = va_arg(ap.va, python_t*);
      p = &arg;
    }
    (*nargs)--;
    strncpy(arg->name, (char*)encoded_bytes, nbytes_expected);
    arg->obj = NULL;
    // Get the class/function
    if (!(Py_IsInitialized())) {
      Py_Initialize();
      if (!(Py_IsInitialized())) {
    	ygglog_throw_error("PyObjMetaschemaType::decode_data: Python not initialized.");
      }
    }
    PyObject *py_module = PyImport_ImportModule("yggdrasil.metaschema.datatypes.ClassMetaschemaType");
    if (py_module == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::decode_data: Failed to import ClassMetaschemaType Python module.");
    }
    PyObject *py_class = PyObject_GetAttrString(py_module, "ClassMetaschemaType");
    if (py_class == NULL) {
      Py_DECREF(py_module);
      ygglog_throw_error("PyObjMetaschemaType::decode_data: Failed to import ClassMetaschemaType Python class.");
    }
    PyObject *py_function = PyObject_CallMethod(py_class, "decode_data",
    						"ss", arg->name, NULL);
    Py_DECREF(py_module);
    Py_DECREF(py_class);
    if (py_function == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::decode_data: Failed to get Python function by calling PyObjMetaschemaType.decode_data.");
    }
    arg->obj = py_function;
    return true;
  }
  
};


#endif /*PYOBJ_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
