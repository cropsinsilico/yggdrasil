#ifndef METASCHEMA_TYPE_H_
#define METASCHEMA_TYPE_H_

#include "../../tools.h"

#include <stdexcept>
#include <map>
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
  MetaschemaType(const char* type) : type_((const char*)malloc(100)), type_code_(-1) {
    update_type(type);
  }
  /*!
    @brief Constructor for MetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  MetaschemaType(const rapidjson::Value &type_doc) : type_((const char*)malloc(100)), type_code_(-1) {
    if (!(type_doc.IsObject()))
      ygglog_throw_error("MetaschemaType: Parsed document is not an object.");
    if (!(type_doc.HasMember("type")))
      ygglog_throw_error("MetaschemaType: Parsed header dosn't contain a type.");
    if (!(type_doc["type"].IsString()))
      ygglog_throw_error("MetaschemaType: Type in parsed header is not a string.");
    update_type(type_doc["type"].GetString());
    /*
    type_ = type_doc["type"].GetString();
    int* type_code_modifier = const_cast<int*>(&type_code_);
    *type_code_modifier = check_type();
    */
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new MetaschemaType instance with the same data.
   */
  MetaschemaType* copy() { return (new MetaschemaType(type_)); }
  /*!
    @brief Print information about the type to stdout.
  */
  virtual void display() {
    printf("%-15s = %s\n", "type", type_);
    printf("%-15s = %d\n", "type_code", type_code_);
  }
  /*!
    @brief Check that the type is correct and get the corresponding code.
    @returns int Type code for the instance's type.
   */
  int check_type() {
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
  const char* type() { return type_; }
  /*!
    @brief Get the type code.
    @returns int Type code associated with the curent type.
   */
  const int type_code() { return type_code_; }
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
  virtual void set_length(size_t new_length) {
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    new_length;
#endif 
    ygglog_throw_error("MetaschemaType::set_length: Cannot set length for type '%s'.", type_);
  }
  /*!
    @brief Get the type's length.
    @returns size_t Type length.
   */
  virtual size_t get_length() {
    ygglog_throw_error("MetaschemaType::get_length: Cannot get length for type '%s'.", type_);
    return 0;
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  virtual size_t nargs_exp() {
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
  bool encode_type(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
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
  virtual bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
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
			   size_t *nargs, va_list_t &ap) {
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
		   size_t *nargs, ...) {
    va_list_t ap_s;
    va_start(ap_s.va, nargs);
    bool out = encode_data(writer, nargs, ap_s);
    va_end(ap_s.va);
    return out;
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
			     const int allow_realloc, bool skip_terminal = false) {
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
			   size_t *nargs, va_list_t &ap) {
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
    remaining in ap.
   */
  virtual int deserialize(const char *buf, const size_t buf_siz,
			  const int allow_realloc, size_t* nargs, va_list_t &ap) {
    const size_t nargs_orig = *nargs;
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

private:
  const char *type_;
  const int type_code_;
};

#endif /*METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
