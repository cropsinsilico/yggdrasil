#ifndef YGGDRASIL_SERIALIZATION_H_
#define YGGDRASIL_SERIALIZATION_H_

// Platform specific
#ifdef _WIN32
#include "../regex/regex_win32.h"
#else
#include "../regex/regex_posix.h"
#endif
#include "../constants.h"
#include "utils.h"

#define RAPIDJSON_YGGDRASIL
#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/schema.h"
#include "rapidjson/va_list.h"


/*!
  @brief Split header and body of message.
  @param[in] buf const char* Message that should be split.
  @param[in] buf_siz size_t Size of buf.
  @param[out] head const char** pointer to buffer where the extracted header
  should be stored.
  @param[out] headsiz size_t reference to memory where size of extracted header
  should be stored.
  @returns: int 0 if split is successful, -1 if there was an error.
*/
static inline
int split_head_body(const char *buf, const size_t buf_siz,
		    const char **head, size_t *headsiz) {
  // Split buffer into head and body
  int ret;
  size_t sind, eind, sind_head, eind_head;
  sind = 0;
  eind = 0;
#ifdef _WIN32
  // Windows regex of newline is buggy
  UNUSED(buf_siz);
  size_t sind1, eind1, sind2, eind2;
  char re_head_tag[COMMBUFFSIZ + 1];
  snprintf(re_head_tag, COMMBUFFSIZ, "(%s)", MSG_HEAD_SEP);
  ret = find_match(re_head_tag, buf, &sind1, &eind1);
  if (ret > 0) {
    sind = sind1;
    ret = find_match(re_head_tag, buf + eind1, &sind2, &eind2);
    if (ret > 0)
      eind = eind1 + eind2;
  }
#else
  // Extract just header
  char re_head[COMMBUFFSIZ] = MSG_HEAD_SEP;
  strcat(re_head, "(.*)");
  strcat(re_head, MSG_HEAD_SEP);
  // strcat(re_head, ".*");
  ret = find_match(re_head, buf, &sind, &eind);
#endif
  if (ret < 0) {
    sind_head = 0;
    eind_head = 0;
    ygglog_throw_error("split_head_body: Could not find header in '%.1000s'", buf);
  } else if (ret == 0) {
    sind_head = 0;
    eind_head = 0;
    ygglog_debug("split_head_body: No header in '%.1000s...'", buf);
  } else {
    sind_head = sind + strlen(MSG_HEAD_SEP);
    eind_head = eind - strlen(MSG_HEAD_SEP);
  }
  headsiz[0] = (eind_head - sind_head);
  head[0] = buf + strlen(MSG_HEAD_SEP);
  // char* temp = (char*)realloc(*head, *headsiz + 1);
  // if (temp == NULL) {
  //   ygglog_throw_error("split_head_body: Failed to reallocate header.");
  // }
  // *head = temp;
  // memcpy(*head, buf + sind_head, *headsiz);
  // (*head)[*headsiz] = '\0';
  return 0;
};


class Header {
public:
  Header() :
    data_(NULL), data(NULL), size_data(0), size_buff(0), size_curr(0),
    size_head(0), flags(HEAD_FLAG_VALID),
    metadata(rapidjson::kObjectType), schema(NULL) {}
  ~Header() {
    if ((flags & HEAD_FLAG_OWNSDATA) && data_)
      free(data_);
  }

  void add_schema(rapidjson::Value& src) {
    if (schema == NULL) {
      if (!metadata.HasMember("serializer"))
	metadata.AddMember(rapidjson::Value("serializer", 10).Move(),
			   rapidjson::Value(rapidjson::kObjectType).Move(),
			   metadata.GetAllocator());
      if (!metadata["serializer"].HasMember("datatype"))
	metadata["serializer"].AddMember(rapidjson::Value("datatype", 8).Move(),
					 rapidjson::Value(rapidjson::kObjectType).Move(),
					 metadata.GetAllocator());
      schema = &(metadata["serializer"]["datatype"]);
    }
    schema->CopyFrom(src, metadata.GetAllocator(), true);
  }

