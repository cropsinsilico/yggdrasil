#ifndef JSON_ARRAY_METASCHEMA_TYPE_H_
#define JSON_ARRAY_METASCHEMA_TYPE_H_

#include "../../tools.h"
#include "MetaschemaType.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


class JSONArrayMetaschemaType : public MetaschemaType {
public:
  JSONArrayMetaschemaType(std::vector<MetaschemaType*> items,
			  const char *format_str = "") :
    MetaschemaType("array"), items_(items) {
    strcpy(format_str_, format_str);
  }
  JSONArrayMetaschemaType* copy() { return (new JSONArrayMetaschemaType(items_, format_str_)); }
  void display() {
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
  size_t nitems() { return items_.size(); }
  std::vector<MetaschemaType*> items() { return items_; }
  bool all_arrays() {
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
  size_t nargs_exp() {
    size_t nargs = 0;
    if (all_arrays())
      nargs++; // For the number of rows
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      nargs = nargs + items_[i]->nargs_exp();
    }
    return nargs;
  }

  // Encoding
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
    if (not MetaschemaType::encode_type_prop(writer)) { return false; }
    if (strlen(format_str_) > 0) {
      writer->Key("format_str");
      writer->String(format_str_, strlen(format_str_));
    }
    writer->Key("items");
    writer->StartArray();
    size_t i;
    for (i = 0; i < items_.size(); i++) {
      if (not (items_[i]->encode_type(writer)))
	return false;
    }
    writer->EndArray();
    return true;
  }
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) {
    size_t i;
    if (all_arrays()) {
      size_t nrows = va_arg(ap.va, size_t);
      (*nargs)--;
      for (i = 0; i < items_.size(); i++) {
	items_[i]->set_length(nrows);
      }
    }
    writer->StartArray();
    for (i = 0; i < items_.size(); i++) {
      if (not (items_[i]->encode_data(writer, nargs, ap)))
	return false;
    }
    writer->EndArray();
    return true;
  }

  // Decoding
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) {
    size_t i;
    if (all_arrays()) {
      size_t *nrows = va_arg(ap.va, size_t*);
      size_t inrows;
      (*nargs)--;
      *nrows = items_[0]->get_length();
      for (i = 1; i < items_.size(); i++) {
	inrows = items_[i]->get_length();
	if (*nrows != inrows) {
	  ygglog_error("JSONArrayMetaschemaType::decode_data: Number of rows not consistent across all items.");
	  return false;
	}
      }
    }
    if (not data.IsArray()) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: Raw data is not an array.");
      return false;
    }
    if (data.Size() != items_.size()) {
      ygglog_error("JSONArrayMetaschemaType::decode_data: %lu items expected, but %lu found.",
		   items_.size(), data.Size());
      return false;
    }
    for (i = 0; i < items_.size(); i++) {
      if (not (items_[i]->decode_data(data[i], allow_realloc, nargs, ap)))
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
