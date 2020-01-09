#ifndef JSON_OBJECT_METASCHEMA_TYPE_H_
#define JSON_OBJECT_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Class for describing JSON objects.

  The JSONObjectMetaschemaType provides basic functionality for encoding/decoding
  JSON object datatypes from/to JSON style strings.
 */
class JSONObjectMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for JSONObjectMetaschemaType.
    @param[in] properties MetaschemaTypeMap Map from
    property names to types.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
  */
  JSONObjectMetaschemaType(const MetaschemaTypeMap properties,
			   const bool use_generic=true) :
    // Always generic
    MetaschemaType("object", true) {
    UNUSED(use_generic);
    strncpy(prop_key_, "properties", 100);
    update_properties(properties, true);
  }
  /*!
    @brief Constructor for JSONObjectMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing
    the type definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
    @param[in] prop_key const char Key to use for properties. Defaults to "properties".
   */
  JSONObjectMetaschemaType(const rapidjson::Value &type_doc,
			   const bool use_generic=true,
			   const char prop_key[100]="properties") :
    // Always generic
    MetaschemaType(type_doc, true) {
    UNUSED(use_generic);
    prop_key_[0] = '\0';
    strncpy(prop_key_, prop_key, 100);
    if (!(type_doc.HasMember(prop_key_)))
      ygglog_throw_error("JSONObjectMetaschemaType: Properties missing.");
    if (!(type_doc[prop_key_].IsObject()))
      ygglog_throw_error("JSONObjectMetaschemaType: Properties must be an object.");
    MetaschemaTypeMap properties;
    for (rapidjson::Value::ConstMemberIterator itr = type_doc[prop_key_].MemberBegin(); itr != type_doc[prop_key_].MemberEnd(); ++itr) {
      MetaschemaType* iprop = (MetaschemaType*)type_from_doc_c(&(itr->value), MetaschemaType::use_generic());
      properties[itr->name.GetString()] = iprop;
    }
    update_properties(properties, true);
  }
  /*!
    @brief Constructor for JSONObjectMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
    @param[in] prop_key const char Key to use for properties. Defaults to "properties".
   */
  JSONObjectMetaschemaType(PyObject* pyobj, const bool use_generic=true,
			   const char prop_key[100]="properties") :
    // Always generic
    MetaschemaType(pyobj, true) {
    UNUSED(use_generic);
    prop_key_[0] = '\0';
    strncpy(prop_key_, prop_key, 100);
    PyObject* pyprops = get_item_python_dict(pyobj, prop_key_,
  					     "JSONObjectMetaschemaType: properties: ",
  					     T_OBJECT);
    MetaschemaTypeMap properties;
    PyObject* pykeys = PyDict_Keys(pyprops);
    if (pykeys == NULL) {
      ygglog_throw_error("JSONObjectMetaschemaType: Failed to get keys from Python dictionary.");
    }
    size_t i, nkeys = PyList_Size(pykeys);
    for (i = 0; i < nkeys; i++) {
      char ikey[100] = "";
      get_item_python_list_c(pykeys, i, ikey,
			     "JSONObjectMetaschemaType: keys: ",
			     T_STRING, 100);
      PyObject* ipyprop = get_item_python_dict(pyprops, ikey,
					       "JSONObjectMetaschemaType: properties: ",
					       T_OBJECT);
      MetaschemaType* iprop = (MetaschemaType*)type_from_pyobj_c(ipyprop, MetaschemaType::use_generic());
      if (iprop == NULL) {
	ygglog_throw_error("JSONObjectMetaschemaType: Failed to reconstruct type for property '%s' from the Python object.", ikey);
      }
      properties[ikey] = iprop;
    }
    update_properties(properties, true);
  }
  /*!
    @brief Copy constructor.
    @param[in] other JSONObjectMetaschemaType* Instance to copy.
   */
  JSONObjectMetaschemaType(const JSONObjectMetaschemaType &other) :
    JSONObjectMetaschemaType(other.properties(),
			     other.use_generic()) {}
  /*!
    @brief Destructor for JSONObjectMetaschemaType.
    Free the type string malloc'd during constructor.
   */
  ~JSONObjectMetaschemaType() {
    free_properties();
  }
  /*!
    @brief Free properties.
   */
  void free_properties() {
    MetaschemaTypeMap::iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      delete it->second;
      it->second = NULL;
    }
    properties_.clear();
  }
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  bool operator==(const MetaschemaType &Ref) const override {
    if (!(MetaschemaType::operator==(Ref)))
      return false;
    const JSONObjectMetaschemaType* pRef = dynamic_cast<const JSONObjectMetaschemaType*>(&Ref);
    if (!pRef)
      return false;
    if (nitems() != pRef->nitems())
      return false;
    MetaschemaTypeMap::const_iterator it;
    MetaschemaTypeMap::const_iterator oit;
    MetaschemaTypeMap new_properties = pRef->properties();
    for (it = properties_.begin(); it != properties_.end(); it++) {
      oit = new_properties.find(it->first);
      if (oit == new_properties.end()) {
	return false;
      }
      if (*(it->second) != *(oit->second)) {
	return false;
      }
    }
    return true;
  }
  /*!
    @brief Determine if the datatype is effectively empty.
    @returns bool true if the datatype is empty, false otherwise.
   */
  bool is_empty() const override {
    if (nitems() == 0)
      return true;
    return false;
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new JSONObjectMetaschemaType instance with the same data.
   */
  JSONObjectMetaschemaType* copy() const override { return (new JSONObjectMetaschemaType(properties_, use_generic())); }
  /*!
    @brief Print information about the type to stdout.
    @param[in] indent char* Indentation to add to display output.
  */
  void display(const char* indent="") const override {
    MetaschemaType::display(indent);
    MetaschemaTypeMap::const_iterator it;
    char new_indent[100] = "";
    strcat(new_indent, indent);
    strcat(new_indent, "    ");
    for (it = properties_.begin(); it != properties_.end(); it++) {
      printf("%sElement %s:\n", indent, it->first.c_str());
      it->second->display(new_indent);
    }
  }
  /*!
    @brief Get type information as a Python dictionary.
    @returns PyObject* Python dictionary.
   */
  PyObject* as_python_dict() const override {
    PyObject* out = MetaschemaType::as_python_dict();
    PyObject* pyprops = PyDict_New();
    MetaschemaTypeMap::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      PyObject* ipyitem = it->second->as_python_dict();
      set_item_python_dict(pyprops, it->first.c_str(), ipyitem,
			   "JSONObjectMetaschemaType::as_python_dict: properties: ",
			   T_OBJECT);
    }
    set_item_python_dict(out, prop_key_, pyprops,
			 "JSONObjectMetaschemaType::as_python_dict: ",
			 T_OBJECT);
    return out;
  }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const override {
    if (data == NULL) {
      ygglog_throw_error("JSONObjectMetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      YggGenericMap* old_data = (YggGenericMap*)orig_data;
      YggGenericMap* new_data = new YggGenericMap();
      YggGenericMap::iterator it;
      for (it = old_data->begin(); it != old_data->end(); it++) {
      	(*new_data)[it->first] = (it->second)->copy();
      }
      out = (void*)(new_data);
    }
    return out;
  }
  /*!
    @brief Free data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
   */
  void free_generic(YggGeneric* data) const override {
    if (data == NULL) {
      ygglog_throw_error("JSONObjectMetaschemaType::free_generic: Generic object is NULL.");
    }
    YggGenericMap** ptr = (YggGenericMap**)(data->get_data_pointer());
    if (ptr[0] != NULL) {
      YggGenericMap::iterator it;
      for (it = (*ptr)->begin(); it != (*ptr)->end(); it++) {
	delete it->second;
      }
      delete ptr[0];
      ptr[0] = NULL;
    }
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(const YggGeneric* data, const char* indent) const override {
    if (data == NULL) {
      ygglog_throw_error("JSONObjectMetaschemaType::display_generic: Generic object is NULL.");
    }
    YggGenericMap arg;
    YggGenericMap::iterator it;
    char new_indent[100] = "";
    strcat(new_indent, indent);
    strcat(new_indent, "    ");
    data->get_data(arg);
    printf("%sObject with %zu elements:\n", indent, arg.size());
    for (it = arg.begin(); it != arg.end(); it++) {
      std::cout << new_indent << std::left << std::setw(10) << it->first << " ";
      (it->second)->display(new_indent);
    }
  }
  /*!
    @brief Get number of items in type.
    @returns size_t Number of items in type.
   */
  size_t nitems() const { return properties_.size(); }
  /*!
    @brief Get types for properties.
    @returns MetaschemaTypeMap Map from property
    names to types.
   */
  MetaschemaTypeMap properties() const { return properties_; }
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override {
    MetaschemaType::update(new_info);
    JSONObjectMetaschemaType* new_info_obj = (JSONObjectMetaschemaType*)new_info;
    update_properties(new_info_obj->properties());
  }
  /*!
    @brief Update the property types.
    @param[in] new_properties MetaschemaTypeMap Map of new types describing properties.
    @param[in] force bool If true, the existing properties are overwritten, otherwise they are only updated.
   */
  void update_properties(const MetaschemaTypeMap new_properties,
			 bool force=false) {
    if (force) {
      free_properties();
    }
    if (properties_.size() > 0) {
      if (properties_.size() != new_properties.size()) {
	ygglog_throw_error("JSONObjectMetaschemaType::update_properties: Cannot update object with %ld elements from an object with %ld elements.",
			   properties_.size(), new_properties.size());
      }
      MetaschemaTypeMap::iterator it;
      MetaschemaTypeMap::const_iterator new_it;
      for (it = properties_.begin(); it != properties_.end(); it++) {
	new_it = new_properties.find(it->first);
	if (new_it == new_properties.end()) {
	  ygglog_throw_error("JSONObjectMetaschemaType::update_properties: New property map dosn't include old property '%s'.",
			     it->first.c_str());
	}
	if (it->second == NULL) {
	  ygglog_throw_error("JSONObjectMetaschemaType::update_properties: Existing value for property '%s' is NULL.", it->first.c_str());
	} else {
	  it->second->update(new_it->second);
	}
      }
    } else {
      MetaschemaTypeMap::const_iterator it;
      for (it = new_properties.begin(); it != new_properties.end(); it++) {
	if (it->second == NULL) {
	  ygglog_throw_error("JSONObjectMetaschemaType::update_properties: New value for property '%s' is NULL.", it->first.c_str());
	} else {
	  properties_[it->first] = it->second->copy();
	}
      }
    }
    // Force children to follow parent use_generic
    update_use_generic(use_generic());
  }
  /*!
    @brief Update the instance's use_generic flag.
    @param[in] new_use_generic const bool New flag value.
   */
  void update_use_generic(const bool new_use_generic) override {
    MetaschemaType::update_use_generic(new_use_generic);
    // Force children to follow parent use_generic
    MetaschemaTypeMap::iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      if (it->second == NULL) {
	ygglog_throw_error("JSONObjectMetaschemaType::update_use_generic: Value for property %s is NULL.", it->first.c_str());
      } else {
	if ((it->second->type_code() == T_ARRAY) ||
	    (it->second->type_code() == T_OBJECT)) {
	  it->second->update_use_generic(true);
	} else {
	  it->second->update_use_generic(use_generic());
	}
      }
    }
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    size_t iout;
    size_t out = MetaschemaType::update_from_serialization_args(nargs, ap);
    if (use_generic())
      return out;
    MetaschemaTypeMap::const_iterator it;
    size_t new_nargs;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      new_nargs = nargs[0] - out;
      iout = it->second->update_from_serialization_args(&new_nargs, ap);
      if (iout == 0) {
	iout += it->second->nargs_exp();
	// Can't use void* because serialization uses non-pointer arguments
	std::vector<size_t> iva_skip = it->second->nbytes_va();
	if (iva_skip.size() != iout) {
	  ygglog_throw_error("JSONObjectMetaschemaType::update_from_serialization_args: nargs = %lu, size(skip) = %lu",
			     iout, iva_skip.size());
	}
	size_t iskip;
	for (iskip = 0; iskip < iva_skip.size(); iskip++) {
	  va_list_t_skip(&ap, iva_skip[iskip]);
	}
      }
      out = out + iout;
    }
    return out;
  }
  /*!
    @brief Update the type object with info from provided variable arguments for deserialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_deserialization_args(size_t *nargs, va_list_t &ap) override {
    size_t iout;
    size_t out = MetaschemaType::update_from_deserialization_args(nargs, ap);
    if (use_generic())
      return out;
    MetaschemaTypeMap::const_iterator it;
    size_t new_nargs;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      new_nargs = nargs[0] - out;
      iout = it->second->update_from_deserialization_args(&new_nargs, ap);
      if (iout == 0) {
	for (iout = 0; iout < it->second->nargs_exp(); iout++) {
	  // Can use void* here since all variables will be pointers
	  va_arg(ap.va, void*);
	}
      }
      out = out + iout;
    }
    return out;
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    return sizeof(YggGenericMap);
  }
  /*!
    @brief Get the number of bytes occupied by a variable of the type in a variable argument list.
    @returns std::vector<size_t> Number of bytes/variables occupied by the type.
   */
  std::vector<size_t> nbytes_va_core() const override {
    if (!(use_generic())) {
      MetaschemaTypeMap::const_iterator it;
      std::vector<size_t> out;
      std::vector<size_t> iout;
      for (it = properties_.begin(); it != properties_.end(); it++) {
	iout = it->second->nbytes_va();
	out.insert(out.end(), iout.begin(), iout.end());
      }
      return out;
    }
    return MetaschemaType::nbytes_va_core();
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    size_t nargs = 0;
    if (use_generic()) {
      nargs = 1;
    } else {
      MetaschemaTypeMap::const_iterator it;
      for (it = properties_.begin(); it != properties_.end(); it++) {
	nargs = nargs + it->second->nargs_exp();
      }
    }
    return nargs;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject* pyobj) const override {
    if (!(PyDict_Check(pyobj))) {
      ygglog_throw_error("JSONObjectMetaschemaType::python2c: Python object must be a dict.");
    }
    if ((size_t)(PyDict_Size(pyobj)) != nitems()) {
      ygglog_throw_error("JSONObjectMetaschemaType::python2c: Python dict has %lu elements, but the type expects %lu.",
			 PyDict_Size(pyobj), nitems());
    }
    YggGenericMap *cmap = new YggGenericMap();
    MetaschemaTypeMap::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      PyObject *ipy_item = PyDict_GetItemString(pyobj, it->first.c_str());
      if (ipy_item == NULL) {
	ygglog_throw_error("JSONObjectMetaschemaType::python2c: Failed to get item %s out of the Python dict.", it->first.c_str());
      }
      YggGeneric *ic_item = it->second->python2c(ipy_item);
      (*cmap)[it->first] = ic_item;
    }
    YggGeneric* cobj = new YggGeneric(this, cmap);
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric* cobj) const override {
    initialize_python("JSONObjectMetaschemaType::c2python: ");
    PyObject *pyobj = PyDict_New();
    if (pyobj == NULL) {
      ygglog_throw_error("JSONObjectMetaschemaType::c2python: Failed to create new Python dict.");
    }
    YggGenericMap c_map;
    cobj->get_data(c_map);
    if (c_map.size() != nitems()) {
      ygglog_throw_error("JSONObjectMetaschemaType::c2python: Type has %lu elements but object has %lu.", nitems(), c_map.size());
    }
    MetaschemaTypeMap::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      YggGenericMap::iterator ic_item = c_map.find(it->first);
      if (ic_item == c_map.end()) {
	ygglog_throw_error("JSONObjectMetaschemaType::c2python: C object does not have element %s.", it->first.c_str());
      }
      PyObject *ipy_item = it->second->c2python(ic_item->second);
      if (PyDict_SetItemString(pyobj, it->first.c_str(), ipy_item) < 0) {
	ygglog_throw_error("JSONObjectMetaschemaType::c2python: Error setting item %s in the Python dict.", it->first.c_str());
      }
    }
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
    writer->Key(prop_key_);
    writer->StartObject();
    MetaschemaTypeMap::const_iterator it = properties_.begin();
    for (it = properties_.begin(); it != properties_.end(); it++) {
      writer->Key(it->first.c_str());
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
    writer->StartObject();
    MetaschemaTypeMap::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      writer->Key(it->first.c_str());
      if (!(it->second->encode_data_wrap(writer, nargs, ap)))
	return false;
    }
    writer->EndObject();
    return true;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] arg YggGenericMap Mapping between keys and generic wrappers.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGenericMap arg) const {
    writer->StartObject();
    MetaschemaTypeMap::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      YggGenericMap::iterator iarg = arg.find(it->first);
      if (iarg == arg.end()) {
	ygglog_throw_error("JSONObjectMetaschemaType::encode_data: Object does not have element %s.", it->first.c_str());
	return false;
      }
      writer->Key(it->first.c_str());
      if (!(it->second->encode_data(writer, iarg->second)))
	return false;
    }
    writer->EndObject();
    return true;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGeneric* x) const override {
    YggGenericMap arg;
    x->get_data(arg);
    return encode_data(writer, arg);
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
    if (!(data.IsObject())) {
      ygglog_error("JSONObjectMetaschemaType::decode_data: Raw data is not an object.");
      return false;
    }
    MetaschemaTypeMap::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      if (!(data.HasMember(it->first.c_str()))) {
	ygglog_error("JSONObjectMetaschemaType::decode_data: Data doesn't have member '%s'.",
		     it->first.c_str());
	return false;
      }
      if (!(it->second->decode_data_wrap(data[it->first.c_str()], allow_realloc, nargs, ap)))
	return false;
    }
    return true;
  }
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[out] x YggGeneric* Pointer to generic object where data should be stored.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, YggGeneric* x) const override {
    if (!(data.IsObject())) {
      ygglog_error("JSONObjectMetaschemaType::decode_data: Raw data is not an object.");
      return false;
    }
    if (x == NULL) {
      ygglog_error("JSONObjectMetaschemaType::decode_data: Generic object is NULL.");
      return false;
    }
    MetaschemaTypeMap::const_iterator it;
    YggGenericMap** arg = (YggGenericMap**)(x->get_data_pointer());
    if (arg == NULL) {
      ygglog_error("JSONObjectMetaschemaType::decode_data: Data pointer is NULL.");
      return false;
    }
    if (arg[0] == NULL) {
      arg[0] = new YggGenericMap();
      for (it = properties_.begin(); it != properties_.end(); it++) {
	(**arg)[it->first] = (new YggGeneric(it->second, NULL, 0));
      }
    } else if ((arg[0])->size() == 0) {
      for (it = properties_.begin(); it != properties_.end(); it++) {
	(**arg)[it->first] = (new YggGeneric(it->second, NULL, 0));
      }
    }
    for (it = properties_.begin(); it != properties_.end(); it++) {
      if (!(data.HasMember(it->first.c_str()))) {
	ygglog_error("JSONObjectMetaschemaType::decode_data: Data doesn't have member '%s'.",
		     it->first.c_str());
	return false;
      }
      YggGenericMap::iterator iarg = (*arg)->find(it->first);
      if (iarg == (*arg)->end()) {
	ygglog_error("JSONObjectMetaschemaType::decode_data: Destination dosn't have member '%s'.", it->first.c_str());
	return false;
      }
      if (!(it->second->decode_data(data[it->first.c_str()], iarg->second)))
	return false;
    }
    return true;
  }

private:
  char prop_key_[100];
  MetaschemaTypeMap properties_;
};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
//}
#endif

#endif /*JSON_OBJECT_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
