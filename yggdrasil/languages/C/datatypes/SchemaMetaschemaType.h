#ifndef SCHEMA_METASCHEMA_TYPE_H_
#define SCHEMA_METASCHEMA_TYPE_H_

#include "MetaschemaType.h"


/*!
  @brief Base class for metaschema type definitions.

  The MetaschemaType provides basic functionality for encoding/decoding
  datatypes from/to JSON style strings.
 */
class SchemaMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for SchemaMetaschemaType.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  SchemaMetaschemaType(const bool use_generic=true) :
    // Always generic
    MetaschemaType("schema", true) {}
  /*!
    @brief Constructor for SchemaMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing
    the type definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  SchemaMetaschemaType(const rapidjson::Value &type_doc,
		       const bool use_generic=true) :
    // Always generic
    MetaschemaType(type_doc, true) {}
  /*!
    @brief Constructor for SchemaMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  SchemaMetaschemaType(PyObject* pyobj, const bool use_generic=true) :
    // Always generic
    MetaschemaType(pyobj, true) {} 
  /*!
    @brief Copy constructor.
    @param[in] other SchemaMetaschemaType* Instance to copy.
   */
  SchemaMetaschemaType(const SchemaMetaschemaType &other) :
    SchemaMetaschemaType(other.use_generic()) {}
  /*!
    @brief Create a copy of the type.
    @returns pointer to new SchemaMetaschemaType instance with the same data.
   */
  SchemaMetaschemaType* copy() const override { return (new SchemaMetaschemaType(use_generic())); }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const override {
    if (data == NULL) {
      ygglog_throw_error("SchemaMetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      dtype_t* old_data = (dtype_t*)orig_data;
      dtype_t* new_data = copy_dtype(old_data);
      if (new_data == NULL) {
	ygglog_throw_error("SchemaMetaschemaType::copy_generic: Failed to copy datatype struct.");
      }
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
      ygglog_throw_error("SchemaMetaschemaType::free_generic: Generic object is NULL.");
    }
    dtype_t **ptr = (dtype_t**)(data->get_data_pointer());
    if (destroy_dtype(ptr) < 0) {
      ygglog_throw_error("SchemaMetaschemaType::free_generic: Failed to destroy datatype struct.");
    }
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(const YggGeneric* data, const char* indent="") const override {
    if (data == NULL) {
      ygglog_throw_error("SchemaMetaschemaType::display_generic: Generic object is NULL.");
    }
    dtype_t *arg = (dtype_t*)(data->get_data());
    display_dtype(arg, indent);
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
    va_arg(ap.va, dtype_t*);
    out++;
    return out;
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    return sizeof(dtype_t);
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    return 1;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject* pyobj) const override {
    YggGeneric* cobj = new YggGeneric(this, NULL, 0);
    dtype_t** data = (dtype_t**)(cobj->get_data_pointer());
    data[0] = create_dtype_python(pyobj, false);
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric *cobj) const override {
    PyObject *pyobj = NULL;
    dtype_t *src = (dtype_t*)(cobj->get_data());
    if (src != NULL) {
      MetaschemaType* obj = (MetaschemaType*)(src->obj);
      if (obj != NULL) {
	pyobj = obj->as_python_dict();
      }
    }
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
    dtype_t* arg = va_arg(ap.va, dtype_t*);
    MetaschemaType* obj = (MetaschemaType*)(arg->obj);
    (*nargs)--;
    return obj->encode_type(writer);
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
    dtype_t* arg = (dtype_t*)(x->get_data());
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
    dtype_t *arg;
    dtype_t **p;
    if (allow_realloc) {
      p = va_arg(ap.va, dtype_t**);
      bool new_obj = false;
      if (p[0] == NULL)
	new_obj = true;
      dtype_t *temp = (dtype_t*)realloc(p[0], sizeof(dtype_t));
      if (temp == NULL) {
	ygglog_throw_error("SchemaMetaschemaType::decode_data: Failed to realloc variable.");
      }
      if (new_obj) {
	temp->type[0] = '\0';
	temp->use_generic = false;
	temp->obj = NULL;
      }
      p[0] = temp;
      arg = *p;
    } else {
      arg = va_arg(ap.va, dtype_t*);
      p = &arg;
    }
    (*nargs)--;
    arg->type[0] = '\0';
    arg->use_generic = false;
    if (arg->obj != NULL) {
      ygglog_info("SchemaMetaschemaType::decode_data: Datatype has existing type. Deleting.");
      MetaschemaType* old_obj = (MetaschemaType*)(arg->obj);
      delete old_obj;
    }
    arg->obj = NULL;
    MetaschemaType* obj = (MetaschemaType*)type_from_doc_c(&data, use_generic());
    if (obj == NULL) {
      ygglog_throw_error("SchemaMetaschemaType::decode_data: Failed to decode type from JSON document.");
    }
    arg->obj = obj;
    arg->use_generic = obj->use_generic();
    strncpy(arg->type, obj->type(), COMMBUFFSIZ);
    display_dtype(arg, "");
    return true;
  }

};


#endif /*SCHEMA_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
