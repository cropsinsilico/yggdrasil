#ifndef JSON_ARRAY_METASCHEMA_TYPE_H_
#define JSON_ARRAY_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Class for describing JSON arrays.

  The JSONArrayMetaschemaType provides basic functionality for encoding/decoding
  JSON array datatypes from/to JSON style strings.
 */
class JSONArrayMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for JSONArrayMetaschemaType.
    @param[in] items std::vector<MetaschemaType*> Type classes for array items.
    @param[in] format_str const char * (optional) Format string describing the
    item types. Defaults to empty string.
  */
  JSONArrayMetaschemaType(const std::vector<MetaschemaType*> items,
			  const char *format_str = "") :
    MetaschemaType("array") {
    strncpy(format_str_, format_str, 1000);
    update_items(items, true);
  }
  /*!
    @brief Destructor for JSONArrayMetaschemaType.
    Free the type string malloc'd during constructor.
   */
  ~JSONArrayMetaschemaType() {
    items_.clear();
  }
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  bool operator==(const MetaschemaType &Ref) const override {
    if (!(MetaschemaType::operator==(Ref)))
      return false;
    const JSONArrayMetaschemaType* pRef = dynamic_cast<const JSONArrayMetaschemaType*>(&Ref);
    if (!pRef)
      return false;
    if (nitems() != pRef->nitems())
      return false;
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      if (*(items_[i]) != *(pRef->items()[i])) {
	return false;
      }
    }
    return true;
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new JSONArrayMetaschemaType instance with the same data.
   */
  JSONArrayMetaschemaType* copy() const override { return (new JSONArrayMetaschemaType(items_, format_str_)); }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() const override {
    MetaschemaType::display();
    if (strlen(format_str_) > 0) {
      printf("format_str = %s\n", format_str_);
    }
    printf("%lu Elements\n", items_.size());
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      printf("Element %lu:\n", i);
      items_[i]->display();
    }
  }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(YggGeneric* data, void* orig_data=NULL) const override {
    if (data == NULL) {
      ygglog_throw_error("JSONArrayMetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      YggGenericVector* old_data = (YggGenericVector*)orig_data;
      YggGenericVector* new_data = new YggGenericVector();
      YggGenericVector::iterator it;
      for (it = old_data->begin(); it != old_data->end(); it++) {
      	new_data->push_back((*it)->copy());
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
      ygglog_throw_error("JSONArrayMetaschemaType::free_generic: Generic object is NULL.");
    }
    YggGenericVector** ptr = (YggGenericVector**)(data->get_data_pointer());
    if (ptr[0] != NULL) {
      YggGenericVector::iterator it;
      for (it = (*ptr)->begin(); it != (*ptr)->end(); it++) {
	delete *it;
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
  void display_generic(YggGeneric* data, const char* indent) const override {
    if (data == NULL) {
      ygglog_throw_error("JSONArrayMetaschemaType::display_generic: Generic object is NULL.");
    }
    YggGenericVector arg;
    YggGenericVector::const_iterator it;
    char new_indent[100] = "";
    strcat(new_indent, indent);
    strcat(new_indent, "    ");
    data->get_data(arg);
    printf("%sArray with %lu elements:\n", indent, arg.size());
    for (it = arg.begin(); it != arg.end(); it++) {
      (*it)->display(new_indent);
    }
  }
  /*!
    @brief Get number of items in type.
    @returns size_t Number of items in type.
   */
  size_t nitems() const { return items_.size(); }
  /*!
    @brief Get types for items.
    @returns std::vector<MetaschemaType*> Array item types.
   */
  std::vector<MetaschemaType*> items() const { return items_; }
  /*!
    @brief Determine if the items are all arrays.
    @returns bool true if all items are arrays, false otherwise.
   */
  bool all_arrays() const {
    bool out = true;
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      if (strcmp(items_[i]->type(), "1darray") != 0) {
	out = false;
	break;
      }
    }
    return out;
  }
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override {
    MetaschemaType::update(new_info);
    JSONArrayMetaschemaType* new_info_array = (JSONArrayMetaschemaType*)new_info;
    update_items(new_info_array->items());
  }
  /*!
    @brief Update the item types.
    @param[in] new_items std::vector<MetaschemaType*> Vector of new types describing items.
    @param[in] force bool If true, the existing items are overwritten, otherwise they are only updated.
   */
  void update_items(const std::vector<MetaschemaType*> new_items,
		    bool force=false) {
    size_t i;
    if (force) {
      items_.clear();
    }
    if (items_.size() > 0) {
      if (items_.size() != new_items.size()) {
	ygglog_throw_error("JSONArrayMetaschemaType::update_items: Cannot update array with %ld elements from an array with %ld elements.",
			   items_.size(), new_items.size());
      }
      for (i = 0; i < items_.size(); i++) {
	items_[i]->update(new_items[i]);
      }
    } else {
      for (i = 0; i < new_items.size(); i++) {
	items_.push_back(new_items[i]->copy());
      }
    }
    
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
   */
  void update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    MetaschemaType::update_from_serialization_args(nargs, ap);
    if ((all_arrays()) && (*nargs == (nitems() + 1))) {
      size_t nrows = va_arg(ap.va, size_t);
      (*nargs)--;
      size_t i;
      for (i = 0; i < items_.size(); i++) {
	if (items_[i]->type_code() != T_1DARRAY) {
	  ygglog_throw_error("JSONArrayMetaschemaType::update_from_serialization_args: "
			     "Item %lu is of type %s, but the all_arrays"
			     "parameter is set, indicating it should "
			     "be \"1darray\".", i, items_[i]->type());
	}
	items_[i]->set_length(nrows);
      }
    }
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    return sizeof(YggGenericVector);
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    size_t nargs = 0;
    if (all_arrays())
      nargs++; // For the number of rows
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      nargs = nargs + items_[i]->nargs_exp();
    }
    return nargs;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject* pyobj) const override {
    if (!(PyList_Check(pyobj))) {
      ygglog_throw_error("JSONArrayMetaschemaType::python2c: Python object must be a list.");
    }
    if (PyList_Size(pyobj) != nitems()) {
      ygglog_throw_error("JSONArrayMetaschemaType::python2c: Python list has %lu elements, but the type expects %lu.",
			 PyList_Size(pyobj), nitems());
    }
    size_t i;
    YggGenericVector *citems = new YggGenericVector();
    for (i = 0; i < nitems(); i++) {
      PyObject *ipy_item = PyList_GetItem(pyobj, (Py_ssize_t)i);
      if (ipy_item == NULL) {
	ygglog_throw_error("JSONArrayMetaschemaType::python2c: Failed to get item %lu out of the Python list.", i);
      }
      YggGeneric *ic_item = items_[i]->python2c(ipy_item);
      citems->push_back(ic_item);
    }
    YggGeneric* cobj = new YggGeneric(this, citems);
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric* cobj) const override {
    initialize_python("JSONArrayMetaschemaType::c2python: ");
    PyObject *pyobj = PyList_New((Py_ssize_t)(nitems()));
    if (pyobj == NULL) {
      ygglog_throw_error("JSONArrayMetaschemaType::c2python: Failed to create new Python list.");
    }
    YggGenericVector c_items;
    cobj->get_data(c_items);
    if (c_items.size() != nitems()) {
      ygglog_throw_error("JSONArrayMetaschemaType::c2python: Type has %lu elements but object has %lu.", nitems(), c_items.size());
    }
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      PyObject *iitem = items_[i]->c2python(c_items[i]);
      if (PyList_SetItem(pyobj, (Py_ssize_t)i, iitem) < 0) {
	ygglog_throw_error("JSONArrayMetaschemaType::c2python: Error setting item %lu in the Python list.", i);
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
    if (strlen(format_str_) > 0) {
      writer->Key("format_str");
      writer->String(format_str_, strlen(format_str_));
    }
    writer->Key("items");
    writer->StartArray();
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      if (!(items_[i]->encode_type(writer)))
	return false;
    }
    writer->EndArray();
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
    size_t i;
    writer->StartArray();
    for (i = 0; i < items_.size(); i++) {
      if (!(items_[i]->encode_data(writer, nargs, ap)))
	return false;
    }
    writer->EndArray();
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
    size_t i;
    YggGenericVector arg;
    x->get_data(arg);
    if (arg.size() != items_.size()) {
      ygglog_throw_error("JSONArrayMetaschemaType::encode_data: Type has %d elements, but object has %d.", items_.size(), arg.size());
      return false;
    }
    if (all_arrays()) {
      size_t nrows = arg[0]->get_nelements();
      for (i = 0; i < items_.size(); i++) {
	if (items_[i]->nelements() != nrows) {
	  ygglog_throw_error("JSONArrayMetaschemaType::encode_data: Element %lu has %lu elements but all array entries are expected to have %lu elements.",
			     i, items_[i]->nelements(), nrows);
	}
      }
    }
    writer->StartArray();
    for (i = 0; i < items_.size(); i++) {
      if (!(items_[i]->encode_data(writer, arg[i])))
	return false;
    }
    writer->EndArray();
    return true;
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
    size_t i;
    if (all_arrays()) {
      size_t *nrows = va_arg(ap.va, size_t*);
      size_t inrows;
      (*nargs)--;
      *nrows = items_[0]->nelements();
      for (i = 1; i < items_.size(); i++) {
	inrows = items_[i]->nelements();
	if (*nrows != inrows) {
	  ygglog_error("JSONArrayMetaschemaType::decode_data: Number of rows not consistent across all items.");
	  return false;
	}
      }
    }
    if (!(data.IsArray())) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: Raw data is not an array.");
      return false;
    }
    if (data.Size() != items_.size()) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: %lu items expected, but %lu found.",
		   items_.size(), data.Size());
      return false;
    }
    for (i = 0; i < (size_t)(items_.size()); i++) {
      if (!(items_[i]->decode_data(data[i], allow_realloc, nargs, ap)))
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
    size_t i;
    if (all_arrays()) {
      size_t inrows;
      size_t nrows = items_[0]->nelements();
      for (i = 1; i < items_.size(); i++) {
	inrows = items_[i]->nelements();
	if (nrows != inrows) {
	  ygglog_error("JSONArrayMetaschemaType::decode_data: Number of rows not consistent across all items.");
	  return false;
	}
      }
    }
    if (!(data.IsArray())) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: Raw data is not an array.");
      return false;
    }
    if (data.Size() != items_.size()) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: %lu items expected, but %lu found.",
		   items_.size(), data.Size());
      return false;
    }
    YggGenericVector** arg = (YggGenericVector**)(x->get_data_pointer());
    if (arg[0] == NULL) {
      arg[0] = new YggGenericVector();
      for (i = 0; i < (size_t)(items_.size()); i++) {
	arg[0]->push_back((new YggGeneric(items_[i], NULL, 0)));
      }
    }
    if (items_.size() != (arg[0])->size()) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: %lu items found, but destination has %lu.",
		   items_.size(), (arg[0])->size());
      return false;
    }
    
    for (i = 0; i < (size_t)(items_.size()); i++) {
      if (!(items_[i]->decode_data(data[i], (**arg)[i])))
	return false;
    }
    return true;
  }

private:
  std::vector<MetaschemaType*> items_;
  char format_str_[1000];
};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
//}
#endif

#endif /*JSON_ARRAY_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