  /*!
    @brief Set parameters for sending a message.
    @param[in] metadata0 Pointer to metadata document.
    @param[in] schema0 Pointer to datatype document.
  */
  void for_send(rapidjson::Document* metadata0,
		rapidjson::Value* schema0=NULL) {
    // flags |= (HEAD_FLAG_ALLOW_REALLOC | HEAD_FLAG_OWNSDATA);
    if (metadata0 != NULL && metadata0->IsObject()) {
      metadata.CopyFrom(*metadata0, metadata.GetAllocator(), true);
      if (metadata.HasMember("serializer") &&
	  metadata["serializer"].IsObject() &&
	  metadata["serializer"].HasMember("datatype") &&
	  metadata["serializer"]["datatype"].IsObject()) {
	schema = &(metadata["serializer"]["datatype"]);
      }
    } else if (schema0 != NULL && schema0->IsObject()) {
      add_schema(*schema0);
    }
    if (!metadata.HasMember("__meta__")) {
      rapidjson::Value meta(rapidjson::kObjectType);
      metadata.AddMember(rapidjson::Value("__meta__", 8).Move(),
			 meta, metadata.GetAllocator());
    }
    SetMetaID("id");
    char model[100] = "";
    char *model_name = getenv("YGG_MODEL_NAME");
    if (model_name != NULL) {
      strcpy(model, model_name);
    }
    char *model_copy = getenv("YGG_MODEL_COPY");
    if (model_copy != NULL) {
      strcat(model, "_copy");
      strcat(model, model_copy);
    }
    SetMetaString("model", model);
  }
  /*!
    @brief Set parameters for receiving a message.
    @param[in] buf Message containing header.
    @param[in] buf_siz Size of buffer containing message.
    @param[in] msg_siz Size of message in buffer.
    @param[in] allow_realloc If true, the buffer can be resized to
      receive message larger than buf_siz.
   */
  void for_recv(char** buf, size_t buf_siz, size_t msg_siz,
		bool allow_realloc, bool temp=false) {
    data = buf;
    size_buff = buf_siz;
    size_curr = msg_siz;
    if (allow_realloc)
      flags |= HEAD_FLAG_ALLOW_REALLOC;
    if (temp)
      flags |= HEAD_TEMPORARY;
    const char *head = NULL;
    size_t headsiz = 0;
    split_head_body(*buf, msg_siz, &head, &headsiz);
    if (headsiz == 0) {
      size_data = size_curr;
    } else {
      metadata.Parse(head, headsiz);
      if (metadata.HasParseError()) {
	ygglog_throw_error("Header::for_recv: Error parsing header: %s.", head);
      }
      size_head = headsiz + 2*strlen(MSG_HEAD_SEP);
      // size_t bodysiz = msg_siz - size_head;
      if (!(flags & HEAD_TEMPORARY)) {
	size_curr -= size_head;
	memmove(data[0], data[0] + size_head, size_curr);
	(*data)[size_curr] = '\0';
      }
      // Update parameters from document
      if (!(metadata.IsObject()))
	ygglog_throw_error("Header::for_recv: head document must be an object.");
      if (!(metadata.HasMember("__meta__")))
	ygglog_throw_error("Header::for_recv: No __meta__ information in the header.");
      if (!(metadata["__meta__"].IsObject()))
	ygglog_throw_error("Header::for_recv: __meta__ is not an object.");
      size_data = static_cast<size_t>(GetMetaInt("size"));
      if (GetMetaBoolOptional("in_data", false))
	flags |= HEAD_META_IN_DATA;
      else
	flags &= ~HEAD_META_IN_DATA;
      if (metadata.HasMember("serializer") &&
	  metadata["serializer"].IsObject() &&
	  metadata["serializer"].HasMember("datatype") &&
	  metadata["serializer"]["datatype"].IsObject()) {
	schema = &(metadata["serializer"]["datatype"]);
      }
    }
    // Check for flags
    char* data_chk = data[0];
    if (flags & HEAD_TEMPORARY)
      data_chk += size_head;
    if (strcmp(data_chk, YGG_MSG_EOF) == 0)
      flags |= HEAD_FLAG_EOF;
    else if (strcmp(data_chk, YGG_CLIENT_EOF) == 0)
      flags |= HEAD_FLAG_CLIENT_EOF;
    if (size_curr < size_data)
      flags |= HEAD_FLAG_MULTIPART;
    else
      flags &= ~HEAD_FLAG_MULTIPART;
    if ((!(flags & HEAD_TEMPORARY)) && ((size_data + 1) > size_buff)) {
      if (allow_realloc) {
	char *t_data = (char*)realloc(*data, size_data + 1);
	if (t_data == NULL) {
	  ygglog_throw_error("Header::for_recv: Failed to realloc buffer");
	}
	data[0] = t_data;
      } else {
	ygglog_throw_error("Header::for_recv: Buffer is not large enough");
      }
    }
  }

