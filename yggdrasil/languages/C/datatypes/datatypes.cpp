#include "../tools.h"
#include "datatypes.h"
#include "utils.h"
#include "../python_wrapper.h"

#define RAPIDJSON_YGGDRASIL
#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/schema.h"


#define CSafe(x)  \
  try		  \
    {		  \
      x;	  \
    }		  \
  catch(...)	  \
    {		  \
      ygglog_error("C++ exception thrown.");	\
    }

// C++ functions
rapidjson::Document::AllocatorType& generic_allocator(generic_t& x) {
  if (x.allocator)
    return ((rapidjson::Document::AllocatorType*)(x.allocator))[0];
  if (x.obj == NULL)
    ygglog_throw_error("generic_allocator: Not initialized");
  return ((rapidjson::Document*)(x.obj))->GetAllocator();
};

rapidjson::Document::AllocatorType& dtype_allocator(dtype_t& x) {
  rapidjson::Document* s = NULL;
  if (x.metadata != NULL)
    s = (rapidjson::Document*)(x.metadata);
  else if (x.schema != NULL)
    s = (rapidjson::Document*)(x.schema);
  else
    ygglog_throw_error("dtype_allocator: Not initialized");
  return s->GetAllocator();
};

rapidjson::Document* type_from_doc(const rapidjson::Value &type_doc) {
  if (!(type_doc.IsObject()))
    ygglog_throw_error("type_from_doc: Parsed document is not an object.");
  if (!(type_doc.HasMember("serializer") || !type_doc["serializer"].IsObject()))
    ygglog_throw_error("type_from_doc: Parsed document does not have a serializer field");
  if (!(type_doc["serializer"].HasMember("datatype")) || !type_doc["serializer"]["datatype"].IsObject())
    ygglog_throw_error("type_from_doc: Parsed document does not have datatype field");
  rapidjson::Document* out = new rapidjson::Document;
  type_doc["serializer"]["datatype"].Accept(*out);
  out->FinalizeFromStack();
  return out;
};


rapidjson::Document* type_from_header_doc(const rapidjson::Value &header_doc) {
  if (!(header_doc.IsObject()))
    ygglog_throw_error("type_from_header_doc: Parsed document is not an object.");
  if (!(header_doc.HasMember("serializer")))
    ygglog_throw_error("type_from_header_doc: Parsed header dosn't contain serializer information.");
  if (!(header_doc["serializer"].IsObject()))
    ygglog_throw_error("type_from_header_doc: Serializer info in parsed header is not an object.");
  if (!(header_doc["serializer"].HasMember("datatype")))
    ygglog_throw_error("type_from_header_doc: Parsed header dosn't contain type information.");
  if (!(header_doc["serializer"]["datatype"].IsObject()))
    ygglog_throw_error("type_from_header_doc: Type information in parsed header is not an object.");
  // TODO: Add information from header_doc like format_str?
  return type_from_doc(header_doc["serializer"]["datatype"]);
};


bool update_header_from_doc(comm_head_t &head, rapidjson::Value &head_doc) {
  // Type
  if (!(head_doc.IsObject())) {
    ygglog_error("update_header_from_doc: head document must be an object.");
    return false;
  }
  // Meta
  if (!(head_doc.HasMember("__meta__"))) {
    ygglog_error("update_header_from_doc: No __meta__ information in the header.");
    return false;
  }
  rapidjson::Value &meta_doc = head_doc["__meta__"];
  // Size
  if (!(meta_doc.IsObject())) {
    ygglog_error("update_header_from_doc: __meta__ is not an object.");
    return false;
  }
  if (!(meta_doc.HasMember("size"))) {
    ygglog_error("update_header_from_doc: No size information in the header.");
    return false;
  }
  if (!(meta_doc["size"].IsInt())) {
    ygglog_error("update_header_from_doc: Size is not integer.");
    return false;
  }
  head.size = (size_t)(meta_doc["size"].GetInt());
  if (head.bodysiz < head.size) {
    head.flags = head.flags | HEAD_FLAG_MULTIPART;
  } else {
    head.flags = head.flags & ~HEAD_FLAG_MULTIPART;
  }
  // Flag specifying that type is in data
  if (meta_doc.HasMember("in_data")) {
    if (!(meta_doc["in_data"].IsBool())) {
      ygglog_error("update_header_from_doc: in_data is not boolean.");
      return false;
    }
    if (meta_doc["in_data"].GetBool()) {
      head.flags = head.flags | HEAD_META_IN_DATA;
    } else {
      head.flags = head.flags & ~HEAD_META_IN_DATA;
    }
  }
  // String fields
  const char **n;
  const char *string_fields[] = {"address", "id", "request_id", "response_address",
				 "zmq_reply", "zmq_reply_worker",
				 "model", ""};
  n = string_fields;
  while (strcmp(*n, "") != 0) {
    if (meta_doc.HasMember(*n)) {
      if (!(meta_doc[*n].IsString())) {
	ygglog_error("update_header_from_doc: '%s' is not a string.", *n);
	return false;
      }
      char *target = NULL;
      size_t target_size = COMMBUFFSIZ;
      if (strcmp(*n, "address") == 0) {
	target = head.address;
      } else if (strcmp(*n, "id") == 0) {
	target = head.id;
      } else if (strcmp(*n, "request_id") == 0) {
	target = head.request_id;
      } else if (strcmp(*n, "response_address") == 0) {
	target = head.response_address;
      } else if (strcmp(*n, "zmq_reply") == 0) {
	target = head.zmq_reply;
      } else if (strcmp(*n, "zmq_reply_worker") == 0) {
	target = head.zmq_reply_worker;
      } else if (strcmp(*n, "model") == 0) {
	target = head.model;
      } else {
	ygglog_error("update_header_from_doc: '%s' not handled.", *n);
	return false;
      }
      const char *str = meta_doc[*n].GetString();
      size_t len = meta_doc[*n].GetStringLength();
      if (len > target_size) {
	ygglog_error("update_header_from_doc: Size of value for key '%s' (%d) exceeds size of target buffer (%d).",
		     *n, len, target_size);
	return false;
      }
      strncpy(target, str, target_size);
    }
    n++;
  }
  rapidjson::Document* metadata = new rapidjson::Document();
  if (!head_doc.Accept(*(metadata))) {
    ygglog_error("update_header_from_doc: Error copying header data.");
    return false;
  }
  metadata->FinalizeFromStack();
  head.metadata = (void*)metadata;
  if (head_doc.HasMember("serializer") &&
      head_doc["serializer"].IsObject() &&
      head_doc["serializer"].HasMember("datatype") &&
      head_doc["serializer"]["datatype"].IsObject()) {
    head.dtype = (void*)(&((*metadata)["serializer"]["datatype"]));
  }
  
  // Return
  return true;
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
  if (!d->String(type, strlen(type), true))
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
    if (!d->String(subtype, strlen(subtype), true))
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
    if (!d->String(units, strlen(units), true))
      return false;
    N++;
  }
  // end
  return d->EndObject(N);
}

rapidjson::Document* copy_document(rapidjson::Value* rhs) {
  rapidjson::Document* out = NULL;
  if (rhs != NULL) {
    out = new rapidjson::Document();
    if (!rhs->Accept(*out)) {
      delete out;
      ygglog_throw_error("copy_document: Error");
    }
    out->FinalizeFromStack();
  }
  return out;
}

std::string document2string(rapidjson::Value* rhs, const char* indent="") {
  if (rhs == NULL) {
    ygglog_error("document2string: NULL document");
    return std::string("");
  }
  rapidjson::StringBuffer sb;
  rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(sb, 0, strlen(indent));
  writer.SetYggdrasilMode(true);
  if (!rhs->Accept(writer)) {
    ygglog_error("document2string: Error in Accept(writer)");
    return std::string("");
  }
  return std::string(sb.GetString());
}

void display_document(rapidjson::Value* rhs, const char* indent="") {
  std::string s = document2string(rhs, indent);
  printf("%s\n", s.c_str());
}

rapidjson::Document* create_dtype_format_class(const char *format_str,
					       const int as_array = 0) {
  rapidjson::Document* out = new rapidjson::Document;
  out->StartObject();
  out->Key("serializer", 10, true);
  out->StartObject();
  out->Key("format_str", 10, true);
  out->String(format_str, strlen(format_str), true);
  out->Key("datatype", 8, true);
  out->StartObject();
  out->Key("type", 4, true);
  out->String("array", 5, true);
  out->Key("items", 5, true);
  out->StartArray();
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
      ygglog_throw_error("create_dtype_format_class: find_match returned %d", mres);
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
    if (find_match("%.*s", ifmt, &sind, &eind)) {
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
      ygglog_throw_error("create_dtype_format_class: Could not parse format string: %s", ifmt);
    }
    ygglog_debug("isubtype = %s, iprecision = %lu, ifmt = %s",
		 isubtype, iprecision, ifmt);
    if (!add_dtype(out, element_type, isubtype, iprecision)) {
      ygglog_throw_error("create_dtype_format_class: Error in add_dtype");
    }
    nOuter++;
    beg = end;
  }
  out->EndArray(nOuter);
  // if (nOuter == 1) {
  //   out->Key("allowSingular", 13, true);
  //   out->Bool(true);
  //   out->EndObject(3);
  // } else {
  //   out->EndObject(2);
  // }
  out->EndObject(2);
  out->EndObject(2);
  out->EndObject(1);
  out->FinalizeFromStack();
  if (nOuter == 1) {
    typename rapidjson::Document::ValueType tmp;
    (*out)["serializer"]["datatype"].Swap(tmp);
    (*out)["serializer"]["datatype"].Swap(tmp["items"][0]);
    (*out)["serializer"].RemoveMember("format_str");
  }
  return out;
};

rapidjson::Document* encode_schema(rapidjson::Value* document) {
  rapidjson::SchemaEncoder encoder(true);
  if (!document->Accept(encoder)) {
    ygglog_throw_error("encode_schema: Error in schema encoding.");
  }
  rapidjson::Document* s = new rapidjson::Document();
  if (!encoder.Accept(*s)) {
    ygglog_throw_error("encode_schema: Error in getting encoded schema.");
  }
  s->FinalizeFromStack();
  return s;
}

template <typename Validator>
void throw_validator_error(const char* source, Validator& n) {
  rapidjson::Value err;
  typename rapidjson::Document::AllocatorType allocator;
  n.GetErrorMsg(err, allocator);
  rapidjson::StringBuffer sb;
  rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(sb);
  if (!err.Accept(writer)) {
    ygglog_throw_error("%s: Error displaying normalization error", source);
  }
  ygglog_throw_error("%s:\n%s\n", source, sb.GetString());
}

int normalize_document(rapidjson::Document* d, rapidjson::Document* s,
		       bool dont_raise=false) {
  if (d == NULL)
    return 0;
  if (s == NULL)
    return 0;
  rapidjson::SchemaDocument sd(*s);
  rapidjson::SchemaNormalizer normalizer(sd);
  if (!d->Accept(normalizer)) {
    if (dont_raise)
      return 0;
    display_document(d);
    throw_validator_error("normalize_document", normalizer);
  }
  if (normalizer.WasNormalized()) {
    d->SetNull();
    if (!normalizer.GetNormalized().Accept(*d))
      return 0;
    d->FinalizeFromStack();
  }
  return 1;
}

