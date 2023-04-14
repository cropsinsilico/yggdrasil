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
#include <string.h>


#define STRLEN_RJ(var)				\
  static_cast<rapidjson::SizeType>(strlen(var))

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


bool add_dtype(rapidjson::Document* d,
	       const char* type, const char* subtype,
	       const size_t precision,
	       const size_t ndim=0, const size_t* shape=NULL,
	       const char* units=NULL) {
  size_t N = 0;
  if (!d->StartObject())
    return false;
  // type
  if (!d->Key("type", 4, true))
    return false;
  if (!d->String(type, STRLEN_RJ(type), true))
    return false;
  N++;
  // subtype
  if (!d->Key("subtype", 7, true))
    return false;
  if (strcmp(subtype, "bytes") == 0) {
    if (!d->String("string", 6, true))
      return false;
  } else if (strcmp(subtype, "unicode") == 0) {
    if (!d->String("string", 6, true))
      return false;
    if (!d->Key("encoding", 8, true))
      return false;
    if (!d->String("UTF8", 4, true))
      return false;
    N++;
  } else {
    if (!d->String(subtype, STRLEN_RJ(subtype), true))
      return false;
  }
  N++;
  // precision
  if (precision > 0) {
    if (!d->Key("precision", 9, true))
      return false;
    if (!d->Uint(precision))
      return false;
    N++;
  }
  // shape
  if (ndim > 0) {
    if (shape != NULL) {
      if (!d->Key("shape", 5, true))
	return false;
      if (!d->StartArray())
	return false;
      for (size_t i = 0; i < ndim; i++) {
	if (!d->Uint(shape[i]))
	  return false;
      }
      if (!d->EndArray(ndim))
	return false;
    } else {
      if (!d->Key("ndim", 4, true))
	return false;
      if (!d->Uint(ndim))
	return false;
    }
    N++;
  }
  // units
  if (units && strlen(units) > 0) {
    if (!d->Key("units", 5, true))
      return false;
    if (!d->String(units, STRLEN_RJ(units), true))
      return false;
    N++;
  }
  // end
  return d->EndObject(N);
}

