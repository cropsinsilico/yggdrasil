#ifndef DIRECT_METASCHEMA_TYPE_H_
#define DIRECT_METASCHEMA_TYPE_H_

#include "../../tools.h"
#include "MetaschemaType.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


class DirectMetaschemaType : public MetaschemaType {
public:
  DirectMetaschemaType() : MetaschemaType("direct") {}
  DirectMetaschemaType(const rapidjson::Value &type_doc) : MetaschemaType("direct") {}
  DirectMetaschemaType* copy() { return (new DirectMetaschemaType()); }
  size_t nargs_exp() {
    return 2;
  }
  
  // Encoding
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) {
    cislog_error("DirectMetaschemaType::encode_data: Direct type cannot be JSON encoded.");
    return false;
  }
  int serialize(char **buf, size_t *buf_siz,
		const int allow_realloc, size_t *nargs, va_list_t &ap) {
    if (nargs_exp() != *nargs) {
      cislog_throw_error("DirectMetaschemaType::serialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    *nargs = *nargs - nargs_exp();
    // Assumes null termination
    char *msg = va_arg(ap.va, char*);
    size_t msg_siz = va_arg(ap.va, size_t);
    if (*nargs != 0) {
      cislog_error("DirectMetaschemaType::serialize: %d arguments were not used.", *nargs);
      return -1;
    }
    // Copy message to buffer
    return copy_to_buffer(msg, msg_siz, buf, *buf_siz, allow_realloc);
  }
  
  // Decoding
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) {
    cislog_error("DirectMetaschemaType::decode_data: Direct type cannot be JSON decoded.");
    return false;
  }
  int deserialize(const char *buf, const size_t buf_siz,
		  const int allow_realloc, size_t *nargs, va_list_t &ap) {
    if (nargs_exp() != *nargs) {
      cislog_throw_error("DirectMetaschemaType::deserialize: %d arguments expected, but %d provided.",
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
      cislog_error("DirectMetaschemaType::deserialize: %d arguments were not used.", *nargs);
      return -1;
    }
    return (int)(nargs_orig - *nargs);
  }

};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
//}
#endif

#endif /*DIRECT_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
