#ifndef JSON_ARRAY_METASCHEMA_TYPE_H_
#define JSON_ARRAY_METASCHEMA_TYPE_H_

#include "../../tools.h"
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
  JSONArrayMetaschemaType(std::vector<MetaschemaType*> items,
			  const char *format_str = "") :
    MetaschemaType("array"), items_(items) {
    strncpy(format_str_, format_str, 1000);
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new JSONArrayMetaschemaType instance with the same data.
   */
  JSONArrayMetaschemaType* copy() { return (new JSONArrayMetaschemaType(items_, format_str_)); }
  /*!
    @brief Print information about the type to stdout.
  */
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
  /*!
    @brief Get number of items in type.
    @returns size_t Number of items in type.
   */
  size_t nitems() { return items_.size(); }
  /*!
    @brief Get types for items.
    @returns std::vector<MetaschemaType*> Array item types.
   */
  std::vector<MetaschemaType*> items() { return items_; }
  /*!
    @brief Determine if the items are all arrays.
    @returns bool true if all items are arrays, false otherwise.
   */
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
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
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
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
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
      if (!(items_[i]->encode_data(writer, nargs, ap)))
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
