#ifndef DIRECT_METASCHEMA_TYPE_H_
#define DIRECT_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "MetaschemaType.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Class for sending strings directly.

  The DirectMetaschemaType provides basic functionality for encoding/decoding
  strings from/to JSON style strings.
 */
class DirectMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for MetaschemaType.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  DirectMetaschemaType(const bool use_generic=false) :
    MetaschemaType("direct", use_generic) {}
  /*!
    @brief Constructor for DirectMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  DirectMetaschemaType(const rapidjson::Value &type_doc,
		       const bool use_generic=false) :
    MetaschemaType("direct", use_generic) {
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    type_doc;
#endif
  }
  /*!
    @brief Constructor for DirectMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  DirectMetaschemaType(PyObject* pyobj, const bool use_generic=false) :
    MetaschemaType(pyobj, use_generic) {}
  /*!
    @brief Copy constructor.
    @param[in] other DirectMetaschemaType* Instance to copy.
   */
  DirectMetaschemaType(const DirectMetaschemaType &other) :
    DirectMetaschemaType(other.use_generic()) {}
  /*!
    @brief Create a copy of the type.
    @returns pointer to new DirectMetaschemaType instance with the same data.
   */
  DirectMetaschemaType* copy() const override { return (new DirectMetaschemaType(use_generic())); }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    return 2;
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
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    writer;
    nargs;
    ap;
#endif
    ygglog_error("DirectMetaschemaType::encode_data: Direct type cannot be JSON encoded.");
    return false;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGeneric* x) const override {
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    writer;
    x;
#endif
    ygglog_error("DirectMetaschemaType::encode_data: Direct type cannot be JSON encoded.");
    return false;
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
  int serialize(char **buf, size_t *buf_siz,
		const int allow_realloc, size_t *nargs, va_list_t &ap) override {
    if (nargs_exp() != *nargs) {
      ygglog_throw_error("DirectMetaschemaType::serialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    *nargs = *nargs - nargs_exp();
    // Assumes null termination
    char *msg = va_arg(ap.va, char*);
    size_t msg_siz = va_arg(ap.va, size_t);
    if (*nargs != 0) {
      ygglog_error("DirectMetaschemaType::serialize: %d arguments were not used.", *nargs);
      return -1;
    }
    // Copy message to buffer
    return copy_to_buffer(msg, msg_siz, buf, *buf_siz, allow_realloc);
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
  int serialize(char **buf, size_t *buf_siz,
		const int allow_realloc, YggGeneric* x) override {
    // Assumes null termination
    char *msg = NULL;
    size_t msg_siz = 0;
    x->get_data_realloc(&msg, &msg_siz);
    // Copy message to buffer
    int out = copy_to_buffer(msg, msg_siz, buf, *buf_siz, allow_realloc);
    if (msg != NULL) {
      free(msg);
      msg = NULL;
    }
    return out;
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
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    data;
    allow_realloc;
    nargs;
    ap;
#endif
    ygglog_error("DirectMetaschemaType::decode_data: Direct type cannot be JSON decoded.");
    return false;
  }
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[out] x YggGeneric* Pointer to generic object where data should be stored.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, YggGeneric* x) const override {
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    data;
    x;
#endif
    ygglog_error("DirectMetaschemaType::decode_data: Direct type cannot be JSON decoded.");
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
  int deserialize(const char *buf, const size_t buf_siz,
		  const int allow_realloc, size_t *nargs, va_list_t &ap) override {
    if (nargs_exp() != *nargs) {
      ygglog_throw_error("DirectMetaschemaType::deserialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    const size_t nargs_orig = *nargs;
    *nargs = *nargs - nargs_exp();
    // Assumes reallocation is allowed
    char **msg;
    char *msg_base;
    if (allow_realloc) {
      msg = va_arg(ap.va, char**);
    } else {
      msg_base = va_arg(ap.va, char*);
      msg = &msg_base;
    }
    size_t *msg_siz = va_arg(ap.va, size_t*);
    // Copy message from buffer
    if (copy_to_buffer(buf, buf_siz, msg, *msg_siz, allow_realloc) < 0) {
      return -1;
    }
    if (*nargs != 0) {
      ygglog_error("DirectMetaschemaType::deserialize: %d arguments were not used.", *nargs);
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
  int deserialize(const char *buf, const size_t buf_siz,
		  YggGeneric* x) override {
    // Assumes reallocation is allowed
    int allow_realloc = 1;
    char **msg = (char**)(x->get_data_pointer());
    size_t *msg_siz = x->get_nbytes_pointer();
    // Copy message from buffer
    if (copy_to_buffer(buf, buf_siz, msg, *msg_siz, allow_realloc) < 0) {
      return -1;
    }
    return 0;
  }

};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
//}
#endif

#endif /*DIRECT_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
