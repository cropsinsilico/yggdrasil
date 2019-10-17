#ifndef METASCHEMA_TYPE_H_
#define METASCHEMA_TYPE_H_

#include "../tools.h"

#include <stdexcept>
#include <iostream>
#include <iomanip>
#include <map>
#include <vector>
#include "rapidjson/document.h"
#include "rapidjson/writer.h"


enum { T_BOOLEAN, T_INTEGER, T_NULL, T_NUMBER, T_STRING, T_ARRAY, T_OBJECT,
       T_DIRECT, T_1DARRAY, T_NDARRAY, T_SCALAR, T_FLOAT, T_UINT, T_INT, T_COMPLEX,
       T_BYTES, T_UNICODE, T_PLY, T_OBJ, T_ASCII_TABLE };


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
  @brief String comparison structure.
 */
struct strcomp
{
  /*!
    @brief Comparison operator.
    @param[in] a char const * First string for comparison.
    @param[in] b char const * Second string for comparison.
    @returns bool true if the strings are equivalent, false otherwise.
   */
  bool operator()(char const *a, char const *b) const
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
  YggGeneric(MetaschemaType* in_type, void* in_data, size_t in_nbytes=0);
  ~YggGeneric();
  /*!
    @brief Display the data.
   */
  void display(const char* indent="");
  /*!
    @brief Get a copy of the data.
    @returns void* Pointer to copy of data.
  */
  void* copy_data(void* orig_data=NULL);
  /*!
    @brief Free the memory used by the data.
   */
  void free_data();
  /*!
    @brief Get a copy.
    @returns YggGeneric* Copy of this class.
   */
  YggGeneric* copy();
  /*!
    @brief Set the data type.
    @param[in] new_type MetaschemaType* Pointer to new type.
   */
  void set_type(MetaschemaType* new_type);
  /*!
    @brief Get the data type.
    @returns MetaschemaType* Pointer to data type.
   */
  MetaschemaType* get_type();
  /*!
    @brief Set the data size.
    @param[in] new_nbytes size_t New data size.
   */
  void set_nbytes(size_t new_nbytes);
  /*!
    @brief Get the data size.
    @returns size_t Number of bytes in the data object.
   */
  size_t get_nbytes();
  /*!
    @brief Get a pointer to the data size.
    @returns size_t* Pointer to number of bytes in the data object.
   */
  size_t* get_nbytes_pointer();
  /*!
    @brief Get the number of elements in the data.
    @returns size_t Number of elements in the data.
   */
  size_t get_nelements();
  /*!
    @brief Set data.
    @param[in] new_data void* New data.
   */
  void set_data(void *new_data);
  /*!
    @brief Extract data.
    @returns void* Pointer to data.
   */
  void* get_data();
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
  void get_data(T* obj, size_t nelements=1, bool is_char=false);
  /*!
    @brief Extract data and assign the value to the provided variable.
    @param[out] obj T Existing variable where data should be stored.
   */
  template <typename T>
  void get_data(T &obj);
  /*!
    @brief Extract data, realloc provided array, and copy data into it.
    @param[out] obj T** Pointer to existing array where data should be copied.
    @param[in, out] nelements size_t* Pointer to number of elements in
    the provided array. The number of elements in teh array after
    reallocation is stored at this address. Defaults to NULL if not
    provided.
   */
  template <typename T>
  void get_data_realloc(T** obj, size_t* nelements=NULL);
  /*!
    @brief Extract data and copy into the provided variable.
    @param[out] obj T* Pointer to existing variable where data should be copied.
    @param[in] nelements size_t Number of elements in the provided array.
    Defaults to 1 if not provided.
   */
  void get_data(char* obj, size_t nelements);
};


typedef std::vector<YggGeneric*> YggGenericVector;
typedef std::map<const char*, YggGeneric*, strcomp> YggGenericMap;


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
   */
  MetaschemaType(const char* type) :
    type_((const char*)malloc(100)), type_code_(-1), updated_(false),
    nbytes_(0) {
    update_type(type);
  }
  /*!
    @brief Constructor for MetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  MetaschemaType(const rapidjson::Value &type_doc) :
    type_((const char*)malloc(100)), type_code_(-1), updated_(false),
    nbytes_(0) {
    if (!(type_doc.IsObject()))
      ygglog_throw_error("MetaschemaType: Parsed document is not an object.");
    if (!(type_doc.HasMember("type")))
      ygglog_throw_error("MetaschemaType: Parsed header dosn't contain a type.");
    if (!(type_doc["type"].IsString()))
      ygglog_throw_error("MetaschemaType: Type in parsed header is not a string.");
    update_type(type_doc["type"].GetString());
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
    @brief Create a copy of the type.
    @returns pointer to new MetaschemaType instance with the same data.
   */
  virtual MetaschemaType* copy() const { return (new MetaschemaType(type_)); }
  /*!
    @brief Print information about the type to stdout.
  */
  virtual void display() const {
    printf("%-15s = %s\n", "type", type_);
    printf("%-15s = %d\n", "type_code", type_code_);
  }
  /*!
    @brief Display data.
    @param[in] x YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  virtual void display_generic(YggGeneric* data, const char* indent="") const {
    std::cout << indent;
    switch (type_code_) {
    case T_BOOLEAN: {
      bool arg = false;
      data->get_data(arg);
      std::cout << arg << std::endl;
      return;
    }
    case T_INTEGER: {
      int arg = 0;
      data->get_data(arg);
      std::cout << arg << std::endl;
      return;
    }
    case T_NULL: {
      std::cout << NULL << std::endl;
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
    ygglog_throw_error("MetaschemaType::display_generic: Cannot display type '%s'.", type_);
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
    @brief Destructor for MetaschemaType.
    Free the type string malloc'd during constructor.
   */
  virtual ~MetaschemaType() {
    free((char*)type_);
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
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  virtual void update(MetaschemaType* new_info) {
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
   */
  virtual void update_from_serialization_args(size_t *nargs, va_list_t &ap) {
    return;
  }
  /*!
    @brief Update the type object with info from provided variable arguments for deserialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
   */
  virtual void update_from_deserialization_args(size_t *nargs, va_list_t &ap) {
    return;
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
    strncpy(*type_modifier, new_type, 100);
    int* type_code_modifier = const_cast<int*>(&type_code_);
    *type_code_modifier = check_type();
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
#ifdef _WIN32
    new_length;
#endif 
    ygglog_throw_error("MetaschemaType::set_length: Cannot set length for type '%s'.", type_);
  }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements (1 for scalar).
   */
  virtual const size_t nelements() const { return 1; }
  // /*!
  //   @brief Get the type's length.
  //   @returns size_t Type length.
  //  */
  // virtual size_t length() const {
  //   // ygglog_throw_error("MetaschemaType::length: Cannot get length for type '%s'.", type_);
  //   return 1;
  // }
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
    writer->String(type_, strlen(type_));
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
      writer->String(arg, arg_siz);
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
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  virtual bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
			   YggGeneric* x) const {
    size_t nargs = 1;
    switch (type_code_) {
    case T_BOOLEAN:
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
    update_from_serialization_args(nargs, ap);
    if (nargs_exp() != *nargs) {
      ygglog_throw_error("MetaschemaType::serialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    rapidjson::StringBuffer body_buf;
    rapidjson::Writer<rapidjson::StringBuffer> body_writer(body_buf);
    bool out = encode_data(&body_writer, nargs, ap);
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
      void **arg = va_arg(ap.va, void**);
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
    const size_t nargs_orig = *nargs;
    update_from_deserialization_args(nargs, ap);
    if (nargs_exp() > *nargs) {
      ygglog_throw_error("MetaschemaType::deserialize: %d arguments expected, but only %d provided.",
			 nargs_exp(), *nargs);
    }
    // Parse body
    rapidjson::Document body_doc;
    body_doc.Parse(buf, buf_siz);
    bool out = decode_data(body_doc, allow_realloc, nargs, ap);
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
    if (*(x->get_type()) != (*this)) {
      ygglog_throw_error("MetaschemaType::deserialize: "
			 "Type associated with provided generic "
			 "object is not equivalent to the type "
			 "associated with the communication object "
			 "performing the deserialization.");
    }
    // Parse body
    rapidjson::Document body_doc;
    body_doc.Parse(buf, buf_siz);
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
  bool updated_;
  const int nbytes_;
};


YggGeneric::YggGeneric() : type(NULL), data(NULL), nbytes(0) {};


YggGeneric::YggGeneric(MetaschemaType* in_type, void* in_data, size_t in_nbytes) : type(in_type), data(NULL), nbytes(in_nbytes) {
  if (nbytes == 0) {
    nbytes = type->nbytes();
  }
  set_data(in_data);
};
YggGeneric::~YggGeneric() {
  free_data();
};
void YggGeneric::display(const char* indent) {
  type->display_generic(this, indent);
};
void* YggGeneric::copy_data(void* orig_data) {
  void* out = NULL;
  if (orig_data == NULL) {
    orig_data = data;
  }
  if (orig_data != NULL) {
    if (type->type_code() == T_ARRAY) {
      YggGenericVector* old_data = (YggGenericVector*)orig_data;
      YggGenericVector* new_data = new YggGenericVector();
      YggGenericVector::iterator it;
      for (it = old_data->begin(); it != old_data->end(); it++) {
      	new_data->push_back((*it)->copy());
      }
      out = (void*)new_data;
    } else if (type->type_code() == T_OBJECT) {
      YggGenericMap* old_data = (YggGenericMap*)orig_data;
      YggGenericMap* new_data = new YggGenericMap();
      YggGenericMap::iterator it;
      for (it = old_data->begin(); it != old_data->end(); it++) {
      	(*new_data)[it->first] = (it->second)->copy();
      }
      out = (void*)(new_data);
    } else {
      void* idata = (void*)realloc(out, nbytes);
      if (idata == NULL) {
	ygglog_throw_error("YggGeneric: Failed to realloc data.");
      }
      out = idata;
      memcpy(out, orig_data, nbytes);
    }
  }
  return out;
};
void YggGeneric::free_data() {
  if (data != NULL) {
    if (type->type_code() == T_ARRAY) {
      YggGenericVector* old_data = (YggGenericVector*)data;
      YggGenericVector::iterator it;
      for (it = old_data->begin(); it != old_data->end(); it++) {
      	delete *it;
      	*it = NULL;
      }
      delete old_data;
    } else if (type->type_code() == T_OBJECT) {
      YggGenericMap::iterator it;
      YggGenericMap* old_data = (YggGenericMap*)data;
      for (it = old_data->begin(); it != old_data->end(); it++) {
	delete it->second;
	it->second = NULL;
      }
      delete old_data;
    } else {
      free(data);
    }
    data = NULL;
  }
};
YggGeneric* YggGeneric::copy() {
  YggGeneric* out = new YggGeneric();
  // Bytes must be set before data to allow copy to work correctly
  out->set_type(type);
  out->set_nbytes(nbytes);
  out->set_data(data);
  return out;
};
void YggGeneric::set_type(MetaschemaType* new_type) {
  type = new_type;
};
MetaschemaType* YggGeneric::get_type() {
  return type;
};
void YggGeneric::set_nbytes(size_t new_nbytes) {
  nbytes = new_nbytes;
};
size_t YggGeneric::get_nbytes() {
  return nbytes;
};
size_t* YggGeneric::get_nbytes_pointer() {
  return &nbytes;
};
size_t YggGeneric::get_nelements() {
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
void* YggGeneric::get_data() {
  return data;
};
void** YggGeneric::get_data_pointer() {
  return &data;
};
template <typename T>
void YggGeneric::get_data(T* obj, size_t nelements, bool is_char) {
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
void YggGeneric::get_data(T &obj) {
  if (nbytes != sizeof(T)) {
    ygglog_throw_error("YggGeneric::get_data: There are %d elements in the data, but this call signature returns one (provided type has size %d bytes, but object stores %d bytes).", nbytes/sizeof(T),
		       sizeof(T), nbytes);
  }
  T* ptr = static_cast<T*>(data);
  obj = *ptr;
};
template <typename T>
void YggGeneric::get_data_realloc(T** obj, size_t* nelements) {
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
void YggGeneric::get_data(char* obj, size_t nelements) {
  get_data(obj, nelements, true);
};

#endif /*METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