void dtype_schema(rapidjson::Value& s,
		  typename rapidjson::Document::AllocatorType& allocator,
		  bool is_metadata = false) {
  s.SetObject();
  if (is_metadata) {
#define ADD_OBJECT_(x, name, len)					\
    x.AddMember(rapidjson::Value("type", 4, allocator).Move(),		\
		rapidjson::Value("object", 6, allocator).Move(),	\
		allocator);						\
    x.AddMember(rapidjson::Value("properties", 10, allocator).Move(),	\
		rapidjson::Value(rapidjson::kObjectType).Move(),	\
		allocator);						\
    x["properties"].AddMember(rapidjson::Value(#name, len, allocator).Move(), \
			      rapidjson::Value(rapidjson::kObjectType).Move(), \
			      allocator)
    ADD_OBJECT_(s, serializer, 10);
    ADD_OBJECT_(s["properties"]["serializer"], datatype, 8);
#undef ADD_OBJECT_
    dtype_schema(s["properties"]["serializer"]["properties"]["datatype"], allocator);
  } else {
    s.AddMember(rapidjson::Value("type", 4, allocator).Move(),
		rapidjson::Value("schema", 6, allocator).Move(),
		allocator);
  }
}

dtype_t* create_dtype(rapidjson::Document* document=NULL,
		      const bool use_generic=false,
		      bool encode=false, bool is_metadata=false) {
  dtype_t* out = NULL;
  out = (dtype_t*)malloc(sizeof(dtype_t));
  typename rapidjson::Document::AllocatorType* allocator = NULL;
  if (out == NULL) {
    ygglog_throw_error("create_dtype: Failed to malloc for datatype.");
  }
  out->schema = NULL;
  out->metadata = NULL;
  if (use_generic && document == NULL && !encode) {
    document = new rapidjson::Document(rapidjson::kObjectType);
    is_metadata = false;
  }
  if (document != NULL) {
    if (encode) {
      out->schema = (void*)(encode_schema(document));
      allocator = &(((rapidjson::Document*)(out->schema))->GetAllocator());
    } else {
      rapidjson::Document s;
      dtype_schema(s, s.GetAllocator(), is_metadata);
      if (!normalize_document(document, &s)) {
	ygglog_throw_error("create_dtype: Failed to normalize schema.");
      }
      allocator = &(document->GetAllocator());
      if (is_metadata) {
	out->metadata = (void*)document;
	if (document->HasMember("serializer") &&
	    (*document)["serializer"].IsObject() &&
	    (*document)["serializer"].HasMember("datatype") &&
	    (*document)["serializer"]["datatype"].IsObject()) {
	  out->schema = (void*)(&((*document)["serializer"]["datatype"]));
	}
      } else {
	out->schema = (void*)document;
      }
    }
    if (use_generic) {
      ((rapidjson::Value*)out->schema)->AddMember(rapidjson::Value("use_generic", 11, *allocator).Move(),
						  rapidjson::Value(true).Move(),
						  *allocator);
    }
  }
  return out;
};


rapidjson::StringBuffer format_comm_header_json(const comm_head_t head,
						const int no_type,
						const bool meta_only=false) {
  rapidjson::StringBuffer head_buf;
  rapidjson::Writer<rapidjson::StringBuffer> head_writer(head_buf);
  rapidjson::Document* metadata = (rapidjson::Document*)(head.metadata);
  rapidjson::Value* datatype = (rapidjson::Value*)(head.dtype);
  head_writer.StartObject();
  // Metadata
  head_writer.Key("__meta__");
  head_writer.StartObject();
  head_writer.Key("size");
  head_writer.Int((int)(head.size));
  if (head.flags & HEAD_META_IN_DATA) {
    head_writer.Key("in_data");
    head_writer.Bool(true);
  }
  // Metadata strings
  const char **n;
  const char *string_fields[] = {"address", "id", "request_id", "response_address",
				 "zmq_reply", "zmq_reply_worker",
				 "model", ""};
  n = string_fields;
  while (strcmp(*n, "") != 0) {
    const char *target = NULL;
    if (strcmp(*n, "address") == 0) {
      target = head.address;
    } else if (strcmp(*n, "id") == 0) {
      target = head.id;
    } else if (strcmp(*n, "request_id") == 0) {
      target = head.request_id;
    } else if (strcmp(*n, "response_address") == 0) {
      target = head.response_address;
    } else if (strcmp(*n, "zmq_reply") == 0) {
      target = head.zmq_reply;
    } else if (strcmp(*n, "zmq_reply_worker") == 0) {
      target = head.zmq_reply_worker;
    } else if (strcmp(*n, "model") == 0) {
      target = head.model;
    } else {
      ygglog_throw_error("format_comm_header_json: '%s' not handled.", *n);
    }
    if (strlen(target) > 0) {
      head_writer.Key(*n);
      head_writer.String(target);
    }
    n++;
  }
  head_writer.EndObject();
  if (meta_only) {
    head_writer.EndObject();
    return head_buf;
  }
  // Type
  // if ((!(head.flags & HEAD_META_IN_DATA)) && !no_type && head.dtype != NULL) {
  //   head_writer.Key("serializer");
  //   head_writer.StartObject();
  //   head_writer.Key("datatype");
  //   rapidjson::Document* datatype = (rapidjson::Document*)(head.dtype);
  //   if (!datatype.Accept(head_writer))
  //     ygglog_throw_error("format_comm_header_json: Error encoding type.");
  //   if (metadata && metadata->IsObject() && metadata->HasMember("serializer")) {
  //     for (typename rapidjson::Document::ConstMemberIterator it = (*metadata)["serializer"].MemberBegin();
  // 	   it != (*metadata)["serializer"].MemberEnd(); it++) {
  // 	if (strcmp(it->first.GetString(), "datatype") == 0)
  // 	  continue;
  // 	head_writer.Key(it->first.GetString(), it->first.GetStringLength(), true);
  // 	if (!it->second.Accept(head_writer))
  // 	  ygglog_throw_error("format_comm_header_json: Error encoding serializer");
  //     }
  //   }
  //   head_writer.EndObject();
  // }
  // Additional header kwargs
  if (metadata && metadata->IsObject()) {
    for (typename rapidjson::Document::ConstMemberIterator it = metadata->MemberBegin();
	 it != metadata->MemberEnd(); it++) {
      if (((head.flags & HEAD_META_IN_DATA) || no_type) &&
	  strcmp(it->name.GetString(), "serializer") == 0)
	continue;
      head_writer.Key(it->name.GetString(), it->name.GetStringLength(), true);
      if (!it->value.Accept(head_writer))
	ygglog_throw_error("format_comm_header_json: Error adding user metadata");
    }
  } else if (datatype && datatype->IsObject() &&
	     !((head.flags & HEAD_META_IN_DATA) || no_type)) {
    head_writer.Key("serializer", 10, true);
    head_writer.StartObject();
    head_writer.Key("datatype", 8, true);
    if (!datatype->Accept(head_writer))
      ygglog_throw_error("format_comm_header_json: Error adding datatype");
    head_writer.EndObject();
  }
  head_writer.EndObject();
  return head_buf;
};

rapidjson::Document* type_from_pyobj(PyObject* pyobj) {
  rapidjson::Value d(pyobj);
  return encode_schema(&d);
};

size_t is_document_format_array(rapidjson::Value* d,
				bool get_nelements = false) {
  if (!(d->IsArray() && d->Size() > 0))
    return 0;
  size_t nelements = 0;
  size_t i = 0;
  for (typename rapidjson::Value::ConstValueIterator it = d->Begin();
       it != d->End(); it++, i++) {
    if (!it->IsNDArray())
      return 0;
    size_t it_nelements = (size_t)(it->GetNElements());
    if (i == 0) {
      nelements = it_nelements;
    } else if (nelements != it_nelements) {
      return 0;
    }
  }
  if (get_nelements)
    return nelements;
  return 1;
};

size_t is_schema_format_array(rapidjson::Value* d,
			      bool get_nelements = false) {
  if (!(d->IsObject() && d->HasMember("type")))
    return 0;
  if ((*d)["type"] != rapidjson::Document::GetArrayString())
    return 0;
  if (!d->HasMember("items"))
    return 0;
  if (!(*d)["items"].IsArray())
    return 0;
  if ((*d)["items"].Size() == 0)
    return 0;
  size_t nelements = 0;
  size_t i = 0;
  for (typename rapidjson::Value::ConstValueIterator it = (*d)["items"].Begin();
       it != (*d)["items"].End(); it++, i++) {
    if (!(it->HasMember("type") && (*it)["type"].IsString() &&
	  ((*it)["type"] == rapidjson::Document::GetNDArrayString() ||
	   (*it)["type"] == rapidjson::Document::Get1DArrayString()))) {
      return 0;
    }
    size_t it_nelements = 0;
    if (it->HasMember("length") && (*it)["length"].IsInt())
      it_nelements = (size_t)((*it)["length"].GetInt());
    else if (it->HasMember("shape") && (*it)["shape"].IsArray()) {
      it_nelements = 1;
      for (typename rapidjson::Value::ConstValueIterator sit = (*it)["shape"].Begin();
	   sit != (*it)["shape"].End(); sit++) {
	it_nelements *= (size_t)(sit->GetInt());
      }
    }
    if (i == 0) {
      nelements = it_nelements;
    } else if (nelements != it_nelements) {
      return 0;
    }
  }
  if (get_nelements)
    return nelements;
  return 1;
};

int schema_count_vargs(rapidjson::Value& schema, size_t& count,
		       size_t table_nelements = 0,
		       int for_fortran_recv = 0) {
  if (!(schema.IsObject() && schema.HasMember("type") && schema["type"].IsString()))
    return 0;
  bool use_generic = false;
  std::string schema_type(schema["type"].GetString());
  if (schema.HasMember("use_generic") &&
      schema["use_generic"].IsBool() &&
      schema["use_generic"].GetBool()) {
    use_generic = true;
  }
  if (use_generic) {
    count++;
  }
  else if (schema_type == std::string("string")) {
    count += 2; // value & precision
  }
  else if (schema_type == std::string("array")) {
    if (!(schema.HasMember("items") && schema["items"].IsArray()))
      ygglog_throw_error("schema_count_vargs: Schema must have an array as its items member.");
    size_t nelements = is_schema_format_array(&schema);
    if (nelements) {
      count++; // Number of rows
    }
    for (typename rapidjson::Value::ValueIterator it = schema["items"].Begin();
	 it != schema["items"].End(); it++) {
      
      if (!schema_count_vargs(*it, count, nelements))
	return 0;
    }
  }
  else if (schema_type == std::string("object")) {
    if (!(schema.HasMember("properties") && schema["properties"].IsObject()))
      ygglog_throw_error("schema_count_vargs: Schema must have an object as its properties member");
    for (typename rapidjson::Value::MemberIterator it = schema["properties"].MemberBegin();
	 it != schema["properties"].MemberEnd(); it++) {
      if (!schema_count_vargs(it->value, count))
	return 0;
    }
  }
  else if (schema_type == std::string("scalar")) {
    if (!(schema.HasMember("subtype") && schema["subtype"].IsString()))
      ygglog_throw_error("schema_count_vargs: Scalar schema must contain a string subtype member");
    std::string schema_subtype(schema["subtype"].GetString());
    if (schema_subtype == std::string("string")) {
      count += 2; // value & precision
    } else {
      count++;
    }
  }
  else if (schema_type == std::string("ndarray") ||
	   schema_type == std::string("1darray")) {
    if (!(schema.HasMember("subtype") && schema["subtype"].IsString()))
      ygglog_throw_error("schema_count_vargs: ndarray schema must contain a string subtype member");
    int schema_ndim = 0;
    bool has_shape = false;
    std::string schema_subtype(schema["subtype"].GetString());
    if (schema_type == std::string("1darray")) {
      schema_ndim = 1;
    }
    if (schema.HasMember("length") && schema["length"].IsInt()) {
      schema_ndim = 1;
      has_shape = true;
    } else if (schema.HasMember("shape") && schema["shape"].IsArray()) {
      schema_ndim = (int)(schema["shape"].Size());
      has_shape = true;
    }
    if (schema_ndim == 0 && schema.HasMember("ndim") && schema["ndim"].IsInt())
      schema_ndim = schema["ndim"].GetInt();
    count++;
    if (!(has_shape || table_nelements)) {
      if (schema_ndim == 1)
	count++; // length
      else
	count += 2; // ndim & shape
    }
    if ((for_fortran_recv || !table_nelements) &&
	(schema_subtype == std::string("string"))) {
      count++; // precision
    }
  } else {
    count++;
  }
  return 1;
};

int document_count_vargs(rapidjson::Value& document,
			 rapidjson::Value& schema, size_t& count,
			 size_t table_nelements = 0) {
  bool use_generic = false;
  if (schema.HasMember("use_generic") &&
      schema["use_generic"].IsBool() &&
      schema["use_generic"].GetBool()) {
    use_generic = true;
  }
  if (use_generic) {
    count++;
    return 1;
  }
  switch (document.GetType()) {
  case (rapidjson::kNullType):
  case (rapidjson::kFalseType):
  case (rapidjson::kTrueType):
  case (rapidjson::kNumberType): {
    count++;
    break;
  }
  case (rapidjson::kStringType): {
    if (!document.IsYggdrasil()) {
      count += 1;
      return 1;
    }
    const rapidjson::Value& type = document.GetYggType();
    if (type == rapidjson::Document::GetScalarString() ||
	type == rapidjson::Document::Get1DArrayString() ||
	type == rapidjson::Document::GetNDArrayString()) {
      enum rapidjson::YggSubType subtype = document.GetSubTypeCode();
      count += 1;
      bool has_shape = ((schema.HasMember("shape") && schema["shape"].IsArray()) ||
			(schema.HasMember("length") && schema["length"].IsInt()));
      if (!(has_shape || table_nelements)) {
	if (type == rapidjson::Document::Get1DArrayString()) {
	  count += 1; // Length
	} else if (type == rapidjson::Document::GetNDArrayString()) {
	  count += 2; // NDim & shape
	}
      }
      if (!table_nelements && subtype == rapidjson::kYggStringSubType)
	count += 1; // Precision
    } else {
      count += 1;
    }
    break;
  }
  case (rapidjson::kObjectType): {
    if (!document.IsYggdrasil()) {
      count += 1;
      return 1;
    }
    if (!(schema.HasMember("properties") && schema["properties"].IsObject()))
      ygglog_throw_error("document_count_vargs: schema for object must contain a properties member");
    for (typename rapidjson::Value::MemberIterator it = document.MemberBegin();
	 it != document.MemberEnd(); it++) {
      if (!document_count_vargs(it->value, schema["properties"][it->name],
				count))
	return 0;
    }
  }
  case (rapidjson::kArrayType): {
    if (!(schema.HasMember("items") && (schema["items"].IsArray() ||
					schema["items"].IsObject())))
      ygglog_throw_error("document_count_vargs: schema for array must contain an items member");
    size_t nelements = is_document_format_array(&document);
    if (nelements) {
      count++; // Number of rows
    }
    size_t i = 0;
    for (typename rapidjson::Value::ValueIterator it = document.Begin();
	 it != document.End(); it++) {
      if (schema["items"].IsArray()) {
	if (!document_count_vargs(*it, schema["items"][i],
				  count, nelements))
	  return 0;
      } else {
	if (!document_count_vargs(*it, schema["items"],
				  count, nelements))
	  return 0;
      }
    }
    break;
  }
  }
  return 1;
}

int document_get_vargs(rapidjson::Value& document,
		       rapidjson::Value& schema,
		       va_list_t &ap, rapidjson::Document& d,
		       size_t table_nelements = 0) {
  if (!(schema.IsObject() && schema.HasMember("type") && schema["type"].IsString())) {
    ygglog_throw_error("document_get_vargs: Schema must be an object containing a 'type' string property.");
  }
  std::string schema_type(schema["type"].GetString());
#define CASE_STD_(name, method, type)				\
  if (schema_type == std::string(#name)) {			\
    type tmp;							\
    if (!pop_va_list(ap, tmp)) {				\
      return 0;							\
    }								\
    method;							\
  }
  bool use_generic = false;
  if (schema.HasMember("use_generic") &&
      schema["use_generic"].IsBool() &&
      schema["use_generic"].GetBool()) {
    use_generic = true;
  }
  if (use_generic || schema_type == std::string("any") || schema_type == std::string("schema")) {
    generic_t tmp;
    if (!pop_va_list(ap, tmp))
      return 0;
    rapidjson::Value* x_doc = (rapidjson::Value*)(tmp.obj);
    document.CopyFrom(*x_doc, d.GetAllocator());
  }
  else CASE_STD_(null, document.SetNull(), void*)
  else CASE_STD_(boolean, document.SetBool((bool)tmp), int)
  else CASE_STD_(integer, document.SetInt(tmp), int)
  else CASE_STD_(number, document.SetDouble(tmp), double)
  else if (schema_type == std::string("string")) {
    char* tmp;
    size_t tmp_len;
    if (!pop_va_list(ap, tmp))
      return 0;
    if (!pop_va_list(ap, tmp_len))
      return 0;
    document.SetString(tmp, (rapidjson::SizeType)tmp_len, d.GetAllocator());
  }
  else if (schema_type == std::string("array")) {
    if (!(schema.HasMember("items") && schema["items"].IsArray()))
      ygglog_throw_error("document_get_vargs: Schema must have an array as its items member.");
    size_t nelements = 0;
    if (is_schema_format_array(&schema)) {
      if (!pop_va_list(ap, nelements))
	return 0;
    }
    document.SetArray();
    document.Reserve(schema["items"].Size(), d.GetAllocator());
    for (typename rapidjson::Value::ValueIterator it = schema["items"].Begin();
	 it != schema["items"].End(); it++) {
      rapidjson::Value item;
      if (!document_get_vargs(item, *it, ap, d, nelements))
	return 0;
      document.PushBack(item, d.GetAllocator());
    }
  }
  else if (schema_type == std::string("object")) {
    if (!(schema.HasMember("properties") && schema["properties"].IsObject()))
      ygglog_throw_error("document_get_vargs: Schema must have an object as its properties member");
    document.SetObject();
    document.MemberReserve(schema["properties"].MemberCount(), d.GetAllocator());
    for (typename rapidjson::Value::MemberIterator it = schema["properties"].MemberBegin();
	 it != schema["properties"].MemberEnd(); it++) {
      rapidjson::Value item;
      if (!document_get_vargs(item, it->value, ap, d))
	return 0;
      document.AddMember(rapidjson::Value(it->name, d.GetAllocator()).Move(),
			 item, d.GetAllocator());
    }
  }
  else if (schema_type == std::string("scalar")) {
    if (!(schema.HasMember("subtype") && schema["subtype"].IsString()))
      ygglog_throw_error("document_get_vargs: Scalar schema must contain a string subtype member");
    std::string schema_subtype(schema["subtype"].GetString());
    bool is_string = (schema_subtype == std::string("string") ||
		      schema_subtype == std::string("bytes") ||
		      schema_subtype == std::string("unicode"));
    rapidjson::Value schema_cpy(schema, d.GetAllocator());
    int schema_precision = 0;
    if (schema.HasMember("precision") && schema["precision"].IsInt()) {
      if (!is_string)
	schema_precision = schema["precision"].GetInt();
    } else {
      if (!is_string)
	ygglog_throw_error("document_get_vargs: Scalar %s schema must contain an integer precision member", schema_subtype.c_str());
      else
	schema_cpy.AddMember(rapidjson::Document::GetPrecisionString(), rapidjson::Value(0).Move(), d.GetAllocator());
    }
#define CASE_SCALAR_(subtype, precision, type)				\
    if (schema_subtype == std::string(#subtype) && schema_precision == precision) { \
      type tmp;								\
      if (!pop_va_list(ap, tmp)) {					\
	return 0;							\
      }									\
      document.SetYggdrasilString((const char*)(&tmp), precision,	\
				  d.GetAllocator(), schema_cpy);	\
    }
    CASE_SCALAR_(int, 1, int8_t)
    else CASE_SCALAR_(int, 2, int16_t)
    else CASE_SCALAR_(int, 4, int32_t)
    else CASE_SCALAR_(int, 8, int64_t)
    else CASE_SCALAR_(uint, 1, uint8_t)
    else CASE_SCALAR_(uint, 2, uint16_t)
    else CASE_SCALAR_(uint, 4, uint32_t)
    else CASE_SCALAR_(uint, 8, uint64_t)
    else CASE_SCALAR_(float, 4, float)
    else CASE_SCALAR_(float, 8, double)
    else CASE_SCALAR_(complex, 8, complex_float_t)
    else CASE_SCALAR_(complex, 16, complex_double_t)
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else CASE_SCALAR_(float, 16, long double)
    else CASE_SCALAR_(complex, 32, complex_long_double_t)
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else if (is_string) {
      char* tmp;
      size_t tmp_len;
      if (!pop_va_list(ap, tmp))
	return 0;
      if (!pop_va_list(ap, tmp_len))
	return 0;
      document.SetYggdrasilString(tmp, (rapidjson::SizeType)tmp_len,
				  d.GetAllocator(), schema_cpy);
    }
    else {
      ygglog_throw_error("document_get_vargs: Unsupported subtype and precision combination for scalar: subtype = %s, precision = %d", schema_subtype.c_str(), schema_precision);
    }
#undef CASE_SCALAR_    
  }
  else if (schema_type == std::string("ndarray") ||
	   schema_type == std::string("1darray")) {
    if (!(schema.HasMember("subtype") && schema["subtype"].IsString()))
      ygglog_throw_error("document_get_vargs: ndarray schema must contain a string subtype member");
    int schema_ndim = 0;
    bool has_shape = false;
    size_t nelements = 1;
    rapidjson::Value schema_cpy(schema, d.GetAllocator());
    std::string schema_subtype(schema["subtype"].GetString());
    int schema_precision = 0;
    bool is_string = (schema_subtype == std::string("string") ||
		      schema_subtype == std::string("bytes") ||
		      schema_subtype == std::string("unicode"));
    if (schema.HasMember("precision") && schema["precision"].IsInt()) {
      schema_precision = schema["precision"].GetInt();
    } else {
      if ((!is_string) || (is_string && !table_nelements))
	ygglog_throw_error("document_get_vargs: ndarray schema must contain an integer precision member");
      else
	schema_cpy.AddMember(rapidjson::Document::GetPrecisionString(), rapidjson::Value(0).Move(), d.GetAllocator());
    }
    if (schema_type == std::string("1darray")) {
      schema_ndim = 1;
    }
    if (schema.HasMember("length") && schema["length"].IsInt()) {
      schema_ndim = 1;
      has_shape = true;
      nelements *= (size_t)(schema["length"].GetUint());
    } else if (schema.HasMember("shape") && schema["shape"].IsArray()) {
      schema_ndim = (int)(schema["shape"].Size());
      has_shape = true;
      for (typename rapidjson::Value::ValueIterator it = schema["shape"].Begin();
	   it != schema["shape"].End(); it++) {
	nelements *= (size_t)(it->GetUint());
      }
    }
    if (schema_ndim == 0 && schema.HasMember("ndim") && schema["ndim"].IsInt())
      schema_ndim = schema["ndim"].GetInt();
    if (table_nelements) {
      nelements = table_nelements;
    }
    // if (schema_ndim == 0)
    //   ygglog_throw_error("document_get_vargs: Could not determine the number of dimension in the array from the schema");
    if (!has_shape) {
      schema_cpy.AddMember(rapidjson::Document::GetShapeString(),
			   rapidjson::Value(rapidjson::kArrayType).Move(),
			   d.GetAllocator());
      schema_cpy.MemberReserve(schema_ndim, d.GetAllocator());
      if (table_nelements) {
	schema_cpy["shape"].PushBack((rapidjson::SizeType)(table_nelements), d.GetAllocator());
      }
    }
    char* src = NULL;
    size_t src_nbytes = 0;
#define CASE_NDARRAY_(subtype, precision, type)				\
    if (schema_subtype == std::string(#subtype) && schema_precision == precision) { \
      type* tmp = NULL;							\
      src_nbytes = precision;						\
      if (!pop_va_list(ap, tmp)) {					\
	return 0;							\
      }									\
      src = (char*)tmp;							\
    }
    CASE_NDARRAY_(int, 1, int8_t)
    else CASE_NDARRAY_(int, 2, int16_t)
    else CASE_NDARRAY_(int, 4, int32_t)
    else CASE_NDARRAY_(int, 8, int64_t)
    else CASE_NDARRAY_(uint, 1, uint8_t)
    else CASE_NDARRAY_(uint, 2, uint16_t)
    else CASE_NDARRAY_(uint, 4, uint32_t)
    else CASE_NDARRAY_(uint, 8, uint64_t)
    else CASE_NDARRAY_(float, 4, float)
    else CASE_NDARRAY_(float, 8, double)
    else CASE_NDARRAY_(complex, 8, complex_float_t)
    else CASE_NDARRAY_(complex, 16, complex_double_t)
    else CASE_NDARRAY_(string, schema_precision, char)
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else CASE_NDARRAY_(float, 16, long double)
    else CASE_NDARRAY_(complex, 32, complex_long_double_t)
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else {
      ygglog_throw_error("document_get_vargs: Unsupported subtype and precision combination for ndarray: subtype = %s, precision = %d", schema_subtype.c_str(), schema_precision);
    }
    if (!(has_shape || table_nelements)) {
      if (schema_ndim == 1) {
	size_t tmp_len;
	if (!pop_va_list(ap, tmp_len)) {
	  return 0;
	}
	nelements *= tmp_len;
	schema_cpy["shape"].PushBack((rapidjson::SizeType)tmp_len, d.GetAllocator());
      } else {
	size_t tmp_ndim;
	if (!pop_va_list(ap, tmp_ndim)) {
	  return 0;
	}
	size_t* tmp_size = NULL;
	if (!pop_va_list(ap, tmp_size)) {
	  return 0;
	}
	for (size_t i = 0; i < tmp_ndim; i++) {
	  nelements *= tmp_size[i];
	  schema_cpy["shape"].PushBack((rapidjson::SizeType)(tmp_size[i]), d.GetAllocator());
	}
      }
    }
    if ((!table_nelements) && is_string) {
      if (!pop_va_list(ap, src_nbytes)) {
	return 0;
      }
      schema_cpy["precision"].SetUint((unsigned)src_nbytes);
    }
    document.SetYggdrasilString(src, src_nbytes * nelements,
				d.GetAllocator(), schema_cpy);
#undef CASE_NDARRAY_    
  }
#define CASE_GEOMETRY_(name, rjtype)			\
  CASE_STD_(name, rapidjson::rjtype* tmp_obj = (rapidjson::rjtype*)(tmp.obj); document.Set ## rjtype(*tmp_obj), name ## _t)
  else CASE_GEOMETRY_(obj, ObjWavefront)
  else CASE_GEOMETRY_(ply, Ply)
#undef CASE_GEOMETRY_
#define CASE_PYTHON_(name)			\
  CASE_STD_(name, document.SetPythonObjectRaw(tmp.obj), python_t)
  else CASE_PYTHON_(class)
  else CASE_PYTHON_(function)
  else CASE_PYTHON_(instance)
#undef CASE_PYTHON_
  else {
    ygglog_throw_error("document_get_vargs: Unsupported type %s", schema_type.c_str());
  }
#undef CASE_STD_
  return 1;
};

int document_set_vargs(rapidjson::Value& document,
		       rapidjson::Value& schema,
		       va_list_t &ap, int allow_realloc,
		       size_t table_nelements = 0) {
#define BASE_(method, type)				\
    type tmp = method;					\
    if (!set_va_list(ap, tmp, allow_realloc)) {		\
      return 0;						\
    }							\
    break
#define CASE_(code, method, type)			\
  case (rapidjson::code): {				\
    BASE_(method, type);				\
  }
#define CASE_PYTHON_(str)					\
  if (type == rapidjson::Document::Get ## str ## String()) {	\
    python_t tmp;						\
    tmp.obj = document.GetPythonObjectRaw();			\
    if (!set_va_list(ap, tmp, allow_realloc)) {			\
      return 0;							\
    }								\
  }
#define CASE_GEOMETRY_(name, str)				\
  if (type == rapidjson::Document::Get ## str ## String()) {	\
    name ## _t tmp = init_ ## name();				\
    rapidjson::str* tmp_obj = new rapidjson::str();		\
    document.Get ## str(*tmp_obj);				\
    set_ ## name(&tmp, tmp_obj, 0);				\
    if (!set_va_list(ap, tmp, allow_realloc)) {			\
      return 0;							\
    }								\
  }
#define CASE_SCALAR_(subT, prec, type)				\
  if (subtype == rapidjson::subT && prec == precision) {	\
    type tmp = document.GetScalar<type>();			\
    if (!set_va_list(ap, tmp, allow_realloc)) {			\
      return 0;							\
    }								\
  }
#define CASE_NDARRAY_(subT, prec, type)					\
  if (subtype == rapidjson::subT && prec == precision) {		\
    type* dst = (type*)mem;						\
    type** dst_ref = (type**)mem_ref;					\
    type* src = (type*)tmp;						\
    if (!set_va_list_mem(ap, dst, dst_ref, mem_len[0],			\
			 src, tmp_len / sizeof(type), allow_realloc)) {	\
      return 0;								\
    }									\
  }
#define CASE_STRING_							\
  const char* tmp = document.GetString();				\
  size_t tmp_len = (size_t)(document.GetStringLength());		\
  char* mem = NULL;							\
  char** mem_ref = NULL;						\
  size_t* mem_len = NULL;						\
  size_t** mem_len_ref = NULL;						\
  if (!pop_va_list_mem(ap, mem, mem_ref, allow_realloc))		\
    return 0;								\
  if (!pop_va_list_mem(ap, mem_len, mem_len_ref))			\
    return 0;								\
  if (!set_va_list_mem(ap, mem, mem_ref, mem_len[0], tmp, tmp_len, allow_realloc)) \
    return 0
  bool use_generic = false;
  if (schema.HasMember("use_generic") &&
      schema["use_generic"].IsBool() &&
      schema["use_generic"].GetBool()) {
    use_generic = true;
  }
  if (use_generic) {
    rapidjson::Document* tmp_doc = new rapidjson::Document();
    tmp_doc->CopyFrom(document, tmp_doc->GetAllocator());
    generic_t tmp;
    tmp.obj = (void*)(tmp_doc);
    if (!set_va_list(ap, tmp)) {
      return 0;
    }
    return 1;
  }
  switch (document.GetType()) {
  CASE_(kNullType, NULL, void*)
  CASE_(kFalseType, document.GetBool(), bool)
  CASE_(kTrueType, document.GetBool(), bool)
  case (rapidjson::kNumberType): {
    if (document.IsDouble()) {
      BASE_(document.GetDouble(), double);
    } else if (document.IsInt()) {
      BASE_(document.GetInt(), int);
    } else if (document.IsUint()) {
      BASE_(document.GetUint(), unsigned);
    } else if (document.IsInt64()) {
      BASE_(document.GetInt64(), int64_t);
    } else {
      BASE_(document.GetUint64(), uint64_t);
    }
  }
  case (rapidjson::kStringType): {
    if (document.IsYggdrasil()) {
      const rapidjson::Value& type = document.GetYggType();
      if (type == rapidjson::Document::GetScalarString()) {
	enum rapidjson::YggSubType subtype = document.GetSubTypeCode();
	int precision = (int)(document.GetPrecision());
	CASE_SCALAR_(kYggIntSubType, 1, int8_t)
	else CASE_SCALAR_(kYggIntSubType, 2, int16_t)
	else CASE_SCALAR_(kYggIntSubType, 4, int32_t)
	else CASE_SCALAR_(kYggIntSubType, 8, int64_t)
	else CASE_SCALAR_(kYggUintSubType, 1, uint8_t)
	else CASE_SCALAR_(kYggUintSubType, 2, uint16_t)
	else CASE_SCALAR_(kYggUintSubType, 4, uint32_t)
	else CASE_SCALAR_(kYggUintSubType, 8, uint64_t)
	else CASE_SCALAR_(kYggFloatSubType, 4, float)
	else CASE_SCALAR_(kYggFloatSubType, 8, double)
	else CASE_SCALAR_(kYggComplexSubType, 8, std::complex<float>)
	else CASE_SCALAR_(kYggComplexSubType, 16, std::complex<double>)
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
	else CASE_SCALAR_(kYggFloatSubType, 16, long double)
	else CASE_SCALAR_(kYggComplexSubType, 32, std::complex<long double>)
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
	else if (subtype == rapidjson::kYggStringSubType) {
	  // TODO: Encoding
	  CASE_STRING_;
	} else {
	  ygglog_throw_error("document_set_vargs: Unsupported scalar subtype %s", document.GetSubType().GetString());
	}
      } else if (type == rapidjson::Document::Get1DArrayString() ||
		 type == rapidjson::Document::GetNDArrayString()) {
	bool has_shape = false;
	size_t len = 1;
	// if (!ap.for_fortran) {
	if (schema.HasMember("length") && schema["length"].IsInt()) {
	  len = static_cast<size_t>(schema["length"].GetInt());
	  has_shape = true;
	} else if (schema.HasMember("shape") && schema["shape"].IsArray()) {
	  len = 1;
	  for (rapidjson::Value::ConstValueIterator it = schema["shape"].Begin();
	       it != schema["shape"].End(); it++) {
	    len *= static_cast<size_t>(it->GetUint());
	  }
	  has_shape = true;
	}
	// }
	const char* tmp = document.GetString();
	size_t tmp_len = (size_t)(document.GetNBytes()); // StringLength());
	char* mem = NULL;
	char** mem_ref = NULL;
	size_t* mem_len = NULL;
	size_t** mem_len_ref = NULL;
	if (!pop_va_list_mem(ap, mem, mem_ref, allow_realloc))
	  return 0;
	if ((has_shape || table_nelements) && !ap.for_fortran) {
	  if (table_nelements)
	    len = table_nelements;
	  // len = 0;
	  mem_len = &len;
	  mem_len_ref = &mem_len;
	} else {
	  if (!pop_va_list_mem(ap, mem_len, mem_len_ref))
	    return 0;
	  if (!document.Is1DArray()) {
	    size_t* mem_ndim = mem_len;
	    mem_len = &len;
	    size_t* mem_shape = NULL;
	    size_t** mem_shape_ref = NULL;
	    if (!pop_va_list_mem(ap, mem_shape, mem_shape_ref, allow_realloc))
	      return 0;
	    if (ap.for_fortran && mem_shape == nullptr) {
	      len = 0;
	    } else {
	      len = 1;
	      for (size_t i = 0; i < mem_ndim[0]; i++) {
		len *= mem_shape[i];
	      }
	    }
	    size_t i = 0;
	    size_t src_shape_len = (size_t)(document.GetShape().Size());
	    size_t* src_shape = (size_t*)malloc(src_shape_len * sizeof(size_t));
	    for (rapidjson::Value::ConstValueIterator it = document.GetShape().Begin();
		 it != document.GetShape().End(); it++, i++) {
	      src_shape[i] = (size_t)(it->GetUint());
	    }
	    if (!set_va_list_mem(ap, mem_shape, mem_shape_ref, mem_ndim[0],
				 src_shape, src_shape_len, allow_realloc))
	      return 0;
	    free(src_shape);
	  }
	}
	enum rapidjson::YggSubType subtype = document.GetSubTypeCode();
	int precision = (int)(document.GetPrecision());
	size_t* mem_len_alt = mem_len;
	CASE_NDARRAY_(kYggIntSubType, 1, int8_t)
	else CASE_NDARRAY_(kYggIntSubType, 2, int16_t)
	else CASE_NDARRAY_(kYggIntSubType, 4, int32_t)
	else CASE_NDARRAY_(kYggIntSubType, 8, int64_t)
	else CASE_NDARRAY_(kYggUintSubType, 1, uint8_t)
	else CASE_NDARRAY_(kYggUintSubType, 2, uint16_t)
	else CASE_NDARRAY_(kYggUintSubType, 4, uint32_t)
	else CASE_NDARRAY_(kYggUintSubType, 8, uint64_t)
	else CASE_NDARRAY_(kYggFloatSubType, 4, float)
	else CASE_NDARRAY_(kYggFloatSubType, 8, double)
	else CASE_NDARRAY_(kYggComplexSubType, 8, std::complex<float>)
	else CASE_NDARRAY_(kYggComplexSubType, 16, std::complex<double>)
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
	else CASE_NDARRAY_(kYggFloatSubType, 16, long double)
	else CASE_NDARRAY_(kYggComplexSubType, 32, std::complex<long double>)
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
	else if (subtype == rapidjson::kYggStringSubType) {
	  // TODO: Encoding?
	  len = 0; // mem_len[0] * precision;
	  if (ap.for_fortran || !table_nelements) {
	    // Always assume that precision is in C list when called from
	    //   fortran API to ensure that elements in the array of strings
	    //   have a length
	    size_t* mem_prec = NULL;
	    size_t** mem_prec_ref = NULL;
	    if (!pop_va_list_mem(ap, mem_prec, mem_prec_ref))
	      return 0;
	    len = mem_len[0] * mem_prec[0];
	    mem_prec[0] = precision;
	  }
	  mem_len = &len;
	  if (!set_va_list_mem(ap, mem, mem_ref, len, tmp, tmp_len, allow_realloc))
	    return 0;
	  mem_len_alt[0] = len / precision;
	} else {
	  ygglog_throw_error("document_set_vargs: Unsupported array subtype %s", document.GetSubType().GetString());
	}
      }
      else CASE_PYTHON_(PythonClass)
      else CASE_PYTHON_(PythonFunction)
      else CASE_GEOMETRY_(obj, ObjWavefront)
      else CASE_GEOMETRY_(ply, Ply)
      else {
	ygglog_throw_error("document_set_vargs: Unsupported Yggdrasil type %s, stored as a string", type.GetString());
      }
    } else {
      CASE_STRING_;
    }
    break;
  }
  case (rapidjson::kObjectType): {
    if (document.IsYggdrasil()) {
      const rapidjson::Value& type = document.GetYggType();
      if (type == rapidjson::Document::GetSchemaString()) {
	rapidjson::Document* tmp_doc = new rapidjson::Document();
	tmp_doc->CopyFrom(document, tmp_doc->GetAllocator());
	generic_t tmp;
	tmp.obj = (void*)(tmp_doc);
	if (!set_va_list(ap, tmp)) {
	  return 0;
	}
      }
      else CASE_PYTHON_(PythonInstance)
      else {
	ygglog_throw_error("document_set_vargs: Unsupport Yggdrasil type %s, stored as an object", type.GetString());
      }
    } else {
      if (!(schema.HasMember("properties") && schema["properties"].IsObject()))
	ygglog_throw_error("document_set_vargs: schema for object must contain a properties member");
      for (typename rapidjson::Value::MemberIterator it = document.MemberBegin();
	   it != document.MemberEnd(); it++) {
	if (!document_set_vargs(it->value, schema["properties"][it->name],
				ap, allow_realloc))
	  return 0;
      }
    }
    break;
  }
  case (rapidjson::kArrayType): {
    if (!(schema.HasMember("items") && (schema["items"].IsArray() ||
					schema["items"].IsObject())))
      ygglog_throw_error("document_set_vargs: schema for array must contain an items member");
    size_t nelements = is_document_format_array(&document, true);
    if (nelements) {
      if (!set_va_list(ap, nelements))
	return 0;
    }
    size_t i = 0;
    for (typename rapidjson::Value::ValueIterator it = document.Begin();
	 it != document.End(); it++, i++) {
      if (schema["items"].IsArray()) {
	if (!document_set_vargs(*it, schema["items"][i],
				ap, allow_realloc, nelements))
	  return 0;
      } else {
	if (!document_set_vargs(*it, schema["items"],
				ap, allow_realloc, nelements))
	  return 0;
      }
    }
    break;
  }
  }
#undef CASE_STRING_
#undef CASE_NDARRAY_
#undef CASE_SCALAR_
#undef CASE_GEOMETRY_
#undef CASE_PYTHON_
#undef CASE_
#undef BASE_
  return 1;
}

int document_skip_vargs(rapidjson::Value& schema,
			va_list_t &ap, bool pointers,
			size_t table_nelements = 0) {
  if (!(schema.IsObject() && schema.HasMember("type") && schema["type"].IsString())) {
    ygglog_throw_error("document_skip_vargs: Schema must be an object containing a 'type' string property.");
  }
  std::string schema_type(schema["type"].GetString());
#define CASE_STD_(name, type)					\
  if (schema_type == std::string(#name)) {			\
    if (!skip_va_list<type>(ap, pointers)) {			\
      return 0;							\
    }								\
  }
  bool use_generic = false;
  if (schema.HasMember("use_generic") &&
      schema["use_generic"].IsBool() &&
      schema["use_generic"].GetBool()) {
    use_generic = true;
  }
  if (use_generic || schema_type == std::string("any") || schema_type == std::string("schema")) {
    if (!skip_va_list<generic_t>(ap, pointers))
      return 0;
  }
  else CASE_STD_(null, void*)
  else CASE_STD_(boolean, bool)
  else CASE_STD_(integer, int)
  else CASE_STD_(number, double)
  else if (schema_type == std::string("string")) {
    if (pointers) {
      if (!skip_va_list<char>(ap, pointers))
	return 0;
    } else {
      if (!skip_va_list<char*>(ap, pointers))
	return 0;
    }
    if (!skip_va_list<size_t>(ap, pointers))
      return 0;
  }
  else if (schema_type == std::string("array")) {
    if (!(schema.HasMember("items") && schema["items"].IsArray()))
      ygglog_throw_error("document_skip_vargs: Schema must have an array as its items member.");
    size_t nelements = 0;
    if (is_schema_format_array(&schema)) {
      if (!skip_va_list<size_t>(ap, pointers))
	return 0;
      nelements = 1;
    }
    for (typename rapidjson::Value::ValueIterator it = schema["items"].Begin();
	 it != schema["items"].End(); it++) {
      if (!document_skip_vargs(*it, ap, pointers, nelements))
	return 0;
    }
  }
  else if (schema_type == std::string("object")) {
    if (!(schema.HasMember("properties") && schema["properties"].IsObject()))
      ygglog_throw_error("document_skip_vargs: Schema must have an object as its properties member");
    for (typename rapidjson::Value::MemberIterator it = schema["properties"].MemberBegin();
	 it != schema["properties"].MemberEnd(); it++) {
      if (!document_skip_vargs(it->value, ap, pointers))
	return 0;
    }
  }
  else if (schema_type == std::string("scalar")) {
    if (!(schema.HasMember("subtype") && schema["subtype"].IsString()))
      ygglog_throw_error("document_skip_vargs: Scalar schema must contain a string subtype member");
    std::string schema_subtype(schema["subtype"].GetString());
    bool is_string = (schema_subtype == std::string("string") ||
		      schema_subtype == std::string("bytes") ||
		      schema_subtype == std::string("unicode"));
    int schema_precision = 0;
    if (schema.HasMember("precision") && schema["precision"].IsInt()) {
      if (!is_string)
	schema_precision = schema["precision"].GetInt();
    } else {
      if (!is_string)
	ygglog_throw_error("document_skip_vargs: Scalar schema must contain an integer precision member");
    }
#define CASE_SCALAR_(subtype, precision, type)				\
    if (schema_subtype == std::string(#subtype) && schema_precision == precision) { \
      if (!skip_va_list<type>(ap, pointers)) {				\
	return 0;							\
      }									\
    }
    CASE_SCALAR_(int, 1, int8_t)
    else CASE_SCALAR_(int, 2, int16_t)
    else CASE_SCALAR_(int, 4, int32_t)
    else CASE_SCALAR_(int, 8, int64_t)
    else CASE_SCALAR_(uint, 1, uint8_t)
    else CASE_SCALAR_(uint, 2, uint16_t)
    else CASE_SCALAR_(uint, 4, uint32_t)
    else CASE_SCALAR_(uint, 8, uint64_t)
    else CASE_SCALAR_(float, 4, float)
    else CASE_SCALAR_(float, 8, double)
    else CASE_SCALAR_(complex, 8, complex_float_t)
    else CASE_SCALAR_(complex, 16, complex_double_t)
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else CASE_SCALAR_(float, 16, long double)
    else CASE_SCALAR_(complex, 32, complex_long_double_t)
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else if (is_string) {
      if (pointers) {
	if (!skip_va_list<char>(ap, pointers))
	  return 0;
      } else {
	if (!skip_va_list<char*>(ap, pointers))
	  return 0;
      }
      if (!skip_va_list<size_t>(ap, pointers))
	return 0;
    }
    else {
      ygglog_throw_error("document_skip_vargs: Unsupported subtype and precision combination: subtype = %s, precision = %d", schema_subtype.c_str(), schema_precision);
    }
#undef CASE_SCALAR_    
  }
  else if (schema_type == std::string("ndarray") ||
	   schema_type == std::string("1darray")) {
    if (!(schema.HasMember("subtype") && schema["subtype"].IsString()))
      ygglog_throw_error("document_skip_vargs: ndarray schema must contain a string subtype member");
    int schema_ndim = 0;
    bool has_shape = false;
    std::string schema_subtype(schema["subtype"].GetString());
    int schema_precision = 0;
    bool is_string = (schema_subtype == std::string("string") ||
		      schema_subtype == std::string("bytes") ||
		      schema_subtype == std::string("unicode"));
    if (schema.HasMember("precision") && schema["precision"].IsInt()) {
      schema_precision = schema["precision"].GetInt();
    } else {
      if ((!is_string) || (is_string && !table_nelements))
	ygglog_throw_error("document_skip_vargs: ndarray schema must contain an integer precision member");
    }
    if (schema_type == std::string("1darray")) {
      schema_ndim = 1;
    }
    if (schema.HasMember("length") && schema["length"].IsInt()) {
      schema_ndim = 1;
      has_shape = true;
    } else if (schema.HasMember("shape") && schema["shape"].IsArray()) {
      schema_ndim = (int)(schema["shape"].Size());
      has_shape = true;
    }
    if (pointers && ap.for_fortran) {
      has_shape = false;
    }
    if (schema_ndim == 0 && schema.HasMember("ndim") && schema["ndim"].IsInt())
      schema_ndim = schema["ndim"].GetInt();
#define CASE_NDARRAY_(subtype, precision, type)				\
    if (schema_subtype == std::string(#subtype) && schema_precision == precision) { \
      if (!skip_va_list<type*>(ap, pointers)) {				\
	return 0;							\
      }									\
    }
    CASE_NDARRAY_(int, 1, int8_t)
    else CASE_NDARRAY_(int, 2, int16_t)
    else CASE_NDARRAY_(int, 4, int32_t)
    else CASE_NDARRAY_(int, 8, int64_t)
    else CASE_NDARRAY_(uint, 1, uint8_t)
    else CASE_NDARRAY_(uint, 2, uint16_t)
    else CASE_NDARRAY_(uint, 4, uint32_t)
    else CASE_NDARRAY_(uint, 8, uint64_t)
    else CASE_NDARRAY_(float, 4, float)
    else CASE_NDARRAY_(float, 8, double)
    else CASE_NDARRAY_(complex, 8, complex_float_t)
    else CASE_NDARRAY_(complex, 16, complex_double_t)
    else CASE_NDARRAY_(string, schema_precision, char)
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else CASE_NDARRAY_(float, 16, long double)
    else CASE_NDARRAY_(complex, 32, complex_long_double_t)
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
    else {
      ygglog_throw_error("document_skip_vargs: Unsupported subtype and precision combination: subtype = %s, precision = %d", schema_subtype.c_str(), schema_precision);
    }
    if (!(has_shape || table_nelements)) {
      if (schema_ndim == 1) {
	if (!skip_va_list<size_t>(ap, pointers)) {
	  return 0;
	}
      } else {
	if (!skip_va_list<size_t>(ap, pointers)) {
	  return 0;
	}
	if (!skip_va_list<size_t*>(ap, pointers)) {
	  return 0;
	}
      }
    }
    if (((pointers && ap.for_fortran) || !table_nelements) && is_string) {
      if (!skip_va_list<size_t>(ap, pointers)) {
	return 0;
      }
    }
#undef CASE_NDARRAY_    
  }
#define CASE_GEOMETRY_(name)			\
  CASE_STD_(name, name ## _t)
  else CASE_GEOMETRY_(obj)
  else CASE_GEOMETRY_(ply)
#undef CASE_GEOMETRY_
#define CASE_PYTHON_(name)			\
  CASE_STD_(name, python_t)
  else CASE_PYTHON_(class)
  else CASE_PYTHON_(function)
  else CASE_PYTHON_(instance)
#undef CASE_PYTHON_
  else {
    ygglog_throw_error("document_skip_vargs: Unsupported type %s", schema_type.c_str());
  }
#undef CASE_STD_
  return 1;
};

int args2document(rapidjson::Document* document, rapidjson::Value* schema,
		  va_list_t& ap) {
  if (schema == NULL)
    ygglog_throw_error("args2document: schema is NULL");
  if (document == NULL)
    ygglog_throw_error("args2document: document is NULL");
  if (!document_get_vargs(*((rapidjson::Value*)document),
			  *schema, ap, *document))
    return 0;
  return 1;
};

int document2args(rapidjson::Document* document, rapidjson::Document* schema,
		  va_list_t& ap, int allow_realloc) {
  if (document == NULL)
    ygglog_throw_error("document2args: document is NULL");
  bool cleanup_s = false;
  if (schema == NULL) {
    schema = encode_schema((rapidjson::Value*)document);
    cleanup_s = true;
  }
  if (schema == NULL)
    ygglog_throw_error("document2args: encoded schema is NULL");
  if (!document_set_vargs(*((rapidjson::Value*)document),
			  *((rapidjson::Value*)schema),
			  ap, allow_realloc))
    return 0;
  if (cleanup_s)
    delete schema;
  return 1;
};

const char* schema2name(rapidjson::Document* schema) {
  if (schema == NULL || !schema->IsObject() || !schema->HasMember("type"))
    return "";
  return (*schema)["type"].GetString();
};

ply_t Ply2ply(rapidjson::Ply& x) {
  ply_t out = init_ply();
  set_ply(&out, (void*)(&x), 1);
  return out;
};

rapidjson::Ply ply2Ply(ply_t x) {
  if (x.obj == NULL) {
    return rapidjson::Ply();
  } else {
    rapidjson::Ply* obj = (rapidjson::Ply*)(x.obj);
    return rapidjson::Ply(*obj);
  }
};

obj_t ObjWavefront2obj(rapidjson::ObjWavefront& x) {
  obj_t out = init_obj();
  set_obj(&out, (void*)(&x), 1);
  return out;
};
  
rapidjson::ObjWavefront obj2ObjWavefront(obj_t x) {
  if (x.obj == NULL) {
    return rapidjson::ObjWavefront();
  } else {
    rapidjson::ObjWavefront* obj = (rapidjson::ObjWavefront*)(x.obj);
    return rapidjson::ObjWavefront(*obj);
  }
}

void document_check_type(rapidjson::Value* d, std::string& type) {
  if (d == NULL) {
    ygglog_throw_error("document_check_type: Document is NULL");
  }
#define CASE_ERROR_(name)						\
  ygglog_throw_error("document_check_type: Document type is '%s', not '%s'", name, type.c_str())
#define CASE_(method, name)						\
  if (d->Is ## method()) {						\
    if (type != std::string(#name)) {					\
      CASE_ERROR_(#name);						\
    }									\
  }
#define CASE_SCALAR_(method, name)					\
  if (d->Is ## method()) {						\
    if (type != std::string(#name) && type != "scalar") {		\
      CASE_ERROR_(#name);						\
    }									\
  }
  if (d->IsYggdrasil()) {
    if (type != std::string(d->GetYggType().GetString()) &&
	!((type == "number" && d->IsScalar("double")) ||
	  (type == "integer" && d->IsScalar("int")) ||
	  (type == "1darray" && d->Is1DArray()))) {
      CASE_ERROR_(d->GetYggType().GetString());
    }
  }
  else CASE_(Null, null)
  else CASE_(Bool, boolean)
  else CASE_SCALAR_(String, string)
  else CASE_(Array, array)
  else CASE_(Object, object)
  else CASE_SCALAR_(Double, number)
  else CASE_SCALAR_(Int, integer)
  else {
    CASE_ERROR_("unknown");
  }
#undef CASE_ERROR_
#undef CASE_
}

void document_check_yggtype(rapidjson::Value* d, std::string& type,
			    std::string& subtype, size_t precision) {
  document_check_type(d, type);
  if (d->IsYggdrasil()) {
    if (subtype != std::string(d->GetSubType().GetString())) {
      ygglog_throw_error("document_check_yggtype: Document subtype is '%s', not '%s'", d->GetSubType().GetString(), subtype.c_str());
    }
    if (precision != (size_t)(d->GetPrecision())) {
      ygglog_throw_error("document_check_yggtype: Document precision is %d, not %d", (int)(d->GetPrecision()), (int)precision);
    }
  } else if (!((d->IsDouble() && subtype == "float" && precision == 8) ||
	       (d->IsInt() && subtype == "int" && precision == 4) ||
	       (d->IsInt64() && subtype == "int" && precision == 8) ||
	       (d->IsUint() && subtype == "uint" && precision == 4) ||
	       (d->IsUint64() && subtype == "uint" && precision == 8))) {
    ygglog_throw_error("document_check_yggtype: Document is type %d, not scalar '%s' with precision %d", d->GetType(), subtype.c_str(), precision);
  }
}

// C exposed functions
extern "C" {

  void* type_from_doc_c(const void* type_doc) {
    rapidjson::Document* out = NULL;
    try {
      const rapidjson::Value* type_doc_cpp = (const rapidjson::Value*)type_doc;
      out = type_from_doc(*type_doc_cpp);
    } catch(...) {
      ygglog_error("type_from_doc_c: C++ exception thrown.");
      if (out != NULL) {
	delete out;
	out = NULL;
      }
    }
    return (void*)out;
  }

  void* type_from_pyobj_c(PyObject* pyobj) {
    rapidjson::Document* out = NULL;
    try {
      out = type_from_pyobj(pyobj);
    } catch(...) {
      ygglog_error("type_from_pyobj_c: C++ exception thrown.");
      if (out != NULL) {
	delete out;
	out = NULL;
      }
    }
    return (void*)out;
  }

  int is_dtype_format_array(dtype_t* type_struct) {
    try {
      if (type_struct->schema == NULL) {
	return -1;
      }
      if (!is_schema_format_array((rapidjson::Value*)(type_struct->schema)))
	return 0;
      // TODO: Check for format string
    } catch(...) {
      ygglog_error("is_dtype_format_array: C++ exception thrown.");
      return -1;
    }
    return 1;
  }

  const char* schema2name_c(void* schema) {
    return schema2name((rapidjson::Document*)schema);
  }

  const char* dtype2name(dtype_t* type_struct) {
    if (type_struct == NULL || type_struct->schema == NULL)
      return "";
    return schema2name((rapidjson::Document*)(type_struct->schema));
  }
  
  generic_t init_generic() {
    generic_t out;
    out.prefix = prefix_char;
    out.obj = NULL;
    out.allocator = NULL;
    return out;
  }

  generic_t init_generic_null() {
    generic_t out = init_generic();
    rapidjson::Document* x = new rapidjson::Document(rapidjson::kNullType);
    out.obj = (void*)x;
    return out;
  }

  generic_t init_generic_array() {
    generic_t out = init_generic();
    rapidjson::Document* x = new rapidjson::Document(rapidjson::kArrayType);
    out.obj = (void*)x;
    return out;
  }

  generic_t init_generic_map() {
    generic_t out = init_generic();
    rapidjson::Document* x = new rapidjson::Document(rapidjson::kObjectType);
    out.obj = (void*)x;
    return out;
  }

  int is_generic_flag(char x) {
    if (x == prefix_char)
      return 1;
    else
      return 0;
  }

  int is_generic_init(generic_t x) {
    return is_generic_flag(x.prefix);
  }
  
  // generic_t create_generic(dtype_t* type_struct, void* data, size_t nbytes) {
  //   generic_t out = init_generic();
  //   try {
  //     MetaschemaType* type = dtype2class(type_struct);
  //     YggGeneric* obj = new YggGeneric(type, data, nbytes);
  //     out.obj = (void*)obj;
  //   } catch(...) {
  //     ygglog_error("create_generic: C++ exception thrown.");
  //     destroy_generic(&out);
  //   }
  //   return out;
  // }

  int destroy_generic(generic_t* x) {
    int ret = 0;
    if (x != NULL) {
      if (is_generic_init(*x)) {
	x->prefix = ' ';
	if (x->obj != NULL) {
	  if (x->allocator != NULL) {
	    x->obj = NULL;
	  } else {
	    try {
	      rapidjson::Document* obj = (rapidjson::Document*)(x->obj);
	      delete obj;
	      x->obj = NULL;
	    } catch (...) {
	      ygglog_error("destroy_generic: C++ exception thrown in destructor for rapidjson::Document.");
	      ret = -1;
	    }
	  }
	  x->allocator = NULL;
	}
      }
    }
    return ret;
  }

  int copy_generic_into(generic_t* dst, generic_t src) {
    try {
      if (!dst) {
	ygglog_throw_error("copy_generic_into: Destination is empty.");
      }
      if (is_generic_init(*dst))
	destroy_generic(dst);
      dst[0] = init_generic();
      if (!(is_generic_init(src))) {
	ygglog_throw_error("copy_generic_into: Source object not initialized.");
      }
      if (src.obj == NULL) {
	ygglog_throw_error("copy_generic: Generic object class is NULL.");
      }
      dst->obj = (void*)copy_document((rapidjson::Value*)(src.obj));
    } catch(...) {
      ygglog_error("copy_generic_into: C++ exception thrown.");
      destroy_generic(dst);
      return -1;
    }
    return 0;
  }

  generic_t copy_generic(generic_t src) {
    generic_t out = init_generic();
    copy_generic_into(&out, src);
    return out;
  }

  void display_generic(generic_t x) {
    try {
      if (is_generic_init(x)) {
	display_document((rapidjson::Value*)(x.obj));
      }
    } catch (...) {
      ygglog_error("display_generic: C++ exception thrown.");
    }
  }

#define GENERIC_SUCCESS_ 0
#define GENERIC_ERROR_ -1

  void* generic_get_item(generic_t x, const char *type) {
    void* out = NULL;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_get_item: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_get_item: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      std::string typeS(type);
      document_check_type(x_obj, typeS);
      bool requires_freeing = false;
      out = x_obj->GetDataPtr(requires_freeing);
    } catch (...) {
      ygglog_error("generic_get_item: C++ exception thrown.");
      out = NULL;
    }
    return out;
  }
  int generic_get_item_nbytes(generic_t x, const char *type) {
    int out = -1;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_get_item_nbytes: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_get_item_nbytes: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      std::string typeS(type);
      document_check_type(x_obj, typeS);
      out = x_obj->GetNBytes();
    } catch (...) {
      ygglog_error("generic_get_item_nbytes: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_set_item(generic_t x, const char *type, void* value) {
    int out = GENERIC_ERROR_;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_set_item: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_set_item: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      std::string typeS(type);
#define CASE_(name, method)			\
      if (typeS == std::string(#name)) {	\
	x_obj->method;				\
      }
#define GEOMETRY_(name, rjtype)					\
      if (typeS == std::string(#name)) {			\
	rapidjson::rjtype* tmp = (rapidjson::rjtype*)value;	\
	x_obj->Set ## rjtype(*tmp);				\
      }
      CASE_(null, SetNull())
      else CASE_(boolean, SetBool(((bool*)value)[0]))
      else CASE_(number, SetDouble(((double*)value)[0]))
      else CASE_(integer, SetInt(((int*)value)[0]))
      else CASE_(string, SetString(((char*)value), strlen((char*)value),
				   generic_allocator(x))) // Shouuld this be cast to char**?
      else if (typeS == std::string("any") ||
	       typeS == std::string("instance") ||
	       typeS == std::string("schema") ||
	       typeS == std::string("array") ||
	       typeS == std::string("object")) {
	generic_t tmp = init_generic();
	tmp.obj = copy_document((rapidjson::Value*)value);
      }
      else if (typeS == std::string("class") ||
	       typeS == std::string("function")) {
	python_t tmp = init_python();
	tmp.obj = (PyObject*)value;
	if (generic_set_python_class(x, tmp) != GENERIC_SUCCESS_)
	  return GENERIC_ERROR_;
      }
      else GEOMETRY_(obj, ObjWavefront)
      else GEOMETRY_(ply, Ply)
      else {
	ygglog_throw_error("generic_set_item: Unsupported type '%s'", type);
      }
#undef CASE_
#undef GEOMETRY_
    } catch(...) {
      ygglog_error("generic_set_item: C++ exception thrown");
      return GENERIC_ERROR_;
    }
    return out;
  }
  void* generic_get_scalar(generic_t x, const char *subtype, const size_t precision) {
    try {
      std::string typeS("scalar");
      std::string subtypeS(subtype);
      document_check_yggtype((rapidjson::Value*)(x.obj), typeS, subtypeS, precision);
    } catch(...) {
      ygglog_error("generic_get_scalar: C++ exception thrown");
      return NULL;
    }
    return generic_get_item(x, "scalar");
  }
  size_t generic_get_1darray(generic_t x, const char *subtype, const size_t precision, void** data) {
    size_t new_length = 0;
    try {
      std::string typeS("1darray");
      std::string subtypeS(subtype);
      document_check_yggtype((rapidjson::Value*)(x.obj), typeS, subtypeS, precision);
      void* new_data = generic_get_item(x, "1darray");
      if (new_data == NULL)
	return 0;
      size_t nbytes = generic_get_item_nbytes(x, "1darray");
      if (nbytes == 0)
	return 0;
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      new_length = (size_t)(x_obj->GetNElements());
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_get_1darray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
    } catch (...) {
      ygglog_error("generic_get_1darra: C++ exception thrown");
      return 0;
    }
    return new_length;
  }
  size_t generic_get_ndarray(generic_t x, const char *subtype, const size_t precision, void** data, size_t** shape) {
    size_t new_ndim = 0;
    try {
      std::string typeS("ndarray");
      std::string subtypeS(subtype);
      document_check_yggtype((rapidjson::Value*)(x.obj), typeS, subtypeS, precision);
      void* new_data = generic_get_item(x, "ndarray");
      if (new_data == NULL)
	return 0;
      size_t nbytes = generic_get_item_nbytes(x, "ndarray");
      if (nbytes == 0)
	return 0;
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_get_ndarray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
      const rapidjson::Value& rjshape = x_obj->GetShape();
      new_ndim = (size_t)(rjshape.Size());
      size_t i = 0;
      shape[0] = (size_t*)realloc(shape[0], new_ndim);
      if (shape[0] == NULL) {
	ygglog_throw_error("generic_get_ndarray: Failed to reallocate shape.");
      }
      for (rapidjson::Value::ConstValueIterator it = rjshape.Begin();
	   it != rjshape.End(); it++, i++) {
	shape[0][i] = (size_t)(it->GetInt());
      }
    } catch (...) {
      ygglog_error("generic_get_ndarray: C++ exception thrown");
      return 0;
    }
    return new_ndim;
  }
  int generic_set_scalar(generic_t x, void* value, const char *subtype,
			 const size_t precision, const char *units) {
    int out = GENERIC_ERROR_;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_set_scalar: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_set_scalar: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      rapidjson::Document schema(rapidjson::kObjectType);
      schema.AddMember(rapidjson::Document::GetTypeString(),
		       rapidjson::Value("scalar", 6,
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetSubTypeString(),
		       rapidjson::Value(subtype, strlen(subtype),
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetPrecisionString(),
		       rapidjson::Value((unsigned)precision).Move(),
		       schema.GetAllocator());
      if (units && strlen(units) > 0) {
	schema.AddMember(rapidjson::Document::GetUnitsString(),
			 rapidjson::Value(units, strlen(units),
					  schema.GetAllocator()).Move(),
			 schema.GetAllocator());
      }
      x_obj->SetYggdrasilString((char*)value, precision,
				generic_allocator(x),
				schema);
      out = GENERIC_SUCCESS_;
    } catch(...) {
      ygglog_error("generic_set_scalar: C++ exception thrown");
      return GENERIC_ERROR_;
    }
    return out;
  }
  int generic_set_1darray(generic_t x, void* value, const char *subtype,
			  const size_t precision, const size_t length,
			  const char* units) {
    int out = GENERIC_ERROR_;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_set_1darray: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_set_1darray: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      rapidjson::Document schema(rapidjson::kObjectType);
      schema.AddMember(rapidjson::Document::GetTypeString(),
		       rapidjson::Value("1darray", 7,
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetSubTypeString(),
		       rapidjson::Value(subtype, strlen(subtype),
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetPrecisionString(),
		       rapidjson::Value((unsigned)precision).Move(),
		       schema.GetAllocator());
      if (units && strlen(units) > 0) {
	schema.AddMember(rapidjson::Document::GetUnitsString(),
			 rapidjson::Value(units, strlen(units),
					  schema.GetAllocator()).Move(),
			 schema.GetAllocator());
      }
      rapidjson::Value rjshape(rapidjson::kArrayType);
      rjshape.PushBack(rapidjson::Value((unsigned)length).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetShapeString(), rjshape,
		       schema.GetAllocator());
      x_obj->SetYggdrasilString((char*)value, precision,
				generic_allocator(x),
				schema);
      out = GENERIC_SUCCESS_;
    } catch(...) {
      ygglog_error("generic_set_1darray: C++ exception thrown");
      return GENERIC_ERROR_;
    }
    return out;
  }
  int generic_set_ndarray(generic_t x, void* data, const char *subtype,
			  const size_t precision, const size_t ndim, const size_t* shape,
			  const char* units) {
    int out = GENERIC_ERROR_;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_set_ndarray: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_set_ndarray: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      rapidjson::Document schema(rapidjson::kObjectType);
      schema.AddMember(rapidjson::Document::GetTypeString(),
		       rapidjson::Value("ndarray", 7,
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetSubTypeString(),
		       rapidjson::Value(subtype, strlen(subtype),
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetPrecisionString(),
		       rapidjson::Value((unsigned)precision).Move(),
		       schema.GetAllocator());
      if (units && strlen(units) > 0) {
	schema.AddMember(rapidjson::Document::GetUnitsString(),
			 rapidjson::Value(units, strlen(units),
					  schema.GetAllocator()).Move(),
			 schema.GetAllocator());
      }
      rapidjson::Value rjshape(rapidjson::kArrayType);
      for (size_t i = 0; i < ndim; i++) {
	rjshape.PushBack(rapidjson::Value((unsigned)(shape[i])).Move(),
			 schema.GetAllocator());
      }
      schema.AddMember(rapidjson::Document::GetShapeString(), rjshape,
		       schema.GetAllocator());
      x_obj->SetYggdrasilString((char*)data, precision,
				generic_allocator(x),
				schema);
      out = GENERIC_SUCCESS_;
    } catch(...) {
      ygglog_error("generic_set_ndarray: C++ exception thrown");
      return GENERIC_ERROR_;
    }
    return out;
  }
  // TODO: Cleanup temporary item created during setting
#define NESTED_BASICS_(base, idx, idxType)					\
  void* generic_ ## base ## _get_item(generic_t x, idxType idx, const char *type) { \
    try {								\
      generic_t tmp;							\
      if (get_generic_ ## base(x, idx, &tmp, false) != GENERIC_SUCCESS_) { \
	return NULL;							\
      }									\
      return generic_get_item(tmp, type);				\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get: C++ exception thrown");	\
      return NULL;							\
    }									\
  }									\
  int generic_ ## base ## _get_item_nbytes(generic_t x, idxType idx, const char *type) { \
    try {								\
      generic_t tmp;							\
      if (get_generic_ ## base(x, idx, &tmp, false) != GENERIC_SUCCESS_) { \
	return 0;							\
      }									\
      return generic_get_item_nbytes(tmp, type);			\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_nbytes: C++ exception thrown"); \
      return 0;								\
    }									\
  }									\
  void* generic_ ## base ## _get_scalar(generic_t x, idxType idx, const char *subtype, const size_t precision) { \
    try {								\
      generic_t tmp;							\
      if (get_generic_ ## base(x, idx, &tmp, false) != GENERIC_SUCCESS_) { \
	return NULL;							\
      }									\
      return generic_get_scalar(tmp, subtype, precision);		\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_scalar: C++ exception thrown"); \
      return NULL;							\
    }									\
  }									\
  size_t generic_ ## base ## _get_1darray(generic_t x, idxType idx, const char *subtype, const size_t precision, void** data) { \
    try {								\
      generic_t tmp;							\
      if (get_generic_ ## base(x, idx, &tmp, false) != GENERIC_SUCCESS_) { \
	return 0;							\
      }									\
      return generic_get_1darray(tmp, subtype, precision, data);	\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_1darray: C++ exception thrown"); \
      return 0;								\
    }									\
  }									\
  size_t generic_ ## base ## _get_ndarray(generic_t x, idxType idx, const char *subtype, const size_t precision, void** data, size_t** shape) { \
    try {								\
      generic_t tmp;							\
      if (get_generic_ ## base(x, idx, &tmp, false) != GENERIC_SUCCESS_) { \
	return 0;							\
      }									\
      return generic_get_ndarray(tmp, subtype, precision, data, shape);	\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_ndarary: C++ exception thrown"); \
      return 0;								\
    }									\
  }									\
  int generic_ ## base ## _set_item(generic_t x, idxType idx, const char *type, void* value) { \
    try {								\
      generic_t tmp;							\
      if (generic_set_item(tmp, type, value) != GENERIC_SUCCESS_) {	\
        return GENERIC_ERROR_;						\
      }									\
      if (set_generic_ ## base(x, idx, tmp) != GENERIC_SUCCESS_) {	\
	return GENERIC_ERROR_;						\
      }									\
      destroy_generic(&tmp);						\
    } catch(...) {							\
      ygglog_error("generic_" #base "_set_item: C++ exception thrown");	\
      return GENERIC_ERROR_;						\
    }									\
    return GENERIC_SUCCESS_;						\
  }									\
  int generic_ ## base ## _set_scalar(generic_t x, idxType idx,		\
				      void* value,			\
				      const char *subtype,		\
				      const size_t precision,		\
				      const char *units) {		\
    try {								\
      generic_t tmp = init_generic_null();				\
      if (generic_set_scalar(tmp, value, subtype, precision, units) != GENERIC_SUCCESS_) { \
        return GENERIC_ERROR_;						\
      }									\
      if (set_generic_ ## base(x, idx, tmp) != GENERIC_SUCCESS_) {	\
	return GENERIC_ERROR_;						\
      }									\
      destroy_generic(&tmp);						\
    } catch(...) {							\
      ygglog_error("generic_" #base "_set_scalar: C++ exception thrown"); \
      return GENERIC_ERROR_;						\
    }									\
    return GENERIC_SUCCESS_;						\
  }									\
  int generic_ ## base ## _set_1darray(generic_t x, idxType idx,	\
				       void* value,			\
				       const char *subtype,		\
				       const size_t precision,		\
				       const size_t length,		\
				       const char *units) {		\
    try {								\
      generic_t tmp = init_generic_null();				\
      if (generic_set_1darray(tmp, value, subtype, precision, length, units) != GENERIC_SUCCESS_) { \
        return GENERIC_ERROR_;						\
      }									\
      if (set_generic_ ## base(x, idx, tmp) != GENERIC_SUCCESS_) {	\
	return GENERIC_ERROR_;						\
      }									\
      destroy_generic(&tmp);						\
    } catch(...) {							\
      ygglog_error("generic_" #base "_set_1darray: C++ exception thrown"); \
      return GENERIC_ERROR_;						\
    }									\
    return GENERIC_SUCCESS_;						\
  }									\
  int generic_ ## base ## _set_ndarray(generic_t x, idxType idx,	\
				       void* value,			\
				       const char *subtype,		\
				       const size_t precision,		\
				       const size_t ndim,		\
				       const size_t* shape,		\
				       const char *units) {		\
    try {								\
      generic_t tmp = init_generic_null();				\
      if (generic_set_ndarray(tmp, value, subtype, precision, ndim, shape, units) != GENERIC_SUCCESS_) { \
        return GENERIC_ERROR_;						\
      }									\
      if (set_generic_ ## base(x, idx, tmp) != GENERIC_SUCCESS_) {	\
	return GENERIC_ERROR_;						\
      }									\
      destroy_generic(&tmp);						\
    } catch(...) {							\
      ygglog_error("generic_" #base "_set_ndarray: C++ exception thrown"); \
      return GENERIC_ERROR_;						\
    }									\
    return GENERIC_SUCCESS_;						\
  }

  NESTED_BASICS_(array, index, const size_t)
  NESTED_BASICS_(map, key, const char*)
  
#undef NESTED_BASICS_
  
  int add_generic_array(generic_t arr, generic_t x) {
    int out = GENERIC_SUCCESS_;
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("add_generic_array: Array is not a generic object.");
      }
      if (!(is_generic_init(x))) {
	ygglog_throw_error("add_generic_array: New element is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("add_generic_array: Array is NULL.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("add_generic_array: New element is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!arr_obj->IsArray()) {
	ygglog_throw_error("add_generic_array: Document is not an array.");
      }
      rapidjson::Value cpy(*x_obj, generic_allocator(arr), true);
      arr_obj->PushBack(cpy, generic_allocator(arr));
    } catch (...) {
      ygglog_error("add_generic_array: C++ exception thrown.");
      out = GENERIC_ERROR_;
    }
    return out;
  }

  int set_generic_array(generic_t arr, const size_t i, generic_t x) {
    int out = GENERIC_SUCCESS_;
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("set_generic_array: Array is not a generic object.");
      }
      if (!(is_generic_init(x))) {
	ygglog_throw_error("set_generic_array: New element is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("set_generic_array: Array is NULL.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("set_generic_array: New element is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!arr_obj->IsArray()) {
	ygglog_throw_error("set_generic_array: Document is not an array.");
      }
      if (arr_obj->Size() > i) {
	(*arr_obj)[i].CopyFrom(*((rapidjson::Value*)x_obj),
			       generic_allocator(arr), true);
      } else {
	rapidjson::Value cpy(*((rapidjson::Value*)x_obj),
			     generic_allocator(arr), true);
	arr_obj->PushBack(cpy, generic_allocator(arr));
      }
    } catch (...) {
      ygglog_error("set_generic_array: C++ exception thrown.");
      out = GENERIC_ERROR_;
    }
    return out;
  }

  int get_generic_array(generic_t arr, const size_t i, generic_t *x, int copy) {
    int out = GENERIC_SUCCESS_;
    x[0] = init_generic();
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("get_generic_array: Array is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("get_generic_array: Array is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      if (!arr_obj->IsArray()) {
	ygglog_throw_error("get_generic_array: Document is not an array.");
      }
      if (arr_obj->Size() <= i) {
	ygglog_throw_error("get_generic_array: Document only has %d elements", (int)(arr_obj->Size()));
      }
      if (copy) {
	rapidjson::Document* cpy = new rapidjson::Document();
	if (!(*arr_obj)[i].Accept(*cpy)) {
	  ygglog_throw_error("get_generic_array: Error in Accept");
	}
	cpy->FinalizeFromStack();
	x[0].obj = (void*)cpy;
      } else {
	x[0].obj = (void*)(&((*arr_obj)[i]));
	x[0].allocator = (void*)(&generic_allocator(arr));
      }
    } catch (...) {
      ygglog_error("get_generic_array: C++ exception thrown.");
      out = GENERIC_ERROR_;
    }
    return out;
  }

  int set_generic_object(generic_t arr, const char* k, generic_t x) {
    int out = GENERIC_SUCCESS_;
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("set_generic_object: Object is not a generic object.");
      }
      if (!(is_generic_init(x))) {
	ygglog_throw_error("set_generic_object: New element is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("set_generic_object: Object is NULL.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("set_generic_object: New element is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!arr_obj->IsObject()) {
	ygglog_throw_error("set_generic_object: Document is not an object.");
      }
      if (arr_obj->HasMember(k)) {
	(*arr_obj)[k].CopyFrom(*((rapidjson::Value*)x_obj),
			       generic_allocator(arr), true);
      } else {
	rapidjson::Value key(k, strlen(k), generic_allocator(arr));
	rapidjson::Value cpy(*((rapidjson::Value*)x_obj),
			     generic_allocator(arr), true);
	arr_obj->AddMember(key, cpy, generic_allocator(arr));
      }
    } catch (...) {
      ygglog_error("set_generic_object: C++ exception thrown.");
      out = GENERIC_ERROR_;
    }
    return out;
  }

  int get_generic_object(generic_t arr, const char* k, generic_t *x, int copy) {
    int out = 0;
    x[0] = init_generic();
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("get_generic_object: Object is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("get_generic_object: Object is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      if (!arr_obj->IsObject()) {
	ygglog_throw_error("get_generic_object: Document is not an object.");
      }
      if (!arr_obj->HasMember(k)) {
	ygglog_throw_error("get_generic_object: Document does not have the requested key.");
      }
      if (copy) {
	rapidjson::Document* cpy = new rapidjson::Document();
	if (!(*arr_obj)[k].Accept(*cpy)) {
	  ygglog_throw_error("get_generic_object: Error in Accept");
	}
	cpy->FinalizeFromStack();
	x[0].obj = (void*)cpy;
      } else {
	x[0].obj = (void*)(&((*arr_obj)[k]));
	x[0].allocator = (void*)(&generic_allocator(arr));
      }
    } catch (...) {
      ygglog_error("get_generic_object: C++ exception thrown.");
      out = 1;
    }
    return out;
  }

#define NESTED_BASE_SET_(base, idx, idxType, name, args, ...)	\
  int generic_ ## base ## _set_ ## name(generic_t x, idxType idx, __VA_ARGS__) { \
    generic_t item = init_generic_null();				\
    if (generic_set_ ## name (item, UNPACK_MACRO args) != GENERIC_SUCCESS_) { \
      return GENERIC_ERROR_;						\
    }									\
    int out = set_generic_ ## base(x, idx, item);			\
    destroy_generic(&item);						\
    return out;								\
  }
#define NESTED_BASE_GET_(base, idx, idxType, name, type, defV, args, ...) \
  type generic_ ## base ## _get_ ## name(generic_t x, idxType idx, __VA_ARGS__) { \
    generic_t item;							\
    type out = defV;							\
    if (get_generic_ ## base(x, (idxType)idx, &item, false) != GENERIC_SUCCESS_) { \
      return out;							\
    }									\
    out = generic_get_ ## name(item, UNPACK_MACRO args);		\
    return out;								\
  }
#define NESTED_BASE_GET_NOARGS_(base, idx, idxType, name, type, defV)	\
  type generic_ ## base ## _get_ ## name(generic_t x, idxType idx) {	\
    generic_t item;							\
    type out = defV;							\
    if (get_generic_ ## base(x, (idxType)idx, &item, false) != GENERIC_SUCCESS_) { \
      return out;							\
    }									\
    out = generic_get_ ## name(item);					\
    return out;								\
  }
#define NESTED_SET_(name, args, ...)					\
  NESTED_BASE_SET_(array, index, const size_t, name, args, __VA_ARGS__)	\
  NESTED_BASE_SET_(map, key, const char*, name, args, __VA_ARGS__)
#define NESTED_GET_(name, type, defV, args, ...)	\
  NESTED_BASE_GET_(array, index, const size_t, name, type, defV, args, __VA_ARGS__) \
  NESTED_BASE_GET_(map, key, const char*, name, type, defV, args, __VA_ARGS__)
#define NESTED_GET_NOARGS_(name, type, defV)	\
  NESTED_BASE_GET_NOARGS_(array, index, const size_t, name, type, defV)	\
  NESTED_BASE_GET_NOARGS_(map, key, const char*, name, type, defV)
  
#define STD_JSON_NESTED_(name)						\
  generic_t generic_array_get_ ## name(generic_t x, const size_t index) { \
    generic_t item;							\
    get_generic_array(x, index, &item, true);				\
    return item;							\
  }									\
  generic_t generic_map_get_ ## name(generic_t x, const char* key) {	\
    generic_t item;							\
    get_generic_object(x, key, &item, true);				\
    return item;							\
  }									\
  int generic_array_set_ ## name(generic_t x, const size_t index, generic_t item) { \
    return set_generic_array(x, index, item);				\
  }									\
  int generic_map_set_ ## name(generic_t x, const char* key, generic_t item) { \
    return set_generic_map(x, key, item);				\
  }

  
#define STD_JSON_BASE_(name, type, isMethod, outMethod, setMethod, defV) \
  type generic_get_ ## name(generic_t x) {				\
    type out = defV;							\
    if (x.obj == NULL) {						\
      ygglog_error("Generic object is NULL");				\
      return out;							\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    if (!isMethod) {							\
      display_document(d);						\
      ygglog_error("Generic object is not " #name);			\
      return out;							\
    }									\
    outMethod;								\
    return out;								\
  }									\
  int generic_set_ ## name(generic_t x, type value) {			\
    if (!is_generic_init(x)) {						\
      ygglog_error("Generic object is not initialized");		\
      return GENERIC_ERROR_;						\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    setMethod;								\
    return GENERIC_SUCCESS_;						\
  }									\
  NESTED_GET_NOARGS_(name, type, defV)					\
  NESTED_SET_(name, (value), type value)
#define STD_UNITS_BASE_(name, type, isMethod, outMethod, setMethod, defV) \
  type generic_get_ ## name(generic_t x) {				\
    type out = defV;							\
    if (x.obj == NULL) {						\
      ygglog_error("Generic object is NULL");				\
      return out;							\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    if (!isMethod) {							\
      ygglog_error("Generic object is not " #name);			\
      return out;							\
    }									\
    outMethod;								\
    return out;								\
  }									\
  int generic_set_ ## name(generic_t x, type value, const char* units) { \
    if (!is_generic_init(x)) {						\
      ygglog_error("Generic object is not initialized");		\
      return GENERIC_ERROR_;						\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    setMethod;								\
    return GENERIC_SUCCESS_;						\
  }									\
  NESTED_GET_NOARGS_(name, type, defV)					\
  NESTED_SET_(name, (value, units), type value, const char* units)
#define STD_JSON_(name, type, method, defV)				\
  STD_JSON_BASE_(name, type, d->Is ## method(), out = d->Get ## method(), d->Set ## method(value), defV)
#define STD_UNITS_(name, type, method, defV)				\
  STD_UNITS_BASE_(name, type, d->Is ## method(), out = d->Get ## method(), d->Set ## method(value), defV)
#define GEOMETRY_(name, rjtype)						\
  STD_JSON_BASE_(name, name ## _t, d->Is ## rjtype(), rapidjson::rjtype* tmp = new rapidjson::rjtype(); d->Get ## rjtype(*tmp); out = rjtype ## 2 ## name(*tmp); delete tmp, d->Set ## rjtype(name ## 2 ## rjtype(value)), init_ ## name())
#define ARRAY_(name, type, rjtype)					\
  size_t generic_get_1darray_ ## name(generic_t x, type** data) {	\
    if (x.obj == NULL || data == NULL) {				\
      ygglog_error("Generic object is NULL");				\
      return 0;								\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);			\
    if (!d->Is1DArray<rjtype>()) {					\
      ygglog_error("Generic object is not " #name);			\
      return 0;								\
    }									\
    rapidjson::SizeType nelements = 0;					\
    data[0] = (type*)(d->Get1DArray<rjtype>(nelements, generic_allocator(x))); \
    return (size_t)nelements;						\
  }									\
  size_t generic_get_ndarray_ ## name(generic_t x, type** data, size_t** shape) { \
    if (x.obj == NULL || data == NULL) {				\
      ygglog_error("Generic object is NULL");				\
      return 0;								\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    if (!d->IsNDArray<rjtype>()) {					\
      ygglog_error("Generic object is not " #name);			\
      return 0;								\
    }									\
    rapidjson::SizeType ndim = 0;					\
    rapidjson::SizeType* rjshape = NULL;				\
    data[0] = (type*)(d->GetNDArray<rjtype>(rjshape, ndim, generic_allocator(x))); \
    shape[0] = (size_t*)(generic_allocator(x).Malloc(ndim * sizeof(size_t))); \
    for (rapidjson::SizeType i = 0; i < ndim; i++) {			\
      (*shape)[i] = rjshape[i];						\
    }									\
    generic_allocator(x).Free(rjshape);					\
    return (size_t)ndim;						\
  }									\
  int generic_set_1darray_ ## name(generic_t x, type* value, const size_t length, const char* units) { \
    if (!is_generic_init(x)) {						\
      ygglog_error("Generic object is not initialized");		\
      return GENERIC_ERROR_;						\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    d->Set1DArray((rjtype*)value, (rapidjson::SizeType)length, units);	\
    return GENERIC_SUCCESS_;						\
  }									\
  int generic_set_ndarray_ ## name(generic_t x, type* value, const size_t ndim, const size_t* shape, const char* units) { \
    if (!is_generic_init(x)) {						\
      ygglog_error("Generic object is not initialized");		\
      return GENERIC_ERROR_;						\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    rapidjson::SizeType* rjshape = (rapidjson::SizeType*)(generic_allocator(x).Malloc(ndim * sizeof(rapidjson::SizeType))); \
    for (size_t i = 0; i < ndim; i++) {					\
      rjshape[i] = (rapidjson::SizeType)(shape[i]);			\
    }									\
    d->SetNDArray((rjtype*)value, rjshape, (rapidjson::SizeType)ndim, units); \
    generic_allocator(x).Free(rjshape);					\
    return GENERIC_SUCCESS_;						\
  }									\
  NESTED_GET_(1darray_ ## name, size_t, 0, (data), type** data)		\
  NESTED_GET_(ndarray_ ## name, size_t, 0, (data, shape), type** data, size_t** shape) \
  NESTED_SET_(1darray_ ## name, (value, length, units), type* value, const size_t length, const char* units) \
  NESTED_SET_(ndarray_ ## name, (data, ndim, shape, units), type* data, const size_t ndim, const size_t* shape, const char* units)
#define SCALAR_(name, type, defV)		\
  STD_UNITS_BASE_(name, type, d->IsScalar<type>(), out = (type)(d->GetScalar<type>()), d->SetScalar(value, units), defV) \
  ARRAY_(name, type, type)
#define COMPLEX_(name, type, subtype, defV)				\
  STD_UNITS_BASE_(name, type, d->IsScalar<std::complex<subtype>>(), std::complex<subtype> tmp = d->GetScalar<std::complex<subtype>>(); out.re = tmp.real(); out.im = tmp.imag(), d->SetScalar(std::complex<subtype>(value.re, value.im), units), type({defV, defV})) \
  ARRAY_(name, type, std::complex<subtype>)
#define __COMPLEX_(name, type, subtype, defV)				\
  type generic_get_ ## name(generic_t x) {				\
    type out;								\
    out.re = defV;							\
    out.im = defV;							\
    if (x.obj == NULL) {						\
      ygglog_error("Generic object is NULL");				\
      return out;							\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    if (!d->IsScalar<std::complex<subtype>>()) {			\
      ygglog_error("Generic object is not " #name);			\
      return out;							\
    }									\
    std::complex<subtype> tmp = d->GetScalar<std::complex<subtype>>();	\
    out.re = tmp.real();						\
    out.im = tmp.imag();						\
    return out;								\
  }									\
  int generic_set_ ## name(generic_t x, type value, const char* units) { \
    if (!is_generic_init(x)) {						\
      ygglog_error("Generic object is not initialized");		\
      return GENERIC_ERROR_;						\
    }									\
    rapidjson::Value* d = (rapidjson::Value*)(x.obj);		\
    std::complex<subtype> tmp(value.re, value.im);			\
    d->SetScalar(tmp, units);						\
    return GENERIC_SUCCESS_;						\
  }									\
  NESTED_GET_NOARGS_(name, type, {defV, defV})				\
  NESTED_SET_(name, (value, units), type value, const char* units)	\
  ARRAY_(name, type, std::complex<subtype>)
#define PYTHON_(name, method)						\
  STD_JSON_BASE_(name, python_t, d->Is ## method(), out.obj = d->GetPythonObjectRaw(), d->SetPythonObjectRaw(value.obj), init_python())
  
  STD_JSON_(bool, bool, Bool, false);
  STD_JSON_(integer, int, Int, 0);
  STD_JSON_BASE_(null, void*, d->IsNull(), out = NULL, d->SetNull(), NULL);
  STD_JSON_(number, double, Double, 0.0);
  STD_JSON_BASE_(string, const char*, d->IsString(), out = d->GetString(), d->SetString(value, strlen(value), generic_allocator(x)), 0);
  STD_JSON_NESTED_(object);
  STD_JSON_NESTED_(array);
  STD_JSON_NESTED_(any);
  STD_JSON_NESTED_(schema);
  SCALAR_(int8, int8_t, 0);
  SCALAR_(int16, int16_t, 0);
  SCALAR_(int32, int32_t, 0);
  SCALAR_(int64, int64_t, 0);
  SCALAR_(uint8, uint8_t, 0);
  SCALAR_(uint16, uint16_t, 0);
  SCALAR_(uint32, uint32_t, 0);
  SCALAR_(uint64, uint64_t, 0);
  SCALAR_(float, float, 0.0);
  SCALAR_(double, double, 0.0);
  COMPLEX_(complex_float, complex_float_t, float, 0.0);
  COMPLEX_(complex_double, complex_double_t, double, 0.0);
#ifdef YGGDRASIL_LONG_DOUBLE_AVAILABLE
  SCALAR_(long_double, long double, 0.0);
  COMPLEX_(complex_long_double, complex_long_double_t, long double, 0.0);
#endif // YGGDRASIL_LONG_DOUBLE_AVAILABLE
  // TODO: Check encoding?
  // SCALAR_(bytes, const char*, 0);
  // SCALAR_(unicode, const char*, 0);
  PYTHON_(python_class, PythonClass);
  PYTHON_(python_function, PythonFunction);
  PYTHON_(python_instance, PythonInstance);
  GEOMETRY_(obj, ObjWavefront);
  GEOMETRY_(ply, Ply);

#undef GEOMETRY_
#undef COMPLEX_
#undef PYTHON_
#undef SCALAR_
#undef ARRAY_
#undef STD_JSON_
#undef STD_UNITS_
#undef STD_JSON_BASE_
#undef STD_UNITS_BASE_
#undef STD_JSON_NESTED_
#undef NESTED_SET_
#undef NESTED_GET_
#undef NESTED_GET_NOARGS_
#undef NESTED_BASE_SET_
#undef NESTED_BASE_GET_
#undef NESTED_BASE_GET_NOARGS_
#undef GENERIC_ERROR_
#undef GENERIC_SUCCESS_

	    

  // Generic array methods
  size_t generic_array_get_size(generic_t x) {
    size_t out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_size: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_array_get_size: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!x_obj->IsArray()) {
	ygglog_throw_error("generic_array_get_size: Document is not an array.");
      }
      out = (size_t)(x_obj->Size());
    } catch (...) {
      ygglog_error("generic_array_get_size: C++ exception thrown.");
    }
    return out;
  }

  // Generic map methods
  size_t generic_map_get_size(generic_t x) {
    size_t out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_size: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_map_get_size: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!x_obj->IsObject()) {
	ygglog_throw_error("generic_map_get_size: Document is not an object.");
      }
      out = (size_t)(x_obj->MemberCount());
    } catch (...) {
      ygglog_error("generic_map_get_size: C++ exception thrown.");
    }
    return out;
  }
  int generic_map_has_key(generic_t x, char* key) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_has_key: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_map_has_key: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!x_obj->IsObject()) {
	ygglog_throw_error("generic_map_has_key: Document is not an object.");
      }
      if (x_obj->HasMember(key)) {
	out = 1;
      }
    } catch (...) {
      ygglog_error("generic_map_has_key: C++ exception thrown.");
    }
    return out;
  }
  size_t generic_map_get_keys(generic_t x, char*** keys) {
    size_t out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_keys: Object not initialized.");
      }
      if (x.obj == NULL) {
	ygglog_throw_error("generic_map_get_keys: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      if (!x_obj->IsObject()) {
	ygglog_throw_error("generic_map_get_keys: Document is not an object.");
      }
      out = (size_t)(x_obj->MemberCount());
      keys[0] = (char**)(generic_allocator(x).Malloc(out * sizeof(char*)));
      size_t i = 0;
      for (rapidjson::Document::ConstMemberIterator it = x_obj->MemberBegin();
	   it != x_obj->MemberEnd(); it++, i++) {
	keys[0][i] = (char*)(generic_allocator(x).Malloc(sizeof(char) * (it->name.GetStringLength() + 1)));
	strcpy(keys[0][i], it->name.GetString());
      }
    } catch (...) {
      ygglog_error("generic_map_get_keys: C++ exception thrown.");
      out = 0;
    }
    return out;
  }

  void destroy_python(python_t *x) {
    if (x != NULL) {
      if (x->obj != NULL) {
#ifndef YGGDRASIL_DISABLE_PYTHON_C_API
	Py_DECREF(x->obj);
#endif // YGGDRASIL_DISABLE_PYTHON_C_API
	x->obj = NULL;
      }
    }
  }

  python_t copy_python(python_t x) {
    python_t out = init_python();
    if (x.obj != NULL) {
#ifndef YGGDRASIL_DISABLE_PYTHON_C_API
      Py_INCREF(x.obj);
#endif // YGGDRASIL_DISABLE_PYTHON_C_API
      out.obj = x.obj;
    }
    return out;
  }

  void display_python(python_t x) {
    if (x.obj != NULL) {
#ifndef YGGDRASIL_DISABLE_PYTHON_C_API
      PyObject_Print_STDOUT(x.obj);
#endif // YGGDRASIL_DISABLE_PYTHON_C_API
    } else {
      printf("NULL");
    }
  }

  int skip_va_elements(const dtype_t* dtype, va_list_t *ap, bool pointers) {
    if (dtype == NULL) {
      return 0;
    }
    if (dtype->schema == NULL) {
      return 0;
    }
    return document_skip_vargs(((rapidjson::Value*)(dtype->schema))[0], *ap,
				 pointers);
  }
  
  int is_empty_dtype(const dtype_t* dtype) {
    if (dtype == NULL) {
      return 1;
    }
    if (dtype->schema == NULL) {
      return 1;
    }
    rapidjson::Value* s = (rapidjson::Value*)(dtype->schema);
    if (!s->HasMember("type")) {
      return 1;
    }
    return 0;
  }
  
  const char* dtype_name(const dtype_t* type_struct) {
    if (is_empty_dtype(type_struct)) {
      ygglog_error("dtype_name: Empty dtype.");
      return "";
    }
    rapidjson::Value* s = (rapidjson::Value*)(type_struct->schema);
    if (!(s->IsObject() && s->HasMember("type"))) {
      ygglog_error("dtype_name: type information not in schema");
      return "";
    }
    return (*s)["type"].GetString();
  }

  const char* dtype_subtype(const dtype_t* type_struct) {
    try {
      if (strcmp(dtype_name(type_struct), "scalar") != 0) {
	ygglog_throw_error("dtype_subtype: Only scalars have subtype.");
      }
      rapidjson::Value* s = (rapidjson::Value*)(type_struct->schema);
      if (!(s->IsObject() && s->HasMember("subtype"))) {
	ygglog_throw_error("dtype_subtype: No subtype in schema.");
      }
      return (*s)["subtype"].GetString();
    } catch(...) {
      ygglog_error("dtype_subtype: C++ exception thrown.");
      return "";
    }
  }

  const size_t dtype_precision(const dtype_t* type_struct) {
    try {
      if (strcmp(dtype_name(type_struct), "scalar") != 0) {
	ygglog_throw_error("dtype_precision: Only scalars have precision.");
      }
      rapidjson::Value* s = (rapidjson::Value*)(type_struct->schema);
      if (!(s->IsObject() && s->HasMember("precision"))) {
	ygglog_throw_error("dtype_precision: No precision in schema.");
      }
      return (size_t)((*s)["precision"].GetUint());
    } catch(...) {
      ygglog_error("dtype_precision: C++ exception thrown.");
      return 0;
    }
  };

  int set_dtype_name(dtype_t *dtype, const char* name) {
    if (dtype == NULL || dtype->schema == NULL) {
      ygglog_error("set_dtype_name: data type structure is NULL.");
      return -1;
    }
    rapidjson::Value* s = (rapidjson::Value*)(dtype->schema);
    if (s->IsObject() && s->HasMember("type")) {
      (*s)["type"].SetString(name, strlen(name), dtype_allocator(*dtype));
    } else {
      rapidjson::Value v(name, strlen(name), dtype_allocator(*dtype));
      s->AddMember(rapidjson::Document::GetTypeString(), v, dtype_allocator(*dtype));
    }
    return 0;
  }

  dtype_t* complete_dtype(dtype_t *dtype, const bool use_generic) {
    try {
      if (dtype == NULL) {
	return create_dtype(NULL, use_generic);
      }
    } catch (...) {
      ygglog_error("complete_dtype: C++ exception thrown.");
      return NULL;
    }
    return dtype;
  }

  int destroy_document(void** obj) {
    if (obj == NULL || obj[0] == NULL)
      return 0;
    rapidjson::Document* s = (rapidjson::Document*)(*obj);
    delete s;
    obj[0] = NULL;
    return 0;
  }

  int destroy_dtype(dtype_t **dtype) {
    int ret = 0;
    if (dtype != NULL) {
      if (dtype[0] != NULL) {
	rapidjson::Document* s = NULL;
	if ((dtype[0])->metadata != NULL) {
	  s = (rapidjson::Document*)((dtype[0])->metadata);
	} else if ((dtype[0])->schema != NULL) {
	  s = (rapidjson::Document*)((dtype[0])->schema);
	}
	if (s != NULL) {
	  try {
	    delete s;
	    dtype[0]->schema = NULL;
	    dtype[0]->metadata = NULL;
	  } catch (...) {
	    ygglog_error("destroy_dtype: C++ exception thrown in dtype2class.");
	    ret = -1;
	  }
	}
	free(dtype[0]);
	dtype[0] = NULL;
      }
    }
    return ret;
  }

  dtype_t* create_dtype_empty(const bool use_generic) {
    try {
      return create_dtype(NULL, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_empty: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_doc(void* type_doc, const bool use_generic) {
    rapidjson::Document* obj = NULL;
    try {
      obj = (rapidjson::Document*)type_from_doc_c(type_doc);
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_doc: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_python(PyObject* pyobj, const bool use_generic) {
    rapidjson::Document* obj = NULL;
    try {
      obj = type_from_pyobj(pyobj);
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_python: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_direct(const bool use_generic) {
    return create_dtype_default("string", use_generic);
  }

  dtype_t* create_dtype_default(const char* type, const bool use_generic) {
    rapidjson::Document* obj = NULL;
    try {
      obj = new rapidjson::Document();
      obj->StartObject();
      obj->Key("type", 4, true);
      obj->String(type, strlen(type), true);
      obj->EndObject(1);
      obj->FinalizeFromStack();
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_default: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_scalar(const char* subtype, const size_t precision,
			       const char* units, const bool use_generic) {
    rapidjson::Document* obj = NULL;
    try {
      obj = new rapidjson::Document();
      if (!add_dtype(obj, "scalar", subtype, precision, 0, NULL, units)) {
	ygglog_throw_error("create_dtype_scalar: Error in add_dtype");
      }
      obj->FinalizeFromStack();
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_scalar: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_format(const char *format_str,
			       const int as_array = 0,
			       const bool use_generic = false) {
    rapidjson::Document* obj = NULL;
    try {
      obj = create_dtype_format_class(format_str, as_array);
      return create_dtype(obj, use_generic, false, true);
    } catch(...) {
      ygglog_error("create_dtype_format: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_1darray(const char* subtype, const size_t precision,
				const size_t length, const char* units,
				const bool use_generic) {
    rapidjson::Document* obj = new rapidjson::Document;
    size_t ndim = 1;
    const size_t* shape = &length;
    if (length == 0)
      shape = NULL;
    if (!add_dtype(obj, "ndarray", subtype, precision, ndim, shape, units)) {
      ygglog_error("create_dtype_1darray: Error in add_dtype");
      CSafe(delete obj);
      return NULL;
    }
    obj->FinalizeFromStack();
    try {
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_1darray: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_ndarray(const char* subtype, const size_t precision,
				const size_t ndim, const size_t* shape,
				const char* units, const bool use_generic) {
    rapidjson::Document* obj = new rapidjson::Document;
    if (!add_dtype(obj, "ndarray", subtype, precision, ndim, shape, units)) {
      ygglog_error("create_dtype_ndarray: Error in add_dtype");
      CSafe(delete obj);
      return NULL;
    }
    obj->FinalizeFromStack();
    try {
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_ndarray: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ndarray_arr(const char* subtype, const size_t precision,
				    const size_t ndim, const int64_t shape[],
				    const char* units, const bool use_generic) {
    size_t *shape_ptr = (size_t*)malloc(ndim*sizeof(size_t));
    // size_t shape_size_t[ndim];
    size_t i;
    for (i = 0; i < ndim; i++) {
      shape_ptr[i] = (size_t)shape[i];
      // shape_size_t[i] = (size_t)shape[i];
    }
    // size_t* shape_ptr = shape_size_t;
    // const size_t* shape_ptr = shape;
    dtype_t* out = create_dtype_ndarray(subtype, precision, ndim, shape_ptr, units, use_generic);
    free(shape_ptr);
    return out;
  }
  dtype_t* create_dtype_json_array(const size_t nitems, dtype_t** items,
				   const bool use_generic=true){
    rapidjson::Document* obj = NULL;
    try {
      size_t i;
      if ((nitems > 0) && (items == NULL)) {
	ygglog_throw_error("create_dtype_json_array: %d items expected, but the items parameter is NULL.", nitems);
      }
      obj = new rapidjson::Document();
      size_t nprops = 1;
      obj->StartObject();
      obj->Key("type", 4, true);
      obj->String("array", 5, true);
      if (nitems > 0) {
	nprops++;
	obj->Key("items", 5, true);
	obj->StartArray();
	for (i = 0; i < nitems; i++) {
	  rapidjson::Document* iSchema = (rapidjson::Document*)(items[i]->schema);
	  if (!iSchema->Accept(*obj)) {
	    ygglog_throw_error("create_dtype_json_array: Error adding element %d.", i);
	  }
	}
	obj->EndArray(nitems);
      }
      obj->EndObject(nprops);
      obj->FinalizeFromStack();
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_json_array: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_json_object(const size_t nitems, char** keys,
				    dtype_t** values,
				    const bool use_generic=true) {
    rapidjson::Document* obj = NULL;
    try {
      size_t i;
      if ((nitems > 0) && ((keys == NULL) || (values == NULL))) {
	ygglog_throw_error("create_dtype_json_object: %d items expected, but the keys and/or values parameter is NULL.", nitems);
      }
      obj = new rapidjson::Document();
      size_t nprops = 1;
      obj->StartObject();
      obj->Key("type", 4, true);
      obj->String("object", 6, true);
      if (nitems > 0) {
	nprops++;
	obj->Key("properties", 10, true);
	obj->StartObject();
	for (i = 0; i < nitems; i++) {
	  obj->Key(keys[i], strlen(keys[i]), true);
	  rapidjson::Document* iSchema = (rapidjson::Document*)(values[i]->schema);
	  if (!iSchema->Accept(*obj)) {
	    ygglog_throw_error("create_dtype_json_array: Error adding element %d.", i);
	  }
	}
	obj->EndObject(nitems);
      }
      obj->EndObject(nprops);
      obj->FinalizeFromStack();
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_json_object: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ply(const bool use_generic) {
    return create_dtype_default("ply", use_generic);
  }
  dtype_t* create_dtype_obj(const bool use_generic) {
    return create_dtype_default("obj", use_generic);
  }
  dtype_t* create_dtype_ascii_table(const char *format_str, const int as_array,
				    const bool use_generic) {
    return create_dtype_format(format_str, as_array, use_generic);
  }
  dtype_t* create_dtype_pyobj(const char* type, const bool use_generic) {
    return create_dtype_default(type, use_generic);
  }
  dtype_t* create_dtype_pyinst(const char* class_name,
			       const dtype_t* args_dtype,
			       const dtype_t* kwargs_dtype,
			       const bool use_generic) {
    rapidjson::Document* obj = NULL;
    rapidjson::Document* args_type = NULL;
    rapidjson::Document* kwargs_type = NULL;
    try {
      size_t N = 0;
      obj = new rapidjson::Document();
      obj->StartObject();
      obj->Key("type", 4, true);
      obj->String("instance", 8, true);
      N++;
      if (args_dtype != NULL) {
	args_type = (rapidjson::Document*)(args_dtype->schema);
	obj->Key("args", 4, true);
	if (!args_type->Accept(*obj)) {
	  ygglog_throw_error("create_dtype_pyinst: Error adding args");
	}
	N++;
      }
      if (kwargs_dtype != NULL) {
	kwargs_type = (rapidjson::Document*)(kwargs_dtype->schema);
	obj->Key("kwargs", 6, true);
	if (!kwargs_type->Accept(*obj)) {
	  ygglog_throw_error("create_dtype_pyinst: Error adding kwargs");
	}
	N++;
      }
      obj->EndObject(N);
      obj->FinalizeFromStack();
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_pyinst: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_schema(const bool use_generic) {
    return create_dtype_default("schema", use_generic);
  }
  dtype_t* create_dtype_any(const bool use_generic) {
    return create_dtype_default("any", use_generic);
  }
  int format_comm_header(comm_head_t* head, char **buf, size_t buf_siz,
			 const size_t max_header_size, const int no_type) {
    try {
      // JSON Serialization
      rapidjson::StringBuffer head_buf = format_comm_header_json(*head, no_type);
      rapidjson::StringBuffer type_buf;
      // Check size
      int ret;
#ifdef _WIN32
      ret = _scprintf("%s%s%s", MSG_HEAD_SEP, head_buf.GetString(), MSG_HEAD_SEP);
#else
      ret = snprintf(*buf, 0, "%s%s%s", MSG_HEAD_SEP, head_buf.GetString(), MSG_HEAD_SEP);
#endif
      if (ret > max_header_size) {
	type_buf = format_comm_header_json(*head, no_type, true);
	head->flags = head->flags | HEAD_META_IN_DATA;
	head->size = head->size + strlen(MSG_HEAD_SEP) + strlen(type_buf.GetString());
	head_buf = format_comm_header_json(*head, no_type);
#ifdef _WIN32
	ret = _scprintf("%s%s%s%s%s", MSG_HEAD_SEP,
			head_buf.GetString(), MSG_HEAD_SEP,
			type_buf.GetString(), MSG_HEAD_SEP);
#else
	ret = snprintf(*buf, 0, "%s%s%s%s%s", MSG_HEAD_SEP,
		       head_buf.GetString(), MSG_HEAD_SEP,
		       type_buf.GetString(), MSG_HEAD_SEP);
#endif
      }
      // Realloc if necessary
      if ((size_t)ret > buf_siz) {
	buf_siz = (size_t)(ret+1);
	buf[0] = (char*)realloc(buf[0], buf_siz);
      }
      // Format
      if (head->flags & HEAD_META_IN_DATA) {
	ret = snprintf(*buf, buf_siz-1, "%s%s%s%s%s", MSG_HEAD_SEP,
		       head_buf.GetString(), MSG_HEAD_SEP,
		       type_buf.GetString(), MSG_HEAD_SEP);
      } else {
	ret = snprintf(*buf, buf_siz-1, "%s%s%s", MSG_HEAD_SEP,
		       head_buf.GetString(), MSG_HEAD_SEP);
      }
      if ((size_t)ret > buf_siz) {
	ygglog_error("format_comm_header: Header size (%d) exceeds buffer size (%lu): '%s%s%s'.",
		     ret, buf_siz, MSG_HEAD_SEP, head_buf.GetString(), MSG_HEAD_SEP);
	return -1;
      }
      ygglog_debug("format_comm_header: Header = '%s'", *buf);
      return ret;
    } catch(...) {
      ygglog_error("format_comm_header: C++ exception thrown.");
      return -1;
    }
  }

  int parse_type_in_data(char **buf, const size_t buf_siz,
			 comm_head_t* head) {
    size_t typesiz;
    int ret;
    size_t sind, eind;
    try {
      ret = find_match(MSG_HEAD_SEP, *buf, &sind, &eind);
      if (ret < 0) {
	ygglog_error("parse_type_in_data: Error locating head separation tag.");
	return -1;
      }
      // type = *buf;
      typesiz = sind;
      rapidjson::Document type_doc;
      type_doc.Parse(*buf, typesiz);
      head->dtype = create_dtype(type_from_header_doc(type_doc));
      ret = buf_siz - eind;
      memmove(*buf, *buf + eind, ret);
      return ret;
    } catch(...) {
      ygglog_error("parse_type_in_data: C++ exception thrown.");
      return -1;
    }
  }

  comm_head_t parse_comm_header(const char *buf, const size_t buf_siz) {
    comm_head_t out = init_header(0, NULL, NULL);
    int ret;
    char *head = NULL;
    size_t headsiz;
    try {
      // Split header/body
      ret = split_head_body(buf, buf_siz, &head, &headsiz);
      if (ret < 0) {
	ygglog_error("parse_comm_header: Error splitting head and body.");
	out.flags = out.flags & ~HEAD_FLAG_VALID;
	if (head != NULL) 
	  free(head);
	return out;
      }
      out.bodybeg = headsiz + 2*strlen(MSG_HEAD_SEP);
      out.bodysiz = buf_siz - out.bodybeg;
      // Handle raw data without header
      if (headsiz == 0) {
	out.flags = out.flags & ~HEAD_FLAG_MULTIPART;
	out.size = out.bodysiz;
	free(head);
	return out;
      }
      // Parse header
      rapidjson::Document head_doc;
      head_doc.Parse(head, headsiz);
      if (!(update_header_from_doc(out, head_doc))) {
	ygglog_error("parse_comm_header: Error updating header from JSON doc.");
	out.flags = out.flags & ~HEAD_FLAG_VALID;
	free(head);
	return out;
      }
      free(head);
      return out;
    } catch(...) {
      ygglog_error("parse_comm_header: C++ exception thrown.");
      out.flags = out.flags & ~HEAD_FLAG_VALID;
      if (head != NULL)
	free(head);
      return out;
    }
  }

  dtype_t* copy_dtype(const dtype_t* dtype) {
    if (dtype == NULL) {
      return NULL;
    }
    dtype_t* out = NULL;
    try {
      rapidjson::Value* s_old = (rapidjson::Value*)(dtype->schema);
      rapidjson::Document* s_new = copy_document(s_old);
      return create_dtype(s_new, false);
    } catch (...) {
      ygglog_error("copy_dtype: C++ exception thrown.");
      destroy_dtype(&out);
      return NULL;
    }
  }

  int dtype_uses_generic(dtype_t* dtype) {
    if (dtype == NULL)
      return 0;
    rapidjson::Value* schema = (rapidjson::Value*)(dtype->schema);
    if (schema == NULL)
      return 0;
    if (schema->HasMember("use_generic") &&
	(*schema)["use_generic"].IsBool() &&
	(*schema)["use_generic"].GetBool()) {
      return 1;
    }
    return 0;
  }

  int update_dtype(dtype_t* dtype1, void* schema2) {
    try {
      if (schema2 == NULL) {
	ygglog_throw_error("update_dtype: Could not recover type to update from.");
      } else if (dtype1 == NULL) {
	ygglog_throw_error("update_dtype: Could not recover type for update.");
      } else if (is_empty_dtype(dtype1)) {
	bool use_generic = false;
	if (dtype1->schema != NULL) {
	  // TODO: preserve metadata
	  use_generic = dtype_uses_generic(dtype1);
	  rapidjson::Document* s_old = NULL;
	  if (dtype1->metadata != NULL)
	    s_old = (rapidjson::Document*)(dtype1->metadata);
	  else
	    s_old = (rapidjson::Document*)(dtype1->schema);
	  delete s_old;
	  dtype1->schema = NULL;
	  dtype1->metadata = NULL;
	}
	rapidjson::Document* s_new = copy_document((rapidjson::Value*)(schema2));
	if (use_generic) {
	  s_new->AddMember(rapidjson::Value("use_generic", 11, s_new->GetAllocator()).Move(),
			   rapidjson::Value(true).Move(),
			   s_new->GetAllocator());
	}
	dtype1->schema = (void*)s_new;
      } else {
	rapidjson::Document* s_old = (rapidjson::Document*)(dtype1->schema);
	rapidjson::Document* s_new = (rapidjson::Document*)(schema2);
	rapidjson::SchemaDocument sd_old(*s_old);
	rapidjson::SchemaNormalizer n(sd_old);
	if (!n.Compare(*s_new)) {
	  throw_validator_error("update_dtype", n);
	}
      }
    } catch (...) {
      ygglog_error("update_dtype: C++ exception thrown.");
      return -1;
    }
    return 0;
  }

  int update_dtype_from_generic_ap(dtype_t* dtype1, va_list_t ap) {
    if (!(is_empty_dtype(dtype1) && dtype_uses_generic(dtype1))) {
      return 0;
    }
    try {
      generic_t gen_arg;
      if (!get_va_list(ap, gen_arg))
	return -1;
      if (!(is_generic_init(gen_arg))) {
	ygglog_throw_error("update_dtype_from_generic_ap: Type expects generic object, but provided object is not generic.");
      } else {
	dtype_t dtype2;
	if (gen_arg.obj == NULL) {
	  ygglog_throw_error("update_dtype_from_generic_ap: Type in generic class is NULL.");
	}
	rapidjson::Document* type_class = encode_schema((rapidjson::Value*)(gen_arg.obj));
	dtype2.schema = (void*)(type_class);
	if (update_dtype(dtype1, dtype2.schema) < 0) {
	  return -1;
	}
	delete type_class;
      }
    } catch (...) {
      ygglog_error("update_dtype_from_generic_ap: C++ exception thrown.");
      return -1;
    }
    return 0;
  }
  
  int update_precision_dtype(dtype_t* dtype,
			     const size_t new_precision) {
    rapidjson::Value* s = (rapidjson::Value*)(dtype->schema);
    if (s == NULL || !s->IsObject()) {
      ygglog_error("update_precision_dtype: No datatype schema.");
      return -1;
    }
    typename rapidjson::Value::MemberIterator it = s->FindMember(rapidjson::Document::GetTypeString());
    if (it == s->MemberEnd()) {
      ygglog_error("update_precision_dtype: No 'type' information in schema.");
      return -1;
    }
    if (it->value != rapidjson::Document::GetScalarString()) {
      ygglog_error("update_precision_dtype: Can only update precision for bytes or unicode scalars.");
      return -1;
    }
    it = s->FindMember(rapidjson::Document::GetPrecisionString());
    if (it == s->MemberEnd()) {
      rapidjson::Value v((uint64_t)new_precision);
      s->AddMember(rapidjson::Document::GetPrecisionString(), v, dtype_allocator(*dtype));
    } else {
      it->value.SetUint64((uint64_t)new_precision);
    }
    return 0;
  }

  int deserialize_document(const char* buf, size_t buf_siz, void** document) {
    rapidjson::Document* d = (rapidjson::Document*)(document[0]);
    if (d == NULL) {
      d = new rapidjson::Document();
      document[0] = d;
    }
    rapidjson::StringStream s(buf);
    d->ParseStream(s);
    return 1;
  }

  int serialize_document(char **buf, size_t *buf_siz, void* document) {
    rapidjson::Value* d = (rapidjson::Value*)document;
    if (d == NULL)
      return 0;
    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    if (!d->Accept(writer))
      return 0;
    if ((size_t)(buffer.GetLength() + 1) > buf_siz[0]) {
      buf_siz[0] = (size_t)(buffer.GetLength() + 1);
      buf[0] = (char*)realloc(buf[0], buf_siz[0]);
    }
    memcpy(buf[0], buffer.GetString(), (size_t)(buffer.GetLength()));
    buf[0][(size_t)(buffer.GetLength())] = '\0';
    return 1;
  }

  int deserialize_dtype(const dtype_t *dtype, const char *buf, const size_t buf_siz,
			const int allow_realloc, va_list_t ap) {
    try {
      size_t nargs_orig = ap.nargs[0];
      rapidjson::Document* d = NULL;
      if (!deserialize_document(buf, buf_siz, (void**)(&d)))
	return -1;
      if (d == NULL) {
	ygglog_throw_error("deserialize_dtype: Document is NULL");
	return -1;
      }
      if (dtype->schema != NULL) {
	if (!normalize_document((rapidjson::Document*)d,
				(rapidjson::Document*)(dtype->schema)))
	  return -1;
      }
      if (!document2args(d, (rapidjson::Document*)(dtype->schema),
			 ap, allow_realloc))
	return -1;
      return (int)(nargs_orig - ap.nargs[0]);
    } catch (...) {
      ygglog_error("deserialize_dtype: C++ exception thrown.");
      return -1;
    }
  }

  int serialize_dtype(const dtype_t *dtype, char **buf, size_t *buf_siz,
		      const int allow_realloc, va_list_t ap) {
    try {
      rapidjson::Document d;
      if (!args2document(&d, (rapidjson::Value*)(dtype->schema), ap))
	return -1;
      if (!serialize_document(buf, buf_siz, (void*)(&d)))
	return -1;
      return (int)strlen(buf[0]);
    } catch(...) {
      ygglog_error("serialize_dtype: C++ exception thrown.");
      return -1;
    }
  }

  void display_dtype(const dtype_t *dtype, const char* indent="") {
    rapidjson::Value* s = (rapidjson::Value*)(dtype->schema);
    display_document(s, indent);
  }

  size_t nargs_exp_dtype(const dtype_t *dtype, const int for_fortran_recv) {
    rapidjson::Value* s = (rapidjson::Value*)(dtype->schema);
    if (s == NULL)
      return 0;
    size_t count = 0;
    if (!schema_count_vargs(*s, count, 0, for_fortran_recv))
      return 0;
    return count;
  }

  // ObjWavefront wrapped methods
  obj_t init_obj() {
    obj_t x;
    x.obj = NULL;
    x.nvert = 0;
    x.ntexc = 0;
    x.nnorm = 0;
    x.nparam = 0;
    x.npoint = 0;
    x.nline = 0;
    x.nface = 0;
    x.ncurve = 0;
    x.ncurve2 = 0;
    x.nsurf = 0;
    return x;
  }

  void set_obj(obj_t* x, void* obj, int copy) {
    if (obj != NULL) {
      rapidjson::ObjWavefront* objw = (rapidjson::ObjWavefront*)obj;
      if (copy) {
	rapidjson::ObjWavefront* cpy = new rapidjson::ObjWavefront(*objw);
	x->obj = cpy;
      } else {
	x->obj = objw;
      }
      std::map<std::string,size_t> counts = objw->element_counts();
#define SET_COUNTS_(ele, Ndst)						\
      if (counts.find(#ele) != counts.end()) {				\
	Ndst = (int)(counts[#ele]);					\
      }
      SET_COUNTS_(v, x->nvert);
      SET_COUNTS_(vt, x->ntexc);
      SET_COUNTS_(vn, x->nnorm);
      SET_COUNTS_(vp, x->nparam);
      SET_COUNTS_(p, x->npoint);
      SET_COUNTS_(l, x->nline);
      SET_COUNTS_(f, x->nface);
      SET_COUNTS_(curv, x->ncurve);
      SET_COUNTS_(curv2, x->ncurve2);
      SET_COUNTS_(surf, x->nsurf);
#undef SET_COUNTS_
    }
  }

  void free_obj(obj_t *p) {
    if (p != NULL) {
      if (p->obj != NULL) {
	rapidjson::ObjWavefront* obj = (rapidjson::ObjWavefront*)(p->obj);
	p->obj = NULL;
	delete obj;
      }
    }
  }

  obj_t copy_obj(obj_t src) {
    obj_t out = init_obj();
    set_obj(&out, src.obj, 1);
    return out;
  }

  void display_obj_indent(obj_t p, const char* indent) {
    if (p.obj == NULL) {
      printf("%sNULL\n", indent);
    } else {
      rapidjson::ObjWavefront* obj = (rapidjson::ObjWavefront*)(p.obj);
      std::string s = obj->as_string();
      std::string s_indent(indent);
      size_t orig_size = s.size(), j = 0;
      for (size_t i = 0; i < orig_size; i++) {
	if (s[j] == '\n') {
	  s.insert(j + 1, s_indent);
	  j += s_indent.size();
	}
	j++;
      }
      printf("%s%s\n", indent, s.c_str());
    }
  }
  void display_obj(obj_t p) {
    return display_obj_indent(p, "");
  }


  // Ply wrapped methods
  ply_t init_ply() {
    ply_t x;
    x.obj = NULL;
    x.nvert = 0;
    x.nedge = 0;
    x.nface = 0;
    return x;
  }

  void set_ply(ply_t* x, void* obj, int copy) {
    if (x == NULL)
      return;
    if (obj != NULL) {
      rapidjson::Ply* objw = (rapidjson::Ply*)obj;
      if (copy) {
	rapidjson::Ply* cpy = new rapidjson::Ply(*objw);
	x->obj = cpy;
      } else {
	x->obj = objw;
      }
      std::map<std::string,size_t> counts = objw->element_counts();
#define SET_COUNTS_(ele, Ndst)						\
      if (counts.find(#ele) != counts.end()) {				\
	Ndst = (int)(counts[#ele]);					\
      }
      SET_COUNTS_(vertex, x->nvert)
      SET_COUNTS_(edge, x->nedge)
      SET_COUNTS_(face, x->nface)
      #undef SET_COUNTS_
    }
  }

  void free_ply(ply_t *p) {
    if (p != NULL) {
      if (p->obj != NULL) {
	rapidjson::Ply* obj = (rapidjson::Ply*)(p->obj);
	p->obj = NULL;
	delete obj;
      }
    }
  }

  ply_t copy_ply(ply_t src) {
    ply_t out = init_ply();
    set_ply(&out, src.obj, 1);
    return out;
  }

  void display_ply_indent(ply_t p, const char* indent) {
    if (p.obj == NULL) {
      printf("%sNULL\n", indent);
    } else {
      rapidjson::Ply* obj = (rapidjson::Ply*)(p.obj);
      std::string s = obj->as_string();
      std::string s_indent(indent);
      size_t orig_size = s.size(), j = 0;
      for (size_t i = 0; i < orig_size; i++) {
	if (s[j] == '\n') {
	  s.insert(j + 1, s_indent);
	  j += s_indent.size();
	}
	j++;
      }
      printf("%s%s\n", indent, s.c_str());
    }
  }

  void display_ply(ply_t p) {
    return display_ply_indent(p, "");
  }

  int init_python_API() {
    try {
#ifndef YGGDRASIL_DISABLE_PYTHON_C_API
      rapidjson::init_python_API();
#endif // YGGDRASIL_DISABLE_PYTHON_C_API
    } catch(...) {
      ygglog_error("init_python_API: C++ exception thrown.");
      return 1;
    }
    return 0;
  }
  
}

// Local Variables:
// mode: c++
// End:
