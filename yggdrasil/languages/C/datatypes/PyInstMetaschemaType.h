#ifndef PYINST_METASCHEMA_TYPE_H_
#define PYINST_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"
#include "PyObjMetaschemaType.h"
#include "JSONObjectMetaschemaType.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Base class for pyinst type definition.

  The PyInstMetaschemaType provides basic functionality for encoding/decoding
  pyinst datatypes from/to JSON style strings.
 */
class PyInstMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for PyInstMetaschemaType.
    @param[in] class_name char* Name of Python class.
    @param[in] args_type JSONObjectMetaschemaType Type definition for instance arguments.
   */
  PyInstMetaschemaType(const char* class_name,
		       const JSONObjectMetaschemaType* args_type) :
    MetaschemaType("instance"), class_name_(""), args_type_(NULL) {
    if (class_name != NULL) {
      update_class_name(class_name, true);
    }
    if (args_type != NULL) {
      update_args_type(args_type, true);
    }
  }
  /*!
    @brief Constructor for PyInstMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  PyInstMetaschemaType(const rapidjson::Value &type_doc) :
    MetaschemaType(type_doc), class_name_(""), args_type_(NULL) {
    if (!(type_doc.HasMember("class"))) {
      ygglog_throw_error("PyInstMetaschemaType: instance type must include 'class'.");
    }
    if (!(type_doc["class"].IsString())) {
      ygglog_throw_error("PyInstMetaschemaType: 'class' value must be a string.");
    }
    update_class_name(type_doc["class"].GetString(), true);
    if (!(type_doc.HasMember("args"))) {
      ygglog_throw_error("PyInstMetaschemaType: instance type must include 'args'.");
    }
    if (!(type_doc["args"].IsObject())) {
      ygglog_throw_error("PyInstMetaschemaType: 'args' value must be an object.");
    }
  }
  /*!
    @brief Destructor for PyInstMetaschemaType.
    Free the type string malloc'd during constructor.
   */
  virtual ~PyInstMetaschemaType() {
    class_name_[0] = '\0';
    delete args_type_;
    args_type_ = NULL;
  }
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  bool operator==(const MetaschemaType &Ref) const override {
    if (!(MetaschemaType::operator==(Ref)))
      return false;
    const PyInstMetaschemaType *pRef = dynamic_cast<const PyInstMetaschemaType*>(&Ref);
    if (!pRef)
      return false;
    if (strcmp(class_name_, pRef->class_name()) != 0)
      return false;
    if (args_type_ != pRef->args_type())
      return false;
    return true;
  }
 /*!
    @brief Create a copy of the type.
    @returns pointer to new MetaschemaType instance with the same data.
   */
  PyInstMetaschemaType* copy() const override {
    return (new PyInstMetaschemaType(class_name_, args_type_));
  }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() const override {
    MetaschemaType::display();
    printf("%-15s = %s\n", "class_name", class_name_);
    printf("Args type:\n");
    args_type_->display();
  }
  /*!
    @brief Display data.
    @param[in] x YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(YggGeneric* x, const char* indent="") const override {
    python_t* arg = (python_t*)(x->get_data());
    FILE* fout = stdout;
    if (PyObject_Print(arg->obj, fout, 0) < 0) {
      ygglog_throw_error("PyInstMetaschemaType::display_generic: Failed to print the Python object.");
    }
  }
  /*!
    @brief Get the class name string.
    @returns const char Pointer to the class name string.
   */
  const char* class_name() const { return class_name_; }
  /*!
    @brief Get the argument type.
    @returns JSONObjectMetaschemaType* Arguments type.
   */
  const JSONObjectMetaschemaType* args_type() const { return args_type_; }
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
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override {
    MetaschemaType::update(new_info);
    const PyInstMetaschemaType* new_info_inst = dynamic_cast<const PyInstMetaschemaType*>(new_info);
    update_class_name(new_info_inst->class_name());
    update_args_type(new_info_inst->args_type());
  }
  /*!
    @brief Update the instance's class name.
    @param[in] new_class_name const char * String for new class name.
   */
  void update_class_name(const char* new_class_name, bool force=false) {
    if ((!(force)) && (strlen(class_name_) > 0) && (strcmp(class_name_, new_class_name) != 0)) {
      ygglog_throw_error("PyInstMetaschemaType::update_class_name: Cannot update class name from %s to %s.",
    			 class_name_, new_class_name);
    }
    strncpy(class_name_, new_class_name, PYTHON_NAME_SIZE);
  }
  /*!
    @brief update the instance's args type.
    @param[in] new_args JSONObjectMetaschemaType* New args type.
   */
  void update_args_type(const JSONObjectMetaschemaType* new_args_type,
			bool force=false) {
    if ((!(force)) && (args_type_ != NULL) && (*new_args_type != *args_type_)) {
      ygglog_throw_error("PyInstMetaschemaType::update_args_type: Cannot update args type.");
    }
    if (args_type_ != NULL)
      delete args_type_;
    args_type_ = new_args_type->copy();
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
      ygglog_throw_error("PyInstMetaschemaType::python2c: Failed to realloc data.");
    }
    PyObject *py_class = import_python_class("yggdrasil.metaschema.datatypes.InstanceMetaschemaType",
					     "InstanceMetaschemaType",
					     "PyInstMetaschemaType::import_python: ");
    PyObject *py_args = PyObject_CallMethod(py_class, "encode_data",
					    "Os", pyobj, NULL);
    Py_DECREF(py_class);
    if (py_args == NULL) {
      ygglog_throw_error("PyObjMetaschemaType::python2c: Failed to get instance arguments.");
    }
    strcpy(idata->name, class_name_);
    idata->args = args_type_->python2c(py_args);
    idata->obj = pyobj;
    data[0] = (void*)idata;
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric* cobj) const override {
    python_t *arg = (python_t*)(cobj->get_data());
    PyObject *pyobj = arg->obj;
    return pyobj;
  }

  // Encoding
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const override {
    if (!(MetaschemaType::encode_type_prop(writer))) { return false; }
    writer->Key("class");
    writer->String(class_name_);
    writer->Key("args");
    writer->StartObject();
    std::map<const char*, MetaschemaType*, strcomp> properties = args_type_->properties();
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it = properties.begin();
    for (it = properties.begin(); it != properties.end(); it++) {
      writer->Key(it->first);
      if (!(it->second->encode_type(writer)))
	return false;
    }
    writer->EndObject();
    return true;
  }
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
    python_t arg0 = va_arg(ap.va, python_t);
    YggGeneric* args = (YggGeneric*)(arg0.args);
    (*nargs)--;
    return args_type_->encode_data(writer, args);
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
    YggGeneric* cargs = new YggGeneric(args_type_, NULL, 0);
    if (!(args_type_->decode_data(data, cargs))) {
      ygglog_error("PyInstMetaschemaType::decode_data: Error decoding arguments.");
      return false;
    }
    // Decode the object
    python_t *arg;
    python_t **p;
    if (allow_realloc) {
      p = va_arg(ap.va, python_t**);
      python_t *temp = (python_t*)realloc(p[0], sizeof(python_t));
      if (temp == NULL) {
	ygglog_throw_error("PyInstMetaschemaType::decode_data: Failed to realloc variable.");
      }
      p[0] = temp;
      arg = *p;
    } else {
      arg = va_arg(ap.va, python_t*);
      p = &arg;
    }
    (*nargs)--;
    strncpy(arg->name, class_name_, PYTHON_NAME_SIZE);
    arg->args = cargs;
    arg->obj = NULL;
    // Get the class/function and call it
    PyObjMetaschemaType *class_type = new PyObjMetaschemaType("class");
    PyObject *py_class = class_type->import_python(arg->name);
    PyObject *py_args = PyTuple_New(0);
    PyObject *py_kwargs = args_type_->c2python((YggGeneric*)(arg->args));
    if (py_args == NULL) {
      ygglog_throw_error("PyInstMetaschemaType::decode_data: Failed to construct arguments for Python callable.");
    }
    if (py_kwargs == NULL) {
      ygglog_throw_error("PyInstMetaschemaType::decode_data: Failed to construct keyword arguments for Python callable.");
    }
    arg->obj = PyObject_Call(py_class, py_args, py_kwargs);
    if (arg->obj == NULL) {
      ygglog_throw_error("PyInstMetaschemaType::decode_data: Failed to call constructor.");
    }
    delete class_type;
    return true;
  }

private:
  char class_name_[PYTHON_NAME_SIZE];
  JSONObjectMetaschemaType *args_type_;
  
};


#endif /*PYINST_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
