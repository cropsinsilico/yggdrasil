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
    @param[in] type const character pointer to the name of the type.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  PyObjMetaschemaType(const char* type, const bool use_generic=false) :
    MetaschemaType(type, use_generic) {}
  /*!
    @brief Constructor for PyObjMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  PyObjMetaschemaType(const rapidjson::Value &type_doc,
		      const bool use_generic=false) :
    MetaschemaType(type_doc, use_generic) {}
  /*!
    @brief Constructor for PyObjMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  PyObjMetaschemaType(PyObject* pyobj, const bool use_generic=false) :
    MetaschemaType(pyobj, use_generic) {}
  /*!
    @brief Copy constructor.
    @param[in] other PyObjMetaschemaType* Instance to copy.
   */
  PyObjMetaschemaType(const PyObjMetaschemaType &other) :
    PyObjMetaschemaType(other.type(), other.use_generic()) {}
  /*!
    @brief Create a copy of the type.
    @returns pointer to new PyObjMetaschemaType instance with the same data.
   */
  PyObjMetaschemaType* copy() const override { return (new PyObjMetaschemaType(type(), use_generic())); }
  /*!
    @brief Copy Python data structure.
    @param[in] x python_t Python struct.
    @returns python_t Copy of data.
   */
  static python_t copy_python_t(python_t x) {
    python_t out = init_python();
    strncpy(out.name, x.name, PYTHON_NAME_SIZE);
    out.args = NULL;
    if (x.args != NULL) {
      YggGeneric* args = (YggGeneric*)(x.args);
      out.args = args->copy();
    }
    out.kwargs = NULL;
    if (x.kwargs != NULL) {
      YggGeneric* kwargs = (YggGeneric*)(x.kwargs);
      out.kwargs = kwargs->copy();
    }
    out.obj = NULL;
    if (x.obj != NULL) {
      // Increment reference count for underlying Python object
      out.obj = Py_BuildValue("O", x.obj);
    }
    return out;
  }
  /*!
    @brief Free a structure containing a Python object.
    @param[in] x python_t* Pointer to Python object structure that should be freed.
  */
  static void free_python_t(python_t *x) {
    if (x != NULL) {
      x->name[0] = '\0';
      if (x->args != NULL) {
	YggGeneric* args = (YggGeneric*)(x->args);
	delete args;
	x->args = NULL;
      }
      if (x->kwargs != NULL) {
	YggGeneric* kwargs = (YggGeneric*)(x->kwargs);
	delete kwargs;
	x->kwargs = NULL;
      }
      if (x->obj != NULL) {
	Py_DECREF(x->obj);
	x->obj = NULL;
      }
    }
  }
  /*!
    @brief Display a Python object structure.
    @param[in] x python_t Structure containing Python object to display.
  */
  static void display_python_t(python_t x) {
    FILE* fout = stdout;
    if (x.obj != NULL) {
      if (PyObject_Print(x.obj, fout, 0) < 0) {
	ygglog_throw_error("display_python: Failed to print the Python object.");
      }
    }
  }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const override {
    if (data == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      python_t* old_data = (python_t*)orig_data;
      python_t* new_data = (python_t*)malloc(sizeof(python_t));
      if (new_data == NULL) {
	ygglog_throw_error("PyObjMetaschemaType::copy_generic: Failed to malloc memory for Python wrapper struct.");
      }
      new_data[0] = copy_python_t(*old_data);
      out = (void*)new_data;
    }
    return out;
  }
  /*!
    @brief Free data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
   */
  void free_generic(YggGeneric* data) const override {
    if (data == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::free_generic: Generic object is NULL.");
    }
    python_t** ptr = (python_t**)(data->get_data_pointer());
    if (ptr[0] != NULL) {
      free_python_t(ptr[0]);
      free(ptr[0]);
      ptr[0] = NULL;
    }
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(const YggGeneric* data, const char* indent="") const override {
    UNUSED(indent);
    if (data == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::display_generic: Generic object is NULL.");
    }
    python_t* arg = (python_t*)(data->get_data());
    display_python_t(*arg);
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    size_t out = MetaschemaType::update_from_serialization_args(nargs, ap);
    if (use_generic())
      return out;
    va_arg(ap.va, python_t);
    out++;
    return out;
  }
  /*!
    @brief Get the size of the type in bytes.
    @returns size_t Type size.
   */
  const size_t nbytes() const override {
    return sizeof(python_t);
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  virtual size_t nargs_exp() const override {
    return 1;
  }
  /*!
    @brief Import a Python object (e.g. class or function).
    @param[in] name const char* Name of Python module and class/function.
    @returns PyObject* Python object.
   */
  PyObject* import_python(const char* name) const {
    PyObject *py_class = import_python_class("yggdrasil.metaschema.datatypes.ClassMetaschemaType",
					     "ClassMetaschemaType",
					     "PyObjMetaschemaType::import_python: ");
    PyObject *py_function = PyObject_CallMethod(py_class, "decode_data",
    						"ss", name, NULL);
    Py_DECREF(py_class);
    if (py_function == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::import_python: Failed to import Python object: '%s'.", name);
    }
    return py_function;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject* pyobj) const override {
    YggGeneric* cobj = new YggGeneric(this, NULL, 0);
    void** data = cobj->get_data_pointer();
    python_t* idata = (python_t*)realloc(data[0], nbytes());
    if (idata == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::python2c: Failed to realloc data.");
    }
    PyObject *py_class = import_python_class("yggdrasil.metaschema.datatypes.ClassMetaschemaType",
					     "ClassMetaschemaType",
					     "PyObjMetaschemaType::import_python: ");
    PyObject *py_name = PyObject_CallMethod(py_class, "encode_data",
					    "Os", pyobj, NULL);
    Py_DECREF(py_class);
    if (py_name == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::python2c: Failed to get function name.");
    }
    idata->name[0] = '\0';
    idata->args = NULL;
    idata->kwargs = NULL;
    idata->obj = pyobj;
    convert_python2c(py_name, &(idata->name), T_BYTES,
		     "PyObjMetaschemaType::python2c: ",
		     PYTHON_NAME_SIZE);
    Py_DECREF(py_name);
    data[0] = (void*)idata;
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric *cobj) const override {
    python_t *arg = (python_t*)(cobj->get_data());
    if (arg == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::c2python: Python structure is NULL.");
    }
    PyObject *pyobj = arg->obj;
    return pyobj;
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
    size_t bytes_precision = PYTHON_NAME_SIZE;
    python_t arg0 = va_arg(ap.va, python_t);
    if (strlen(arg0.name) < bytes_precision) {
      bytes_precision = strlen(arg0.name);
    }
    (*nargs)--;
    bool out = writer->String(arg0.name, (rapidjson::SizeType)bytes_precision);
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
    python_t arg;
    arg.name[0] = '\0';
    arg.args = NULL;
    arg.kwargs = NULL;
    arg.obj = NULL;
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
    size_t nbytes_expected = PYTHON_NAME_SIZE;
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
    arg->name[0] = '\0';
    strncpy(arg->name, (char*)encoded_bytes, nbytes_expected);
    arg->args = NULL;
    arg->kwargs = NULL;
    arg->obj = import_python(arg->name);
    return true;
  }
  
};


#endif /*PYOBJ_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