void format_str2metadata(rapidjson::Document& out,
			 const char* format_str,
			 const int as_array = 0) {
  out.StartObject();
  out.Key("serializer", 10, true);
  out.StartObject();
  out.Key("format_str", 10, true);
  out.String(format_str, STRLEN_RJ(format_str), true);
  out.Key("datatype", 8, true);
  out.StartObject();
  int nDtype = 0;
  nDtype++;
  out.Key("type", 4, true);
  out.String("array", 5, true);
  nDtype++;
  out.Key("items", 5, true);
  out.StartArray();
  // Loop over string
  int mres;
  size_t sind, eind, beg = 0, end;
  char ifmt[FMT_LEN + 1];
  char re_fmt[FMT_LEN + 1];
  char re_fmt_eof[FMT_LEN + 1];
  snprintf(re_fmt, FMT_LEN, "%%[^%s%s ]+[%s%s ]", "\t", "\n", "\t", "\n");
  snprintf(re_fmt_eof, FMT_LEN, "%%[^%s%s ]+", "\t", "\n");
  size_t iprecision = 0;
  size_t nOuter = 0;
  const char* element_type;
  if (as_array)
    element_type = "ndarray";
  else
    element_type = "scalar";
  while (beg < strlen(format_str)) {
    char isubtype[FMT_LEN] = "";
    mres = find_match(re_fmt, format_str + beg, &sind, &eind);
    if (mres < 0) {
      ygglog_throw_error("format_str2metadata: find_match returned %d", mres);
    } else if (mres == 0) {
      // Make sure its not just a format string with no newline
      mres = find_match(re_fmt_eof, format_str + beg, &sind, &eind);
      if (mres <= 0) {
	beg++;
	continue;
      }
    }
    beg += sind;
    end = beg + (eind - sind);
    strncpy(ifmt, format_str + beg, end-beg);
    ifmt[end-beg] = '\0';
    // String
    if (find_match("%(.*)s", ifmt, &sind, &eind)) {
      strncpy(isubtype, "string", FMT_LEN); // or unicode
      mres = regex_replace_sub(ifmt, FMT_LEN,
			       "%(\\.)?([[:digit:]]*)s(.*)", "$2", 0);
      iprecision = atoi(ifmt);
      // Complex
#ifdef _WIN32
    } else if (find_match("(%.*[fFeEgG]){2}j", ifmt, &sind, &eind)) {
#else
    } else if (find_match("(\%.*[fFeEgG]){2}j", ifmt, &sind, &eind)) {
#endif
      strncpy(isubtype, "complex", FMT_LEN);
      iprecision = 2 * sizeof(double);
    }
    // Floats
    else if (find_match("%.*[fFeEgG]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "float", FMT_LEN);
      iprecision = sizeof(double);
    }
    // Integers
    else if (find_match("%.*hh[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = sizeof(char);
    } else if (find_match("%.*h[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = sizeof(short);
    } else if (find_match("%.*ll[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = sizeof(long long);
    } else if (find_match("%.*l64[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = sizeof(long long);
    } else if (find_match("%.*l[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = sizeof(long);
    } else if (find_match("%.*[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = sizeof(int);
    }
    // Unsigned integers
    else if (find_match("%.*hh[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = sizeof(unsigned char);
    } else if (find_match("%.*h[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = sizeof(unsigned short);
    } else if (find_match("%.*ll[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = sizeof(unsigned long long);
    } else if (find_match("%.*l64[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = sizeof(unsigned long long);
    } else if (find_match("%.*l[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = sizeof(unsigned long);
    } else if (find_match("%.*[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = sizeof(unsigned int);
    } else {
      ygglog_throw_error("format_str2metadata: Could not parse format string: %s", ifmt);
    }
    ygglog_debug("isubtype = %s, iprecision = %lu, ifmt = %s",
		 isubtype, iprecision, ifmt);
    if (!add_dtype(&out, element_type, isubtype, iprecision)) {
      ygglog_throw_error("format_str2metadata: Error in add_dtype");
    }
    nOuter++;
    beg = end;
  }
  out.EndArray(nOuter);
  if (nOuter == 1) {
    nDtype++;
    out.Key("allowSingular", 13, true);
    out.Bool(true);
  }
  out.EndObject(nDtype);
  out.EndObject(2);
  out.EndObject(1);
  out.FinalizeFromStack();
  // if (nOuter == 1) {
  //   typename rapidjson::Document::ValueType tmp;
  //   out["serializer"]["datatype"].Swap(tmp);
  //   out["serializer"]["datatype"].Swap(tmp["items"][0]);
  //   out["serializer"].RemoveMember("format_str");
  // }
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

  bool isValid() {
    return (flags & HEAD_FLAG_VALID);
  }
  void invalidate() {
    flags &= ~HEAD_FLAG_VALID;
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
    if (strcmp(buf, YGG_MSG_EOF) == 0) {
      flags |= HEAD_FLAG_EOF;
      metaOnly = true;
    }
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
  
#define GET_SET_METHOD_(type_in, type_out, method, setargs)		\
  type_out GetMeta ## method(const std::string name) {			\
    if (!(metadata.IsObject() && metadata.HasMember("__meta__")))	\
      ygglog_throw_error("Get%s: No __meta__ in metadata", #method);	\
    rapidjson::Value &meta_doc = metadata["__meta__"];			\
    if (!(meta_doc.HasMember(name.c_str())))				\
      ygglog_throw_error("Get%s: No %s information in the header.", #method, name.c_str()); \
    if (!(meta_doc[name.c_str()].Is ## method()))			\
      ygglog_throw_error("Get%s: %s is not %s.", #method, name.c_str(), #type_in); \
    return meta_doc[name.c_str()].Get ## method();			\
  }									\
  type_out GetMeta ## method ## Optional(const std::string name, type_out defV) { \
    if (!(metadata.IsObject() && metadata.HasMember("__meta__")))	\
      ygglog_throw_error("Get%s: No __meta__ in metadata", #method);	\
    rapidjson::Value &meta_doc = metadata["__meta__"];			\
    if (!(meta_doc.HasMember(name.c_str())))				\
      return defV;							\
    if (!(meta_doc[name.c_str()].Is ## method()))			\
      ygglog_throw_error("Get%s: %s is not %s.", #method, name.c_str(), #type_in); \
    return meta_doc[name.c_str()].Get ## method();			\
  }									\
  bool SetMeta ## method(const std::string name, type_in x) {		\
    if (!(metadata.IsObject() && metadata.HasMember("__meta__")))	\
      ygglog_throw_error("Set%s: No __meta__ in metadata", #method);	\
    rapidjson::Value &meta_doc = metadata["__meta__"];			\
    rapidjson::Value x_val setargs;					\
    meta_doc.AddMember(rapidjson::Value(name.c_str(), name.size(),	\
					metadata.GetAllocator()).Move(),\
		       x_val, metadata.GetAllocator());			\
    return true;							\
  }
  GET_SET_METHOD_(int, int, Int, (x));
  GET_SET_METHOD_(bool, bool, Bool, (x));
  // GET_SET_METHOD_(const char*, String, (x, strlen(x), metadata.GetAllocator()));
  GET_SET_METHOD_(const std::string&, const char*, String, (x.c_str(), x.size(), metadata.GetAllocator()));
#undef GET_SET_METHOD_
  bool SetMetaID(const std::string name, const char** id=NULL) {
    char new_id[100];
    snprintf(new_id, 100, "%d", rand());
    bool out = SetMetaString(name, new_id);
    if (out && id)
      id[0] = GetMetaString(name);
    return out;
  }
  bool SetMetaID(const std::string name, std::string& id) {
    const char* id_str;
    bool out = SetMetaID(name, &id_str);
    if (out)
      id.assign(id_str);
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
