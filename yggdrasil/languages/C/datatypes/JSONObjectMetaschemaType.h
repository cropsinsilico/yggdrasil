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
    @param[in] properties std::map<const char*, MetaschemaType*, strcomp> Map from
    property names to types.
  */
  JSONObjectMetaschemaType(const std::map<const char*, MetaschemaType*, strcomp> properties) :
    MetaschemaType("object") {
    update_properties(properties, true);
  }
  /*!
    @brief Destructor for JSONObjectMetaschemaType.
    Free the type string malloc'd during constructor.
   */
  ~JSONObjectMetaschemaType() {
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
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator oit;
    std::map<const char*, MetaschemaType*, strcomp> new_properties = pRef->properties();
    size_t i = 0;
    for (it = properties_.begin(); it != properties_.end(); it++, i++) {
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
    @brief Create a copy of the type.
    @returns pointer to new JSONObjectMetaschemaType instance with the same data.
   */
  JSONObjectMetaschemaType* copy() const override { return (new JSONObjectMetaschemaType(properties_)); }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() const override {
    MetaschemaType::display();
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      printf("Element %s:\n", it->first);
      it->second->display();
    }
  }
  /*!
    @brief Display data.
    @param[in] x YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(YggGeneric* x, const char* indent) const override {
    YggGenericMap arg;
    YggGenericMap::iterator it;
    char new_indent[100] = "";
    strcat(new_indent, indent);
    strcat(new_indent, "    ");
    x->get_data(arg);
    printf("%sObject with %lu elements:\n", indent, arg.size());
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
    @returns std::map<const char*, MetaschemaType*, strcomp> Map from property
    names to types.
   */
  std::map<const char*, MetaschemaType*, strcomp> properties() const { return properties_; }
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
    @param[in] new_properties std::map<const char*, MetaschemaType*, strcomp> Map of new types describing properties.
    @param[in] force bool If true, the existing properties are overwritten, otherwise they are only updated.
   */
  void update_properties(const std::map<const char*, MetaschemaType*, strcomp> new_properties,
			 bool force=false) {
    if (force) {
      properties_.clear();
    }
    if (properties_.size() > 0) {
      if (properties_.size() != new_properties.size()) {
	ygglog_throw_error("JSONObjectMetaschemaType::update_properties: Cannot update object with %ld elements from an object with %ld elements.",
			   properties_.size(), new_properties.size());
      }
      std::map<const char*, MetaschemaType*, strcomp>::iterator it;
      std::map<const char*, MetaschemaType*, strcomp>::const_iterator new_it;
      for (it = properties_.begin(); it != properties_.end(); it++) {
	new_it = new_properties.find(it->first);
	if (new_it == new_properties.end()) {
	  ygglog_throw_error("JSONObjectMetaschemaType::update_properties: New property map dosn't include old property '%s'.",
			     it->first);
	}
	it->second->update(new_it->second);
      }
    } else {
      std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
      for (it = new_properties.begin(); it != new_properties.end(); it++) {
	properties_[it->first] = it->second->copy();
      }
    }
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    return sizeof(YggGenericMap);
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    size_t nargs = 0;
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      nargs = nargs + it->second->nargs_exp();
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
    if (PyDict_Size(pyobj) != nitems()) {
      ygglog_throw_error("JSONObjectMetaschemaType::python2c: Python dict has %lu elements, but the type expects %lu.",
			 PyDict_Size(pyobj), nitems());
    }
    YggGenericMap *cmap = new YggGenericMap();
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      PyObject *ipy_item = PyDict_GetItemString(pyobj, it->first);
      if (ipy_item == NULL) {
	ygglog_throw_error("JSONObjectMetaschemaType::python2c: Failed to get item %s out of the Python dict.", it->first);
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
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      YggGenericMap::iterator ic_item = c_map.find(it->first);
      if (ic_item == c_map.end()) {
	ygglog_throw_error("JSONObjectMetaschemaType::c2python: C object does not have element %s.", it->first);
      }
      PyObject *ipy_item = it->second->c2python(ic_item->second);
      if (PyDict_SetItemString(pyobj, it->first, ipy_item) < 0) {
	ygglog_throw_error("JSONObjectMetaschemaType::c2python: Error setting item %s in the Python dict.", it->first);
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
    writer->Key("properties");
    writer->StartObject();
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it = properties_.begin();
    for (it = properties_.begin(); it != properties_.end(); it++) {
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
    writer->StartObject();
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    size_t i = 0;
    for (it = properties_.begin(); it != properties_.end(); it++, i++) {
      writer->Key(it->first);
      if (!(it->second->encode_data(writer, nargs, ap)))
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
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    size_t i = 0;
    for (it = properties_.begin(); it != properties_.end(); it++, i++) {
      YggGenericMap::iterator iarg = arg.find(it->first);
      if (iarg == arg.end()) {
	ygglog_throw_error("JSONObjectMetaschemaType::encode_data: Object does not have element %s.", it->first);
	return false;
      }
      writer->Key(it->first);
      // printf("Item %s:\n", it->first);
      // it->second->display();
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
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
    size_t i = 0;
    for (it = properties_.begin(); it != properties_.end(); it++, i++) {
      if (!(data.HasMember(it->first))) {
	ygglog_error("JSONObjectMetaschemaType::decode_data: Data dosn't have member '%s'.",
		     it->first);
	return false;
      }
      if (!(it->second->decode_data(data[it->first], allow_realloc, nargs, ap)))
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
    std::map<const char*, MetaschemaType*, strcomp>::const_iterator it;
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
    }
    for (it = properties_.begin(); it != properties_.end(); it++) {
      if (!(data.HasMember(it->first))) {
	ygglog_error("JSONObjectMetaschemaType::decode_data: Data dosn't have member '%s'.",
		     it->first);
	return false;
      }
      YggGenericMap::iterator iarg = (*arg)->find(it->first);
      if (iarg == (*arg)->end()) {
	ygglog_error("JSONObjectMetaschemaType::decode_data: Destination dosn't have member '%s'.", it->first);
	return false;
      }
      if (!(it->second->decode_data(data[it->first], iarg->second)))
	return false;
    }
    return true;
  }

private:
  std::map<const char*, MetaschemaType*, strcomp> properties_;
};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
//}
#endif

#endif /*JSON_OBJECT_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