  void formatBuffer(rapidjson::StringBuffer& buffer, bool metaOnly=true) {
    buffer.Clear();
    if (!metadata.IsObject()) {
      return;
    }
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    if (metaOnly) {
      if (metadata.HasMember("__meta__")) {
	writer.StartObject();
	writer.Key("__meta__", 8, true);
	metadata["__meta__"].Accept(writer);
	writer.EndObject(1);
      }
    } else if (GetMetaBoolOptional("in_data", false)) {
      bool hasMeta = metadata.HasMember("__meta__");
      rapidjson::Value tmp;
      if (hasMeta) {
	tmp.Swap(metadata["__meta__"]);
	metadata.RemoveMember("__meta__");
      }
      metadata.Accept(writer);
      if (hasMeta) {
	metadata.AddMember(rapidjson::Value("__meta__", 8).Move(),
			   tmp, metadata.GetAllocator());
      }
    } else {
      // rapidjson::Value tmp;
      // if (noType && !metadata.HasMember("serializer"))
      // 	noType = false;
      // if (noType) {
      // 	tmp.Swap(metadata["serializer"]);
      // 	metadata.RemoveMember("serializer");
      // }
      metadata.Accept(writer);
      // if (noType) {
      // 	metadata.AddMember("serializer", tmp, metadata.GetAllocator());
      // 	if (schema != NULL)
      // 	  schema = &(metadata["serializer"]["datatype"]);
      // }
    }
  }

  size_t format(const char* buf, size_t buf_siz,
		size_t size_max, bool metaOnly=false) {
    flags |= (HEAD_FLAG_ALLOW_REALLOC | HEAD_FLAG_OWNSDATA);
    data = &data_;
    size_data = buf_siz;
    SetMetaInt("size", buf_siz);
    rapidjson::StringBuffer buffer;
    formatBuffer(buffer, metaOnly);
    rapidjson::StringBuffer buffer_body;
    if (buffer.GetLength() == 0) {
      return 0;
    }
    size_t size_sep = strlen(MSG_HEAD_SEP);
    size_t size_new = static_cast<size_t>(buffer.GetLength()) + 2 * size_sep;
    if (size_new > size_max) {
      if (metaOnly)
	ygglog_throw_error("Header::format: meta already excluded, cannot make header any smaller.");
      flags |= HEAD_META_IN_DATA;
      SetMetaBool("in_data", true);
      formatBuffer(buffer_body);
      size_data += size_sep + static_cast<size_t>(buffer_body.GetLength());
      SetMetaInt("size", size_data);
      formatBuffer(buffer, true);
      size_new = ((3 * size_sep) +
		  static_cast<size_t>(buffer.GetLength()) +
		  static_cast<size_t>(buffer_body.GetLength()));
    }
    size_new += buf_siz;
    if (size_new > size_max && (!(flags & HEAD_FLAG_MULTIPART))) {
      // Early return since comm needs to add to header
      flags |= HEAD_FLAG_MULTIPART;
      return 0;
    }
    if ((size_new + 1) > size_buff) {
      size_buff = size_new + 1;
      data[0] = (char*)realloc(data[0], size_buff);
    }
    int ret;
    if (GetMetaBoolOptional("in_data", false)) {
      ret = snprintf(data[0], size_buff, "%s%s%s%s%s", MSG_HEAD_SEP,
		     buffer.GetString(), MSG_HEAD_SEP,
		     buffer_body.GetString(), MSG_HEAD_SEP);
    } else {
      ret = snprintf(data[0], size_buff, "%s%s%s", MSG_HEAD_SEP,
		     buffer.GetString(), MSG_HEAD_SEP);
    }
    if (((size_t)(ret) + buf_siz) > size_buff)
      ygglog_throw_error("Header::format: Message size (%d) exceeds buffer size (%lu): '%s%s%s'.",
			 ret, size_buff, MSG_HEAD_SEP, buffer.GetString(), MSG_HEAD_SEP);
    size_curr = static_cast<size_t>(ret);
    memcpy(data[0] + size_curr, buf, buf_siz);
    size_curr += buf_siz;
    data[0][size_curr] = '\0';
    return size_curr;
  }

  void finalize_recv() {
    if (!GetMetaBoolOptional("in_data", false))
      return;
    size_t sind, eind;
    int ret = find_match(MSG_HEAD_SEP, *data, &sind, &eind);
    if (ret < 0)
      ygglog_throw_error("Header::finalize_recv: Error locating head separation tag.");
    rapidjson::Document type_doc;
    type_doc.Parse(*data, sind);
    if (type_doc.HasParseError())
      ygglog_throw_error("Header::finalize_recv: Error parsing datatype in data");
    add_schema(type_doc);
    data[0] += eind;
  }
  
#define GET_SET_METHOD_(type, method, setargs)				\
  type GetMeta ## method(const char* name) {				\
    if (!(metadata.IsObject() && metadata.HasMember("__meta__")))	\
      ygglog_throw_error("Get%s: No __meta__ in metadata");		\
    rapidjson::Value &meta_doc = metadata["__meta__"];			\
    if (!(meta_doc.HasMember(name)))					\
      ygglog_throw_error("Get%s: No %s information in the header.", #method, name); \
    if (!(meta_doc[name].Is ## method()))				\
      ygglog_throw_error("Get%s: %s is not %s.", #method, name, #type);	\
    return meta_doc[name].Get ## method();				\
  }									\
  type GetMeta ## method ## Optional(const char* name, type defV) {	\
    if (!(metadata.IsObject() && metadata.HasMember("__meta__")))	\
      ygglog_throw_error("Get%s: No __meta__ in metadata");		\
    rapidjson::Value &meta_doc = metadata["__meta__"];			\
    if (!(meta_doc.HasMember(name)))					\
      return defV;							\
    if (!(meta_doc[name].Is ## method()))				\
      ygglog_throw_error("Get%s: %s is not %s.", #method, name, #type);	\
    return meta_doc[name].Get ## method();				\
  }									\
  bool SetMeta ## method(const char* name, type x) {			\
    if (!(metadata.IsObject() && metadata.HasMember("__meta__")))	\
      ygglog_throw_error("Set%s: No __meta__ in metadata");		\
    rapidjson::Value &meta_doc = metadata["__meta__"];			\
    rapidjson::Value x_val setargs;					\
    meta_doc.AddMember(rapidjson::Value(name, strlen(name)).Move(),	\
		       x_val, metadata.GetAllocator());			\
    return true;							\
  }
  GET_SET_METHOD_(int, Int, (x));
  GET_SET_METHOD_(bool, Bool, (x));
  GET_SET_METHOD_(const char*, String, (x, strlen(x), metadata.GetAllocator()));
#undef GET_SET_METHOD_
  bool SetMetaID(const char* name, const char** id=NULL) {
    char new_id[100];
    snprintf(new_id, 100, "%d", rand());
    bool out = SetMetaString(name, new_id);
    if (out && id)
      id[0] = GetMetaString(name);
    return out;
  }
  char* data_;
  char** data;
  size_t size_data;
  size_t size_buff;
  size_t size_curr;
  size_t size_head;
  uint16_t flags;
  rapidjson::Document metadata;
  rapidjson::Value* schema;
};


template <typename ValueT>
std::string document2string(ValueT& rhs, const char* indent="") {
  rapidjson::StringBuffer sb;
  rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(sb, 0, strlen(indent));
  writer.SetYggdrasilMode(true);
  if (!rhs.Accept(writer)) {
    ygglog_error("document2string: Error in Accept(writer)");
    return std::string("");
  }
  return std::string(sb.GetString());
}

static inline
int deserialize_args(const char* buf, size_t buf_siz,
		     rapidjson::Value& schema,
		     rapidjson::VarArgList& ap) {
  size_t nargs_orig = ap.get_nargs();
  rapidjson::Document d;
  rapidjson::StringStream s(buf);
  d.ParseStream(s);
  if (d.HasParseError())
    ygglog_throw_error("deserialize: Error parsing JSON");
  // TODO: Initialize schema?
  // if (schema.IsNull()) {
  //   schema = encode_schema(d);
  // } else {
  rapidjson::StringBuffer sb;
  if (!d.Normalize(schema, &sb)) {
    std::string d_str = document2string(d);
    std::string s_str = document2string(schema);
    ygglog_throw_error("deserialize_args: Error normalizing document:\n%s\ndocument=%s\nschema=%s\nmessage=%s...", sb.GetString(), d_str.c_str(), s_str.c_str(), buf);
  }
  // }
  if (!d.SetVarArgs(schema, ap)) {
    ygglog_throw_error("deserialize_args: Error setting arguments from JSON document");
  }
  return (int)(nargs_orig - ap.get_nargs());
}

static inline
int serialize_args(char **buf, size_t *buf_siz,
		   rapidjson::Value& schema,
		   rapidjson::VarArgList& ap) {
  rapidjson::Document d;
  if (!d.GetVarArgs(schema, ap)) {
    std::string s_str = document2string(schema);
    ygglog_throw_error("serialize_args: Error creating JSON document from arguments for schema = %s", s_str.c_str());
  }
  rapidjson::StringBuffer buffer;
  rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
  if (!d.Accept(writer))
    ygglog_throw_error("serialize_args: Error serializing document.");
  if ((size_t)(buffer.GetLength() + 1) > buf_siz[0]) {
    buf_siz[0] = (size_t)(buffer.GetLength() + 1);
    buf[0] = (char*)realloc(buf[0], buf_siz[0]);
  }
  memcpy(buf[0], buffer.GetString(), (size_t)(buffer.GetLength()));
  buf[0][(size_t)(buffer.GetLength())] = '\0';
  return static_cast<int>(buffer.GetLength());
}



#endif /* YGGDRASIL_SERIALIZATION_H_ */
// Local Variables:
// mode: c++
// End:
