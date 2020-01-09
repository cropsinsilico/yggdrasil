#ifndef METASCHEMA_TYPE_H_
#define METASCHEMA_TYPE_H_

#include "../tools.h"
#include "utils.h"
#include "datatypes.h"

#include <stdexcept>
#include <iostream>
#include <iomanip>
#include <map>
#include <vector>
#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Base class for metaschema type definitions.

  The MetaschemaType provides basic functionality for encoding/decoding
  datatypes from/to JSON style strings.
 */
class MetaschemaType {
public:
  /*!
    @brief Constructor for MetaschemaType.
    @param[in] type const character pointer to the name of the type.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  MetaschemaType(const char* type, const bool use_generic=false,
		 const bool always_generic=false) :
    type_((const char*)malloc(STRBUFF)), type_code_(-1), updated_(false),
    nbytes_(0), use_generic_(use_generic), always_generic_(always_generic) {
    if (always_generic_)
      update_use_generic(true);
    update_type(type);
  }
  /*!
    @brief Constructor for MetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing
    the type definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  MetaschemaType(const rapidjson::Value &type_doc,
		 const bool use_generic=false,
		 const bool always_generic=false) :
    type_((const char*)malloc(STRBUFF)), type_code_(-1), updated_(false),
    nbytes_(0), use_generic_(use_generic), always_generic_(always_generic) {
    if (always_generic_)
      update_use_generic(true);
    if (!(type_doc.IsObject()))
      ygglog_throw_error("MetaschemaType: Parsed document is not an object.");
    if (!(type_doc.HasMember("type")))
      ygglog_throw_error("MetaschemaType: Parsed header dosn't contain a type.");
    if (!(type_doc["type"].IsString()))
      ygglog_throw_error("MetaschemaType: Type in parsed header is not a string.");
    update_type(type_doc["type"].GetString());
  }
  /*!
    @brief Constructor for MetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  MetaschemaType(PyObject* pyobj, const bool use_generic=false,
		 const bool always_generic=false) :
    type_((const char*)malloc(STRBUFF)), type_code_(-1), updated_(false),
    nbytes_(0), use_generic_(use_generic), always_generic_(always_generic) {
    if (always_generic_)
      update_use_generic(true);
    if (!(PyDict_Check(pyobj))) {
      ygglog_throw_error("MetaschemaType: Python object must be a dict.");
    }
    char ctype[STRBUFF] = "";
    get_item_python_dict_c(pyobj, "type", ctype,
			   "MetaschemaType: type: ",
			   T_STRING, STRBUFF);
    update_type(ctype);
  }
  /*!
    @brief Copy constructor.
    @param[in] other MetaschemaType* Instance to copy.
   */
  MetaschemaType(const MetaschemaType &other) :
    MetaschemaType(other.type(), other.use_generic()) {}
  /*!
    @brief Destructor for MetaschemaType.
    Free the type string malloc'd during constructor.
   */
  virtual ~MetaschemaType() {
    free((char*)type_);
  }
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  virtual bool operator==(const MetaschemaType &Ref) const {
    if (strcmp(type_, Ref.type()) != 0)
      return false;
    if (type_code_ != Ref.type_code())
      return false;
    return true;
  }
  /*!
    @brief Inequivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instances are not equivalent, false otherwise.
   */
  virtual bool operator!=(const MetaschemaType &Ref) const {
    if (operator==(Ref))
      return false;
    else
      return true;
  }
  /*!
    @brief Determine if the datatype is effectively empty.
    @returns bool true if the datatype is empty, false otherwise.
   */
  virtual bool is_empty() const {
    return false;
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new MetaschemaType instance with the same data.
   */
  virtual MetaschemaType* copy() const {
    return (new MetaschemaType(type_, use_generic_));
  }
  /*!
    @brief Print information about the type to stdout.
    @param[in] indent char* Indentation to add to display output.
  */
  virtual void display(const char* indent="") const {
    printf("%s%-15s = %s\n", indent, "type", type_);
    printf("%s%-15s = %d\n", indent, "type_code", type_code_);
    printf("%s%-15s = %d\n", indent, "use_generic", use_generic_);
  }
  /*!
    @brief Get type information as a Python dictionary.
    @returns PyObject* Python dictionary.
   */
  virtual PyObject* as_python_dict() const {
    PyObject* out = PyDict_New();
    set_item_python_dict_c(out, "type", type_,
			   "MetaschemaType::as_python_dict: type: ",
			   T_STRING, STRBUFF);
    return out;
  }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  virtual void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const {
    if (data == NULL) {
      ygglog_throw_error("MetaschemaType::copy_generic: Generic object is NULL.");
    }
    void* out = NULL;
    if (orig_data == NULL) {
      orig_data = data->get_data();
    }
    if (orig_data != NULL) {
      size_t nbytes_data = data->get_nbytes();
      void* temp = (void*)realloc(out, nbytes_data);
      if (temp == NULL) {
	ygglog_throw_error("MetaschemaType::copy_generic: Failed to realloc output pointer.");
      }
      out = temp;
      memcpy(out, orig_data, nbytes_data);
    }
    return out;
  }
  /*!
    @brief Free data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
   */
  virtual void free_generic(YggGeneric* data) const {
    if (data == NULL) {
      ygglog_throw_error("MetaschemaType::free_generic: Generic object is NULL.");
    }
    void** ptr = data->get_data_pointer();
    if (ptr[0] != NULL) {
      free(ptr[0]);
      ptr[0] = NULL;
    }
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  virtual void display_generic(const YggGeneric* data, const char* indent="") const {
    if (data == NULL) {
      ygglog_throw_error("MetaschemaType::display_generic: Generic object is NULL.");
    }
    const MetaschemaType* data_type = data->get_type();
    std::cout << indent;
    switch (data_type->type_code()) {
    case T_BOOLEAN: {
      bool arg = false;
      data->get_data(arg);
      if (arg)
	std::cout << "true" << std::endl;
      else
	std::cout << "false" << std::endl;
      return;
    }
    case T_INTEGER: {
      int arg = 0;
      data->get_data(arg);
      std::cout << arg << std::endl;
      return;
    }
    case T_NULL: {
      std::cout << "NULL" << std::endl;
      return;
    }
    case T_NUMBER: {
      double arg = 0.0;
      data->get_data(arg);
      std::cout << arg << std::endl;
      return;
    }
    case T_STRING: {
      char* arg = (char*)(data->get_data());
      std::cout << arg << std::endl;
      return;
    }
    }
    ygglog_throw_error("MetaschemaType::display_generic: Cannot display type '%s'.", data_type->type());
  }
  /*!
    @brief Check that the type is correct and get the corresponding code.
    @returns int Type code for the instance's type.
   */
  int check_type() const {
    std::map<const char*, int, strcomp> type_map = get_type_map();
    std::map<const char*, int, strcomp>::iterator it = type_map.find(type_);
    if (it == type_map.end()) {
      ygglog_throw_error("MetaschemaType: Unsupported type '%s'.", type_);
    }
    return it->second;
  }
  /*!
    @brief Get the type string.
    @returns const char pointer to the type string.
   */
  const char* type() const { return type_; }
  /*!
    @brief Get the type code.
    @returns int Type code associated with the curent type.
   */
  const int type_code() const { return type_code_; }
  /*!
    @brief Get the value of class attribute use_generic.
    @returns bool Value of use_generic.
   */
  const bool use_generic() const { return use_generic_; }
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  virtual void update(const MetaschemaType* new_info) {
    if (new_info == NULL) {
      ygglog_throw_error("MetaschemaType::update: New type information is NULL.");
    }
    if (strcmp(type_, new_info->type()) != 0) {
      ygglog_throw_error("MetaschemaType::update: Cannot update type %s to type %s.",
			 type_, new_info->type());
    }
    updated_ = true;
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  virtual size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) {
    skip_before_.clear();
    skip_after_.clear();
    if (use_generic()) {
      generic_t gen_arg = pop_generic(nargs, ap, true);
      update_from_serialization_args((YggGeneric*)(gen_arg.obj));
      return 1;
    } else {
      switch (type_code_) {
      case T_BOOLEAN:
      case T_INTEGER: {
	va_arg(ap.va, int);
	return 1;
      }
      case T_NULL: {
	va_arg(ap.va, void*);
	return 1;
      }
      case T_NUMBER: {
	va_arg(ap.va, double);
	return 1;
      }
      case T_STRING: {
	va_arg(ap.va, char*);
	va_arg(ap.va, size_t);
	return 2;
      }
      }
    }
    return 0;
  }
  /*!
    @brief Update the type object with info from provided variable arguments for deserialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  virtual size_t update_from_deserialization_args(size_t *nargs, va_list_t &ap) {
    skip_before_.clear();
    skip_after_.clear();
    if (use_generic()) {
      generic_t* gen_arg = pop_generic_ptr(nargs, ap, true);
      update_from_deserialization_args((YggGeneric*)(gen_arg->obj));
      return 1;
    }
    return 0;
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in] x YggGeneric* Pointer to generic object containing data to be serialized.
   */
  virtual void update_from_serialization_args(YggGeneric* x) {
    update(x->get_type());
  }
  /*!
    @brief Update the type object with info from provided variable arguments for deserialization.
    @param[in,out] x YggGeneric* Pointer to generic object where data will be stored.
   */
  virtual void update_from_deserialization_args(YggGeneric* x) {
    x->get_type()->update(this);
  }
  /*!
    @brief Update the instance's type.
    @param[in] new_type const char * String for new type.
   */
  virtual void update_type(const char* new_type) {
    char** type_modifier = const_cast<char**>(&type_);
    strncpy(*type_modifier, new_type, STRBUFF);
    int* type_code_modifier = const_cast<int*>(&type_code_);
    *type_code_modifier = check_type();
  }
  /*!
    @brief Update the instance's use_generic flag.
    @param[in] new_use_generic const bool New flag value.
   */
  virtual void update_use_generic(const bool new_use_generic) {
    bool* use_generic_modifier = const_cast<bool*>(&use_generic_);
    if (always_generic_)
      *use_generic_modifier = true;
    else
      *use_generic_modifier = new_use_generic;
  }
  /*!
    @brief Set the type length.
    @param[in] new_length size_t New length.
   */
  virtual void set_length(size_t new_length, bool force=false) {
    // This virtual class is required to allow setting lengths
    // for table style type where data is an array of 1darrays.
    // Otherwise circular include results as scalar requires
    // JSON array for checking if there is a single element.
    // Prevent C4100 warning on windows by referencing param
    UNUSED(new_length);
    UNUSED(force);
    ygglog_throw_error("MetaschemaType::set_length: Cannot set length for type '%s'.", type_);
  }
  /*!
    @brief Set the _variable_length private variable.
    @param[in] new_variable_length bool New value.
   */
  virtual void set_variable_length(bool new_variable_length) {
#ifdef _WIN32
    new_variable_length;
#endif 
    ygglog_throw_error("MetaschemaType::set_variable_length: Cannot set variable_length for type '%s'.", type_);
  }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements (1 for scalar).
   */
  virtual const size_t nelements() const { return 1; }
  /*!
    @brief Determine if the number of elements is variable.
    @returns bool true if the number of elements can change, false otherwise.
  */
  virtual const bool variable_nelements() const { return false; }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  virtual const size_t nbytes() const {
    switch (type_code_) {
    case T_BOOLEAN: {
      return sizeof(bool);
    }
    case T_INTEGER: {
      return sizeof(int);
    }
    case T_NULL: {
      return sizeof(NULL);
    }
    case T_NUMBER: {
      return sizeof(double);
    }
    case T_STRING: {
      if (nbytes_ == 0) {
	ygglog_throw_error("MetaschemaType::nbytes: String cannot have size of 0.");
      } else {
	return nbytes_;
      }
    }
    }
    ygglog_throw_error("MetaschemaType::nbytes: Cannot get number of bytes for type '%s'.", type_);
    return 0;
  }
  /*!
    @brief Get the number of bytes occupied by a variable of the type in a variable argument list.
    @returns std::vector<size_t> Number of bytes/variables occupied by the type.
   */
  virtual std::vector<size_t> nbytes_va_core() const {
    std::vector<size_t> out;
    if (use_generic()) {
      out.push_back(sizeof(generic_t));
    } else {   
      switch (type_code_) {
      case T_NULL: {
	out.push_back(sizeof(void*));
	break;
      }	
      case T_STRING: {
	out.push_back(sizeof(char*));
	out.push_back(sizeof(size_t));
	break;
      }
      default: {
	out.push_back(nbytes());
      }
      }
    }
    return out;
  }
  /*!
    @brief Get the number of bytes occupied by a variable of the type in a variable argument list.
    @returns std::vector<size_t> Number of bytes/variables occupied by the type.
   */
  std::vector<size_t> nbytes_va() const {
    std::vector<size_t> out = nbytes_va_core();
    out.insert(out.begin(), skip_before_.begin(), skip_before_.end());
    out.insert(out.end(), skip_after_.begin(), skip_after_.end());
    return out;
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  virtual size_t nargs_exp() const {
    switch (type_code_) {
    case T_BOOLEAN:
    case T_INTEGER:
    case T_NULL:
    case T_NUMBER: {
      return 1;
    }
    case T_STRING: {
      // Add length of sting to be consistent w/ bytes and unicode types
      return 2;
    }
    }
    ygglog_throw_error("MetaschemaType::nargs_exp: Cannot get number of expected arguments for type '%s'.", type_);
    return 0;
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  virtual YggGeneric* python2c(PyObject* pyobj) const {
    YggGeneric* cobj = new YggGeneric(this, NULL, 0);
    void** data = cobj->get_data_pointer();
    void* idata = (void*)realloc(data[0], nbytes());
    if (idata == NULL) {
      ygglog_throw_error("MetaschemaType::python2c: Failed to realloc data.");
    }
    void *dst = idata;
    size_t precision = 0;
    switch (type_code_) {
    case T_BOOLEAN: {
      precision = 8;
      break;
    }
    case T_INTEGER: {
      precision = 8*sizeof(int);
      break;
    }
    case T_NULL: {
      break;
    }
    case T_NUMBER: {
      precision = 8*sizeof(double);
      break;
    }
    case T_STRING: {
      dst = (void*)(&idata);
      break;
    }
    default: {
      ygglog_throw_error("MetaschemaType::python2c: Cannot convert type '%s'.", type_);
    }
    }
    convert_python2c(pyobj, dst, type_code_,
		     "MetaschemaType::python2c: ",
		     precision);
    if (type_code_ == T_STRING) {
      cobj->set_nbytes(strlen((char*)idata));
    }
    data[0] = idata;
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  virtual PyObject* c2python(YggGeneric *cobj) const {
    PyObject *pyobj = NULL;
    void *src = cobj->get_data();
    size_t precision = 0;
    switch (type_code_) {
    case T_BOOLEAN: {
      precision = 8*sizeof(bool);
      break;
    }
    case T_INTEGER: {
      precision = 8*sizeof(int);
      break;
    }
    case T_NULL: {
      break;
    }
    case T_NUMBER: {
      precision = 8*sizeof(double);
      break;
    }
    case T_STRING: {
      src = (void*)(cobj->get_data_pointer());
      break;
    }
    default: {
      ygglog_throw_error("MetaschemaType::c2python: Cannot convert type '%s'.", type_);
    }
    }
    pyobj = convert_c2python(src, type_code_,
			     "MetaschemaType::c2python: ",
			     precision);
    return pyobj;
  }
  /*!
    @brief Return the recovered generic structure if one is present in
    the variable argument list by removing it.
    @param[in] nargs size_t* Pointer to number of arguments present in ap
    that will be decremented by 1.
    @param[in] ap va_list_t Variable argument list.
    @returns generic_t Generic structure if one is present.
  */
  generic_t pop_generic(size_t* nargs, va_list_t &ap, bool skip_nargs_dec=false) const {
    if (skip_nargs_dec)
      (*nargs)++;
    generic_t gen_arg = pop_generic_va(nargs, &ap);
    if (!(is_generic_init(gen_arg))) {
      ygglog_throw_error("MetaschemaType::pop_generic: Type expects generic object, but one was not provided.");
    }
    return gen_arg;
  }
  /*!
    @brief Return the recovered generic structure if one is present in
    the variable argument list by removing it.
    @param[in] nargs size_t* Pointer to number of arguments present in ap
    that will be decremented by 1.
    @param[in] ap va_list_t Variable argument list.
    @param[in] skip_nargs_dec bool If true, nargs will not be modified.
    Defaults to false.
    @returns generic_t* Generic structure if one is present, NULL otherwise.
  */
  generic_t* pop_generic_ptr(size_t* nargs, va_list_t &ap, bool skip_nargs_dec=false) const {
    if (skip_nargs_dec)
      (*nargs)++;
    generic_t* gen_arg = pop_generic_va_ptr(nargs, &ap);
    if (gen_arg == NULL) {
      ygglog_throw_error("MetaschemaType::pop_generic_ptr: Type expects pointer to generic object, but one was not provided.");
    }
    if (gen_arg->obj == NULL) {
      gen_arg->obj = (void*)(new YggGeneric(this, NULL, 0));
    }
    return gen_arg;
  }
  
  // Encoding
  /*!
    @brief Encode the type in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type(rapidjson::Writer<rapidjson::StringBuffer> *writer) const {
    writer->StartObject();
    if (!(encode_type_prop(writer)))
      return false;
    writer->EndObject();
    return true;
  }
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  virtual bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const {
    writer->Key("type");
    writer->String(type_, (rapidjson::SizeType)strlen(type_));
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
  virtual bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
			   size_t *nargs, va_list_t &ap) const {
    if (nargs_exp() > *nargs)
      ygglog_throw_error("MetaschemaType::encode_data: %d arguments expected, but only %d provided.",
			 nargs_exp(), *nargs);
    switch (type_code_) {
    case T_BOOLEAN: {
      int arg = va_arg(ap.va, int);
      (*nargs)--;
      if (arg == 0)
	writer->Bool(false);
      else
	writer->Bool(true);
      return true;
    }
    case T_INTEGER: {
      int arg = va_arg(ap.va, int);
      (*nargs)--;
      writer->Int(arg);
      return true;
    }
    case T_NULL: {
      va_arg(ap.va, void*);
      (*nargs)--;
      writer->Null();
      return true;
    }
    case T_NUMBER: {
      double arg = va_arg(ap.va, double);
      (*nargs)--;
      writer->Double(arg);
      return true;
    }
    case T_STRING: {
      char* arg = va_arg(ap.va, char*);
      size_t arg_siz = va_arg(ap.va, size_t);
      (*nargs)--;
      (*nargs)--;
      writer->String(arg, (rapidjson::SizeType)arg_siz);
      return true;
    }
    }
    ygglog_error("MetaschemaType::encode_data: Cannot encode data of type '%s'.", type_);
    return false;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in,out] nargs size_t * Pointer to the number of arguments contained in
    ap. On return it will be set to the number of arguments used.
    @param[in] ... Variable number of arguments that should be encoded
    as a JSON string.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, ...) const {
    va_list_t ap_s;
    va_start(ap_s.va, nargs);
    bool out = encode_data(writer, nargs, ap_s);
    va_end(ap_s.va);
    return out;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string
    first checking if the arguments should be generic.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in,out] nargs size_t * Pointer to the number of arguments contained in
    ap. On return it will be set to the number of arguments used.
    @param[in] ap va_list_t Variable number of arguments that should be encoded
    as a JSON string.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data_wrap(rapidjson::Writer<rapidjson::StringBuffer> *writer,
			size_t *nargs, va_list_t &ap) const {
    bool out;
    size_t i;
    for (i = 0; i < skip_before_.size(); i++) {
      va_list_t_skip(&ap, skip_before_[i]);
      (*nargs)--;
    }
    if (use_generic()) {
      generic_t gen_arg = pop_generic(nargs, ap);
      out = encode_data(writer, (YggGeneric*)(gen_arg.obj));
    } else {
      out = encode_data(writer, nargs, ap);
    }
    for (i = 0; i < skip_after_.size(); i++) {
      va_list_t_skip(&ap, skip_after_[i]);
      (*nargs)--;
    }
    return out;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string
    first checking if the arguments should be generic.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in,out] nargs size_t * Pointer to the number of arguments contained in
    ap. On return it will be set to the number of arguments used.
    @param[in] ... Variable number of arguments that should be encoded
    as a JSON string.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data_wrap(rapidjson::Writer<rapidjson::StringBuffer> *writer,
			size_t *nargs, ...) const {
    va_list_t ap_s;
    va_start(ap_s.va, nargs);
    bool out = encode_data_wrap(writer, nargs, ap_s);
    va_end(ap_s.va);
    return out;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  virtual bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
			   YggGeneric* x) const {
    size_t nargs = 1;
    switch (type_code_) {
    case T_BOOLEAN: {
      bool arg = false;
      x->get_data(arg);
      return encode_data(writer, &nargs, arg);
    }
    case T_INTEGER: {
      int arg = 0;
      x->get_data(arg);
      return encode_data(writer, &nargs, arg);
    }
    case T_NULL: {
      void* arg = NULL;
      return encode_data(writer, &nargs, arg);
    }
    case T_NUMBER: {
      double arg = 0.0;
      x->get_data(arg);
      return encode_data(writer, &nargs, arg);
    }
    case T_STRING: {
      nargs = 2;
      char* arg = NULL;
      size_t arg_siz = 0;
      x->get_data_realloc(&arg, &arg_siz);
      bool out = encode_data(writer, &nargs, arg, arg_siz);
      if (arg != NULL) {
	free(arg);
	arg = NULL;
      }
      return out;
    }
    }
    ygglog_error("MetaschemaType::encode_data: Cannot encode data of type '%s'.", type_);
    return false;
  }

  /*!
    @brief Copy data from a source buffer to a destination buffer.
    @param[in] src_buf char* Pointer to source buffer.
    @param[in] src_buf_siz size_t Size of src_buf.
    @param[in,out] dst_buf char** Pointer to memory address of destination buffer.
    @param[in,out] dst_buf_siz size_t Reference to size of destination buffer.
    If dst_buf is reallocated, this will be updated with the size of the buffer
    after reallocation.
    @param[in] allow_realloc int If 1, dst_buf can be reallocated if it is
    not large enough to contain the contents of src_buf. If 0, an error will
    be thrown if dst_buf is not large enough.
    @param[in] skip_terminal bool (optional) If true, the terminal character will
    not be added to the end of the copied buffer. Defaults to false.
    @returns int -1 if there is an error, otherwise its the size of the data
    copied to the destination buffer.
   */
  virtual int copy_to_buffer(const char *src_buf, const size_t src_buf_siz,
			     char **dst_buf, size_t &dst_buf_siz,
			     const int allow_realloc, bool skip_terminal = false) const {
    size_t src_buf_siz_term = src_buf_siz;
    if (!(skip_terminal))
      src_buf_siz_term++;
    if (src_buf_siz_term > dst_buf_siz) {
      if (allow_realloc == 1) {
	dst_buf_siz = src_buf_siz_term;
	char *temp = (char*)realloc(*dst_buf, dst_buf_siz);
	if (temp == NULL) {
	  ygglog_error("MetaschemaType::copy_to_buffer: Failed to realloc destination buffer to %lu bytes.",
		       dst_buf_siz);
	  return -1;
	}
	*dst_buf = temp;
	ygglog_debug("MetaschemaType::copy_to_buffer: Reallocated to %lu bytes.",
		     dst_buf_siz);
      } else {
	if (!(skip_terminal)) {
	  ygglog_error("MetaschemaType::copy_to_buffer: Source with termination character (%lu + 1) exceeds size of destination buffer (%lu).",
		       src_buf_siz, dst_buf_siz);
	} else {
	  ygglog_error("MetaschemaType::copy_to_buffer: Source (%lu) exceeds size of destination buffer (%lu).",
		       src_buf_siz, dst_buf_siz);
	}
	return -1;
      }
    }
    memcpy(*dst_buf, src_buf, src_buf_siz);
    if (!(skip_terminal)) {
      size_t i;
      for (i = src_buf_siz; i < dst_buf_siz; i++)
	(*dst_buf)[i] = '\0';
    }
    return (int)src_buf_siz;
  }

  /*!
    @brief Serialize an instance including it's type and data.
    @param[out] buf char ** Buffer where serialized data should be written.
    @param[in,out] buf_siz size_t* Size of buf. If buf is reallocated, the
    new size of the buffer will be assigned to this address.
    @param[in] allow_realloc int If 1, buf will be reallocated if it is not
    large enough to contain the serialized data. If 0, an error will be raised
    if it is not large enough.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of arguments used will be assigned to this address.
    @param[in] ap va_list_t Variable number of arguments that will be serialized.
    @returns int Size of the serialized data in buf.
   */
  virtual int serialize(char **buf, size_t *buf_siz,
			const int allow_realloc, size_t *nargs, va_list_t &ap) {
    if (use_generic()) {
      generic_t gen_arg = pop_generic(nargs, ap);
      return serialize(buf, buf_siz, allow_realloc,
		       (YggGeneric*)(gen_arg.obj));
    }
    va_list_t ap_copy;
    va_copy(ap_copy.va, ap.va);
    update_from_serialization_args(nargs, ap_copy);
    if (nargs_exp() != *nargs) {
      ygglog_throw_error("MetaschemaType::serialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    rapidjson::StringBuffer body_buf;
    rapidjson::Writer<rapidjson::StringBuffer> body_writer(body_buf);
    bool out = encode_data_wrap(&body_writer, nargs, ap);
    if (!(out)) {
      return -1;
    }
    if (*nargs != 0) {
      ygglog_error("MetaschemaType::serialize: %d arguments were not used.", *nargs);
      return -1;
    }
    // Copy message to buffer
    return copy_to_buffer(body_buf.GetString(), body_buf.GetSize(),
			  buf, *buf_siz, allow_realloc);
  }
  /*!
    @brief Serialize an instance including it's type and data.
    @param[out] buf char ** Buffer where serialized data should be written.
    @param[in,out] buf_siz size_t* Size of buf. If buf is reallocated, the
    new size of the buffer will be assigned to this address.
    @param[in] allow_realloc int If 1, buf will be reallocated if it is not
    large enough to contain the serialized data. If 0, an error will be raised
    if it is not large enough.
    @param[in] Pointer to generic wrapper for object being serialized.
    @returns int Size of the serialized data in buf.
   */
  virtual int serialize(char **buf, size_t *buf_siz,
			const int allow_realloc, YggGeneric* x) {
    update_from_serialization_args(x);
    if (*(x->get_type()) != (*this)) {
      ygglog_throw_error("MetaschemaType::serialize: "
			 "Type associated with provided generic "
			 "object is not equivalent to the type "
			 "associated with the communication object "
			 "performing the serialization.");
    }
    rapidjson::StringBuffer body_buf;
    rapidjson::Writer<rapidjson::StringBuffer> body_writer(body_buf);
    bool out = encode_data(&body_writer, x);
    if (!(out)) {
      return -1;
    }
    // Copy message to buffer
    return copy_to_buffer(body_buf.GetString(), body_buf.GetSize(),
			  buf, *buf_siz, allow_realloc);
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
  virtual bool decode_data(rapidjson::Value &data, const int allow_realloc,
			   size_t *nargs, va_list_t &ap) const {
    if (nargs_exp() != *nargs) {
      ygglog_throw_error("MetaschemaType::decode_data: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    switch (type_code_) {
    case T_BOOLEAN: {
      if (!(data.IsBool()))
	ygglog_throw_error("MetaschemaType::decode_data: Data is not a bool.");
      bool *arg;
      bool **p;
      if (allow_realloc) {
	p = va_arg(ap.va, bool**);
	arg = (bool*)realloc(*p, sizeof(bool));
	if (arg == NULL)
	  ygglog_throw_error("MetaschemaType::decode_data: could not realloc bool pointer.");
	*p = arg;
      } else {
	arg = va_arg(ap.va, bool*);
      }
      (*nargs)--;
      arg[0] = data.GetBool();
      return true;
    }
    case T_INTEGER: {
      if (!(data.IsInt()))
	ygglog_throw_error("MetaschemaType::decode_data: Data is not an int.");
      int *arg;
      int **p;
      if (allow_realloc) {
	p = va_arg(ap.va, int**);
	arg = (int*)realloc(*p, sizeof(int));
	if (arg == NULL)
	  ygglog_throw_error("MetaschemaType::decode_data: could not realloc int pointer.");
	*p = arg;
      } else {
	arg = va_arg(ap.va, int*);
      }
      (*nargs)--;
      arg[0] = data.GetInt();
      return true;
    }
    case T_NULL: {
      if (!(data.IsNull()))
	ygglog_throw_error("MetaschemaType::decode_data: Data is not null.");
      void **arg;
      void ***p;
      if (allow_realloc) {
	p = va_arg(ap.va, void***);
	arg = (void**)realloc(*p, sizeof(void*));
	if (arg == NULL)
	  ygglog_throw_error("MetaschemaType::decode_data: could not realloc void* pointer.");
	*p = arg;
      } else {
	arg = va_arg(ap.va, void**);
      }
      (*nargs)--;
      arg[0] = NULL;
      return true;
    }
    case T_NUMBER: {
      if (!(data.IsDouble()))
	ygglog_throw_error("MetaschemaType::decode_data: Data is not a double.");
      double *arg;
      double **p;
      if (allow_realloc) {
	p = va_arg(ap.va, double**);
	arg = (double*)realloc(*p, sizeof(double));
	if (arg == NULL)
	  ygglog_throw_error("MetaschemaType::decode_data: could not realloc double pointer.");
	*p = arg;
      } else {
	arg = va_arg(ap.va, double*);
      }
      (*nargs)--;
      arg[0] = data.GetDouble();
      return true;
    }
    case T_STRING: {
      if (!(data.IsString()))
	ygglog_throw_error("MetaschemaType::decode_data: Data is not a string.");
      char *arg;
      char **p;
      if (allow_realloc) {
	p = va_arg(ap.va, char**);
	arg = *p;
      } else {
	arg = va_arg(ap.va, char*);
	p = &arg;
      }
      size_t *arg_siz = va_arg(ap.va, size_t*);
      (*nargs)--;
      (*nargs)--;
      int ret = copy_to_buffer(data.GetString(), data.GetStringLength(),
			       p, *arg_siz, allow_realloc);
      if (ret < 0) {
	ygglog_error("MetaschemaType::decode_data: Failed to copy string buffer.");
	return false;
      }
      return true;
    }
    }
    ygglog_error("MetaschemaType::decode_data: Cannot decode data of type '%s'.", type_);
    return false;
  }
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[in] allow_realloc int If 1, the passed variables will be reallocated
    to contain the deserialized data.
    @param[in,out] nargs size_t Number of arguments contained in ap. On return,
    the number of arguments assigned from the deserialized data will be assigned
    to this address.
    @param[out] ... Variable number of arguments that contain addresses 
    where deserialized data should be assigned.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, ...) const {
    va_list_t ap_s;
    va_start(ap_s.va, nargs);
    bool out = decode_data(data, allow_realloc, nargs, ap_s);
    va_end(ap_s.va);
    return out;
  }
  
  /*!
    @brief Decode variables from a JSON string, first checking if the
    type expects a generic object and extracting it if it does.
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
  bool decode_data_wrap(rapidjson::Value &data, const int allow_realloc,
			size_t *nargs, va_list_t &ap) const {
    bool out;
    size_t i;
    for (i = 0; i < skip_before_.size(); i++) {
      va_arg(ap.va, void*);
      (*nargs)--;
    }
    if (use_generic()) {
      generic_t* gen_arg = pop_generic_ptr(nargs, ap);
      out = decode_data(data, (YggGeneric*)(gen_arg->obj));
    } else {
      out = decode_data(data, allow_realloc, nargs, ap);
    }
    for (i = 0; i < skip_after_.size(); i++) {
      va_arg(ap.va, void*);
      (*nargs)--;
    }
    return out;
  }
  /*!
    @brief Decode variables from a JSON string, first checking if the
    type expects a generic object and extracting it if it does.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[in] allow_realloc int If 1, the passed variables will be reallocated
    to contain the deserialized data.
    @param[in,out] nargs size_t Number of arguments contained in ap. On return,
    the number of arguments assigned from the deserialized data will be assigned
    to this address.
    @param[out] ... Variable number of arguments that contain addresses 
    where deserialized data should be assigned.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data_wrap(rapidjson::Value &data, const int allow_realloc,
			size_t *nargs, ...) const {
    va_list_t ap_s;
    va_start(ap_s.va, nargs);
    bool out = decode_data_wrap(data, allow_realloc, nargs, ap_s);
    va_end(ap_s.va);
    return out;
  }
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[out] x YggGeneric* Pointer to generic object where data should be stored.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  virtual bool decode_data(rapidjson::Value &data, YggGeneric* x) const {
    size_t nargs = 1;
    int allow_realloc = 1;
    if (x == NULL) {
      ygglog_throw_error("MetaschemaType::decode_data: Generic wrapper is not initialized.");
    }
    void **arg = x->get_data_pointer();
    if (type_code_ == T_STRING) {
      nargs = 2;
      size_t *arg_siz = x->get_nbytes_pointer();
      return decode_data(data, allow_realloc, &nargs, arg, arg_siz);
    } else {
      return decode_data(data, allow_realloc, &nargs, arg);
    }
  }
  /*!
    @brief Deserialize variables from a JSON string.
    @param[in] buf char* Buffer containing serialized data.
    @param[in] buf_siz size_t Size of the serialized data.
    @param[in] allow_realloc int If 1, the provided variables will be realloced
    as necessary to house the deserialized data.
    @param[in,out] nargs size_t* Number of arguments contained in ap. On
    return, the number of arguments assigned will be assigned to this address.
    @param[out] ap va_list_t Arguments that should be assigned based on the
    deserialized data.
    @returns int -1 if there is an error, otherwise the number of arguments
    used.
   */
  virtual int deserialize(const char *buf, const size_t buf_siz,
			  const int allow_realloc, size_t* nargs, va_list_t &ap) {
    if (use_generic()) {
      generic_t* gen_arg = pop_generic_ptr(nargs, ap);
      return deserialize(buf, buf_siz, (YggGeneric*)(gen_arg->obj));
    }
    const size_t nargs_orig = *nargs;
    va_list_t ap_copy;
    va_copy(ap_copy.va, ap.va);
    update_from_deserialization_args(nargs, ap_copy);
    if (nargs_exp() != *nargs) {
      ygglog_throw_error("MetaschemaType::deserialize: %d arguments expected, but only %d provided.",
			 nargs_exp(), *nargs);
    }
    // Parse body
    rapidjson::Document body_doc;
    body_doc.Parse(buf, buf_siz);
    bool out = decode_data_wrap(body_doc, allow_realloc, nargs, ap);
    if (!(out)) {
      ygglog_error("MetaschemaType::deserialize: One or more errors while parsing body.");
      return -1;
    }
    if (*nargs != 0) {
      ygglog_error("MetaschemaType::deserialize: %d arguments were not used.", *nargs);
      return -1;
    }
    return (int)(nargs_orig - *nargs);
  }
  /*!
    @brief Deserialize variables from a JSON string.
    @param[in] buf char* Buffer containing serialized data.
    @param[in] buf_siz size_t Size of the serialized data.
    @param[out] x YggGeneric* Pointer to generic type wrapper where
    deserialized data should be stored.
    @returns int -1 if there is an error, 0 otherwise.
   */
  virtual int deserialize(const char *buf, const size_t buf_siz,
			  YggGeneric* x) {
    update_from_deserialization_args(x);
    if (x->get_type() == NULL) {
      ygglog_throw_error("MetaschemaType::deserialize: "
			 "The type associated with the generic "
			 "object is NULL.");
    }
    if (*(x->get_type()) != (*this)) {
      printf("Generic object's type:\n");
      x->get_type()->display();
      printf("Deserializing type:\n");
      display();
      ygglog_throw_error("MetaschemaType::deserialize: "
			 "Type associated with provided generic "
			 "object is not equivalent to the type "
			 "associated with the communication object "
			 "performing the deserialization.");
    }
    // Parse body
    rapidjson::Document body_doc;
    body_doc.Parse(buf, buf_siz);
    if (x->get_data() != NULL) {
      ygglog_info("MetaschemaType::deserialize: The generic object where deserialized results are to be stored already contains information. Freeing it.");
      x->free_data();
    }
    bool out = decode_data(body_doc, x);
    if (!(out)) {
      ygglog_error("MetaschemaType::deserialize: One or more errors while parsing body.");
      return -1;
    }
    return 0;
  }

private:
  const char *type_;
  const int type_code_;
protected:
  bool updated_;
private:
  const int nbytes_;
  const bool use_generic_;
protected:
  bool always_generic_;
  std::vector<size_t> skip_before_;
  std::vector<size_t> skip_after_;
};


YggGeneric::YggGeneric() : type(NULL), data(NULL), nbytes(0) {};

YggGeneric::YggGeneric(const MetaschemaType* in_type, void* in_data, size_t in_nbytes) : type(NULL), data(NULL), nbytes(in_nbytes) {
  set_type(in_type);
  set_data(in_data);
  if (nbytes == 0) {
    nbytes = type->nbytes();
  }
};

YggGeneric::YggGeneric(const YggGeneric &other) :
  YggGeneric(other.get_type(), other.get_data(), other.get_nbytes()) {};

YggGeneric::~YggGeneric() {
  free_data();
  free_type();
};

void YggGeneric::display(const char* indent) const {
  type->display_generic(this, indent);
};

void* YggGeneric::copy_data(void* orig_data) const {
  if (orig_data == NULL)
    orig_data = data;
  if (orig_data == NULL)
    return NULL;
  return type->copy_generic(this, orig_data);
};

void YggGeneric::free_data() {
  if ((data != NULL) && (type != NULL)) {
    type->free_generic(this);
  }
  data = NULL;
};

void YggGeneric::free_type() {
  if (type != NULL) {
    delete type;
    type = NULL;
  }
};

YggGeneric* YggGeneric::copy() const {
  YggGeneric* out = new YggGeneric();
  // Bytes must be set before data to allow copy to work correctly
  out->set_type(type);
  out->set_nbytes(nbytes);
  out->set_data(data);
  return out;
};

void YggGeneric::set_type(const MetaschemaType* new_type) {
  type = new_type->copy();
};

MetaschemaType* YggGeneric::get_type() const {
  return type;
};

void YggGeneric::set_nbytes(size_t new_nbytes) {
  nbytes = new_nbytes;
};

size_t YggGeneric::get_nbytes() const {
  return nbytes;
};

size_t* YggGeneric::get_nbytes_pointer() {
  return &nbytes;
};

size_t YggGeneric::get_nelements() const {
  try {
    return type->nelements();
  } catch(...) {
    return 1;
  }
};

void YggGeneric::set_data(void* new_data) {
  free_data();
  data = copy_data(new_data);
};

void* YggGeneric::get_data() const {
  return data;
};

void** YggGeneric::get_data_pointer() {
  return &data;
};

template <typename T>
void YggGeneric::get_data(T* obj, size_t nelements, bool is_char) const {
  size_t obj_size = nelements * sizeof(T);
  bool check = false;
  if (is_char) {
    check = (obj_size > nbytes);
  } else {
    check = (obj_size != nbytes);
  }
  if (check) {
    ygglog_throw_error("YggGeneric::get_data: Type indicates the data has a size of %d bytes, but the provided pointer is to an object with a size of %d bytes.",
		       nbytes, sizeof(T));
  }
  memcpy((void*)obj, data, nbytes);
};

template <typename T>
void YggGeneric::get_data(T &obj) const {
  if (nbytes != sizeof(T)) {
    ygglog_throw_error("YggGeneric::get_data: There are %d elements in the data, but this call signature returns one (provided type has size %d bytes, but object stores %d bytes).", nbytes/sizeof(T),
		       sizeof(T), nbytes);
  }
  T* ptr = static_cast<T*>(data);
  obj = *ptr;
};

template <typename T>
void YggGeneric::get_data_realloc(T** obj, size_t* nelements) const {
  T* new_obj = (T*)realloc(obj[0], nbytes);
  if (new_obj == NULL) {
    ygglog_throw_error("YggGeneric::get_data_realloc: Failed to reallocated input variables.");
  }
  obj[0] = new_obj;
  if (nelements != NULL) {
    nelements[0] = nbytes/sizeof(T);
  }
  get_data(obj[0], nbytes/sizeof(T));
};

void YggGeneric::get_data(char* obj, size_t nelements) const {
  get_data(obj, nelements, true);
};


typedef std::map<std::string, MetaschemaType*> MetaschemaTypeMap;
typedef std::vector<MetaschemaType*> MetaschemaTypeVector;

#endif /*METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
