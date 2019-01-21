#ifndef JSON_DECODER_H_
#define JSON_DECODER_H_

#include "PlySerialize.h"
#include "ObjSerialize.h"
#include "base64.h"
#include "../comm_header.h"

#define YGG_MSG_HEAD "YGG_MSG_HEAD"
#define COMMBUFFSIZ 2000

#ifndef __cplusplus /* If this is a C compiler, use C++ linkage */
extern "C++" {
#endif

#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"


template <typename Encoding, typename Allocator = MemoryPoolAllocator<>, typename StackAllocator = CrtAllocator>
class HeadDocumentDecoder : public rapidjson::GenericDocument<Encoding, Allocator, StackAllocator> {
public:
  typedef char Ch;
  
  HeadDocumentDecoder(comm_head_t& head) :
    head_(head), curr_key_(""), level_(0)
  {}
  bool Int(int i)         {
    if ((strlen(curr_key_) != 0) && (level_ == 1)) {
      switch (curr_key_) {
      case "size":
	head_->size = (size_t)i;
	if (head_->bodysiz < head_->size) {
	  head_->multipart = 1;
	} else {
	  head_->multipart = 0;
	}
      }
    }
    return rapidjson::GenericDocument::Int(i);
  }
  bool String   (const Ch* str, SizeType len, bool copy) {
    if ((strlen(curr_key_) != 0) && (level_ == 1)) {
      char *target = NULL;
      size_t target_size = COMMBUFFSIZ;
      switch (curr_key_) {
      case "address":
	target = head_->address;
	break;
      case "id":
	target = head_->id;
	break;
      case "request_id":
	target = head->request_id;
	break;
      case "response_address":
	target = head->response_address;
	break;
      case "zmq_reply":
	target = head->zmq_reply;
	break;
      case "zmq_reply_worker":
	target = head->zmq_reply_worker;
	break;
      }
      if (target) {
	if (len > size_t) {
	  ygglog_error("HeadDocumentDecoder: Size of value for key '%s' (%d) exceeds size of target buffer (%d).",
		       curr_key_, len, target_size);
	  return false;
	}
	strcpy(target, str);
      }
    }
    return rapidjson::GenericDocument::String(str, len, copy);
  }

  bool StartObject() {
    level_++;
    if (level_ == 1) {
      curr_key_[0] = '\0';
    }
    return rapidjson::GenericDocument::StartObject();
  }
  bool Key(const Ch* str, SizeType len, bool copy) {
    if (level_ == 1) {
      curr_key_ = (char*)realloc(curr_key_, len + 1);
      strcpy(curr_key_, str);
    }
    return rapidjson::GenericDocument::Key(str, len, copy);
  }
  bool EndObject(SizeType memberCount) {
    if (level_ == 1) {
      curr_key_[0] = '\0';
    }
    level_--;
    return rapidjson::GenericDocument::EndObject(memberCount);
  }

private:
  HeadDocumentDecoder(const HeadDocumentDecoder&);
  HeadDocumentDecoder& operator=(const HeadDocumentDecoder&);

  comm_head_t& head_;
  char curr_key_[COMMBUFFSIZ];
  size_t level_;

};


class BodyDecoder {
public:
  typedef char Ch;
  
  BodyDecoder(comm_head_t& head_, HeadDocumentDecoder& head_doc, va_list ap) :
    head_(head), head_doc_(head_doc), ap_(ap), level_(0), curr_type_(),
    first_key_(), in_array_(), array_element_count_()
  {
    curr_type_.push(head_doc_);
    first_key_.push(true);
    in_array_.push(false);
  }
  bool StartScalar() {
    // TODO: Way to pass arbitrary & dynamic data back to C
    if (level_ > 1) {
      ygglog_error("BodyDecoder: Maximum level of 1 imposed to prevent arbitrary objects.");
      return false;
    }
    if ((level_ == 1) and (not in_array_.top())) {
      ygglog_error("BodyDecoder: Only flat arrays are allowed.");
      return false;
    }
    if (in_array_.top()) {
      if (curr_type_.top().IsObject()) {
	curr_type_.push(curr_type_);
      } else if (curr_type_.top().IsArray()) {
	if (array_element_count_.top() > curr_type_.top().Size()) {
	  ygglog_error("BodyDecoder: Array does not have an element %d." % array_element_count_.top());
	  return false;
	}
	if (not curr_type_.top()[array_element_count_.top()].IsObject()) {
	  ygglog_error("BodyDecoder: Type for element %d is not an object." % array_element_count_.top());
	  return false;
	}
	curr_type_.push(curr_type_.top()[array_element_count_.top()].GetObject());
      } else {
	ygglog_error("BodyDecoder: Array type must be an object or array of types.");
	return false;
      }
    }
    if (!(curr_type_.top().IsObject())) {
      ygglog_error("BodyDecoder: Type definition must be an object.");
      return false;
    }
    if (not curr_type_.top().HasMember("type")) {
      ygglog_error("BodyDecoder: Type object does not have explicit type entry.");
      return false;
    }
    if (not curr_type_.top()["type"].IsString()) {
      ygglog_error("BodyDecoder: Type is not a string.");
      return false;
    }
    in_array.push(false);
    return true;
  }
  bool EndScalar() {
    in_array.pop();
    if (in_array_.top()) {
      curr_type_.pop();
      ++array_element_count_.top();
    }
    return true;
  }

  bool Null()             { return StartScalar() ? EndScalar() : false }
  bool Bool(bool b)       { return StartScalar() ? EndScalar() : false }
  bool Int(int i)         { return StartScalar() ? EndScalar() : false }
  bool Uint(unsigned u)   { return StartScalar() ? EndScalar() : false }
  bool Int64(int64_t i)   { return StartScalar() ? EndScalar() : false }
  bool Uint64(uint64_t u) { return StartScalar() ? EndScalar() : false }
  bool Double(double d)   { return StartScalar() ? EndScalar() : false }
  bool RawNumber(const Ch* str, SizeType len, bool copy) { return StartScalar() ? EndScalar() : false }
  bool String   (const Ch* str, SizeType len, bool copy) {
    if (not StartScalar())
      return false;
    char *type = curr_type_.top()["type"].GetString();
    size_t nele = 1;
    switch (type) {
    case "string":
      char **msg = va_arg(ap_, char**);
      *msg = (char*)realloc(*msg, len + 1);
      memcpy(*msg, str, len);
      (*msg)[len] = '\0';
      head_->nargs_populated += 1;
      break;
    case "ply":
      seri_t s;
      int ret = deserialize_ply(s, str, len, ap_);
      if (ret < 0)
	return false;
      head_->nargs_populated += ret;
      break;
    case "obj":
      seri_t s;
      int ret = deserialize_obj(s, str, len, ap_);
      if (ret < 0)
	return false;
      head_->nargs_populated += ret;
      break;
    case "1darray":
    case "ndarray": {
      if (strcmp(type, "1darray") == 0) {
	if (not (curr_type_.top().HasMember("length"))) {
	  ygglog_error("BodyDecoder: 1darray types must include 'length'.");
	  return false;
	}
	if (not (curr_type_.top()["length"].IsInt())) {
	  ygglog_error("BodyDecoder: 1darray 'length' value must be an int.");
	  return false;
	}
	nele = (size_t)curr_type_.top()["length"].GetInt();
      } else {
	if (not (curr_type_.top().HasMember("shape"))) {
	  ygglog_error("BodyDecoder: ndarray types must include 'shape'.");
	  return false;
	}
	if (not (curr_type_.top()["shape"].IsArray())) {
	  ygglog_error("BodyDecoder: ndarray 'shape' value must be an int.");
	  return false;
	}
	a = curr_type_.top()["shape"];
	nele = 1;
	for (rapidjson::Value::ConstValueIterator itr = a.Begin(); itr != a.End(); ++itr) {
	  if (not (itr.IsInt())) {
	    ygglog_error("BodyDecoder: All elements in shape must be intengers.");
	    return false;
	  }
	  nele = nele * (size_t)iter.GetInt();
	}
      }
    }
    case "scalar":
    case "float":
    case "int":
    case "uint":
    case "bytes":
    case "complex":
    case "unicode": {
      if (not (curr_type_.top().HasMember("precision"))) {
	ygglog_error("BodyDecoder: Precision missing.");
	return false;
      }
      if (not (curr_type_.top()["precision"].IsInt())) {
	ygglog_error("BodyDecoder: Precision must be integer.");
	return false;
      }
      size_t prec = (size_t)curr_type_.top()["precision"].GetInt();
      size_t nbytes = nele * prec;
      // Decode base64
      size_t decoded_len = 0;
      unsigned char *decoded = base64_decode(str, len, &decoded_len);
      if (nbytes != decoded_len) {
	ygglog_error("BodyDecoder: %d bytes were expected, but %d were decoded.",
		     nbytes, decoded_len);
	return false;
      }
      // Transfer data to array memory
      unsigned char **temp;
      unsigned char *t2;
      temp = va_arg(ap, unsigned char**);
      head_->nargs_populated += 1;
      t2 = (unsigned char*)realloc(*temp, nbytes);
      if (t2 == NULL) {
	ygglog_error("BodyDecoder: Failed ro realloc temp var.");
	free(*temp);
	return false;
      }
      *temp = t2;
      memcpy(*temp, decoded, nbytes);
      break;
    }
    }
    return EndScalar();
  }

  bool StartObject() {
    if (not StartScalar())
      return false;
    if (not curr_type_.top().HasMember("properties")) {
      ygglog_error("BodyDecoder: Object type def does not have 'properties' defined.");
      return false;
    }
    if (not curr_type_.top()["properties"].IsObject()) {
      ygglog_error("BodyDecoder: Properties value is not an object.");
      return false;
    }
    curr_type_.push(curr_type_.top()["properties"].GetObject());
    first_key_.push(true);
    level_++;
    return true;
  }
  bool Key(const Ch* str, SizeType len, bool copy) {
    if (first_key_.top()) {
      first_key_.pop();
      first_key_.push(false);
    } else {
      // Remove previous key's type definition
      curr_type_.pop();
    }
    if (not curr_type_.top().HasMember(str)) {
      ygglog_error("BodyDecoder: There is not a property definition for key '%s'.", str);
      return false;
    }
    curr_type_.push(curr_type_.top()[str]);
    return true;
  }
  bool EndObject(SizeType memberCount) {
    if (memberCount > 0) {
      // Remove type from last key
      curr_type_.pop();
    }
    curr_type_.pop();
    first_key_.pop();
    level_--;
    return EndScalar();
  }

  bool StartArray() {
    if (!(StartScalar()))
      return false;
    if (not curr_type_.top().HasMember("items")) {
      ygglog_error("BodyDecoder: Object type def does not have 'items' defined.");
      return false;
    }
    curr_type_.push(curr_type_.top()["items"]);
    in_array_.push(true);
    array_element_count_.push(0);
    level_++;
    return true;
  }
  bool EndArray(SizeType elementCount) {
    curr_type_.pop();
    in_array_.pop();
    array_element_count_.pop();
    level_--;
    return EndScalar();
  }

private:
  BodyDecoder(const BodyDecoder&);
  BodyDecoder& operator=(const BodyDecoder&);

  HeadDocumentDecoder &head_doc_;
  va_list ap;
  std::stack<Value&> curr_type_;
  std::stack<bool> first_key_;
  std::stack<bool> in_array_;
  std::stack<size_t> array_element_count_;

};

#ifndef __cplusplus /* If this is a C compiler, end C++ linkage */
}
#endif

#endif /*JSON_DECODER_H_*/
// Local Variables:
// mode: c++
// End:
