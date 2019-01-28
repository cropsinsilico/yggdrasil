#ifndef JSON_OBJECT_METASCHEMA_TYPE_H_
#define JSON_OBJECT_METASCHEMA_TYPE_H_

#include "../../tools.h"
#include "MetaschemaType.h"

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
//extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


class JSONObjectMetaschemaType : public MetaschemaType {
public:
  JSONObjectMetaschemaType(std::map<const char*, MetaschemaType*, strcomp> properties) :
    MetaschemaType("object"), properties_(properties) {}
  JSONObjectMetaschemaType* copy() { return (new JSONObjectMetaschemaType(properties_)); }
  void display() {
    MetaschemaType::display();
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      printf("Element %s:\n", it->first);
      it->second->display();
    }
  }
  std::map<const char*, MetaschemaType*, strcomp> properties() { return properties_; }
  size_t nargs_exp() {
    size_t nargs = 0;
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
    for (it = properties_.begin(); it != properties_.end(); it++) {
      nargs = nargs + it->second->nargs_exp();
    }
    return nargs;
  }

  // Encoding
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
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) {
    if (!(data.IsObject())) {
      cislog_error("JSONObjectMetaschemaType::decode_data: Raw data is not an object.");
      return false;
    }
    std::map<const char*, MetaschemaType*, strcomp>::iterator it;
    size_t i = 0;
    for (it = properties_.begin(); it != properties_.end(); it++, i++) {
      if (!(data.HasMember(it->first))) {
	cislog_error("JSONObjectMetaschemaType::decode_data: Data dosn't have member '%s'.",
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
