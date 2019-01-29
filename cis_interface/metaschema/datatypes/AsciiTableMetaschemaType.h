#ifndef ASCII_TABLE_METASCHEMA_TYPE_H_
#define ASCII_TABLE_METASCHEMA_TYPE_H_

#include "../../tools.h"
#include "MetaschemaType.h"
#include "../../dataio/AsciiTable.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


class AsciiTableMetaschemaType : public MetaschemaType {
public:
  AsciiTableMetaschemaType(const char *format_str, const int as_array=0) :
    MetaschemaType("ascii_table"), as_array_(as_array), table_(NULL) {
    table_ = (asciiTable_t*)malloc(sizeof(asciiTable_t));
    if (table_ == NULL)
      cislog_throw_error("AsciiTableMetaschemaType: Failed to allocate table.");
    table_[0] = asciiTable("seri", "0", format_str, NULL, NULL, NULL);
  }
  ~AsciiTableMetaschemaType() {
    if (table_ != NULL) {
      at_cleanup(table_);
      free(table_);
    }
  }
  AsciiTableMetaschemaType* copy() { return (new AsciiTableMetaschemaType(format_str(),
									  as_array())); }
  void display() {
    MetaschemaType::display();
    printf("%-15s = %s\n", "format_str", format_str());
    printf("%-15s = %d\n", "as_array", as_array_);
  }
  const char* format_str() { return table_->format_str; }
  asciiTable_t* table() { return table_; }
  const int as_array() { return as_array_; }
  virtual size_t nargs_exp() {
    size_t nargs = (size_t)(table_->ncols);
    if (as_array_) {
      nargs++; // For the number of rows
    }
    return nargs;
  }
  
  // Encoding
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) {
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    writer;
    nargs;
    ap;
#endif
    cislog_error("AsciiTableMetaschemaType::encode_data: AsciiTable type cannot be JSON encoded.");
    return false;
  }
  int serialize(char **buf, size_t *buf_siz,
		const int allow_realloc, size_t *nargs, va_list_t &ap) {
    if (nargs_exp() != *nargs) {
      cislog_throw_error("AsciiTableMetaschemaType::serialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    *nargs = *nargs - nargs_exp();
    // Assumes null termination
    int ret;
    if (as_array_) {
      ret = at_varray_to_bytes(*table_, *buf, *buf_siz, ap.va);
    } else {
      ret = at_vrow_to_bytes(*table_, *buf, *buf_siz, ap.va);
    }
    if (*nargs != 0) {
      cislog_error("AsciiTableMetaschemaType::serialize: %d arguments were not used.", *nargs);
      return -1;
    }
    return ret;
  }
  
  // Decoding
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) {
    // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
    data;
    allow_realloc;
    nargs;
    ap;
#endif
    cislog_error("AsciiTableMetaschemaType::decode_data: AsciiTable type cannot be JSON decoded.");
    return false;
  }
  int deserialize(const char *buf, const size_t buf_siz,
		  const int allow_realloc, size_t *nargs, va_list_t &ap) {
    if (nargs_exp() != *nargs) {
      cislog_throw_error("AsciiTableMetaschemaType::deserialize: %d arguments expected, but %d provided.",
			 nargs_exp(), *nargs);
    }
    const size_t nargs_orig = *nargs;
    *nargs = *nargs - nargs_exp();
    int ret;
    if (as_array_) {
      ret = at_vbytes_to_array(*table_, buf, buf_siz, ap.va);
    } else {
      if (allow_realloc) {
	cislog_error("AsciiTableMetaschemaType::deserialize: allow_realloc not supported for rows.");
	return -1;
      }
      ret = at_vbytes_to_row(*table_, buf, ap.va);
    }
    if (ret < 0) {
      cislog_error("AsciiTableMetaschemaType::deserialize: Error using table.");
      return -1;
    } else if (ret != nargs_exp()) {
      cislog_error("AsciiTableMetaschemaType::deserialize: Table used %d arguments, but was expected to used %d.",
		   ret, nargs_exp());
      return -1;
    }
    if (*nargs != 0) {
      cislog_error("AsciiTableMetaschemaType::deserialize: %d arguments were not used.", *nargs);
      return -1;
    }
    return (int)(nargs_orig - *nargs);
  }

private:
  const int as_array_;
  asciiTable_t *table_;

};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
//}
#endif

#endif /*ASCII_TABLE_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
