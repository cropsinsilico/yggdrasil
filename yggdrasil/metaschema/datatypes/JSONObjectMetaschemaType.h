#ifndef JSON_OBJECT_METASCHEMA_TYPE_H_
#define JSON_OBJECT_METASCHEMA_TYPE_H_

#include "../../tools.h"
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
  JSONObjectMetaschemaType(std::map<const char*, MetaschemaType*, strcomp> properties) :
    MetaschemaType("object"), properties_(properties) {}
  /*!
    @brief Create a copy of the type.
    @returns pointer to new JSONObjectMetaschemaType instance with the same data.
   */
  JSONObjectMetaschemaType* copy() { return (new JSONObjectMetaschemaType(properties_)); }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() {
    MetaschemaType::display();
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      printf("Element %s:\n", it->first);
      it->second->display();
    }
  }
  /*!
    @brief Get types for properties.
    @returns std::map<const char*, MetaschemaType*, strcomp> Map from property
    names to types.
   */
  std::map<const char*, MetaschemaType*, strcomp> properties() { return properties_; }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() {
    size_t nargs = 0;
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      nargs = nargs + it->second->nargs_exp();
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
    writer->Key("properties");
    writer->StartObject();
    std::map<const char*, MetaschemaType*, strcomp>::iterator it = properties_.begin();
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
		   size_t *nargs, va_list_t &ap) {
    // TODO: Handle case of single map argument for encoding
    writer->StartObject();
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
    size_t i = 0;
    for (it = properties_.begin(); it != properties_.end(); it++, i++) {
      writer->Key(it->first);
      if (!(it->second->encode_data(writer, nargs, ap)))
	return false;
    }
    writer->EndObject();
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
    if (!(data.IsObject())) {
      ygglog_error("JSONObjectMetaschemaType::decode_data: Raw data is not an object.");
      return false;
    }
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
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
