#include "../tools.h"
#include "datatypes.h"
#include "utils.h"
#include "serialization.h"

#define RAPIDJSON_YGGDRASIL
#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/prettywriter.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/schema.h"
#include "rapidjson/va_list.h"


#define STRLEN_RJ(var)				\
  static_cast<rapidjson::SizeType>(strlen(var))

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
  if (x.obj == NULL)
    ygglog_throw_error("generic_allocator: Not initialized");
  return ((rapidjson::Document*)(x.obj))->GetAllocator();
};

rapidjson::Document::AllocatorType& generic_ref_allocator(generic_ref_t& x) {
  if (x.obj == NULL)
    ygglog_throw_error("generic_ref_allocator: Not initialized");
  return *((rapidjson::Document::AllocatorType*)(x.allocator));
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

// rapidjson::Document* type_from_doc(const rapidjson::Value &type_doc) {
//   if (!(type_doc.IsObject()))
//     ygglog_throw_error("type_from_doc: Parsed document is not an object.");
//   if (!(type_doc.HasMember("serializer") || !type_doc["serializer"].IsObject()))
//     ygglog_throw_error("type_from_doc: Parsed document does not have a serializer field");
//   if (!(type_doc["serializer"].HasMember("datatype")) || !type_doc["serializer"]["datatype"].IsObject())
//     ygglog_throw_error("type_from_doc: Parsed document does not have datatype field");
//   rapidjson::Document* out = new rapidjson::Document;
//   type_doc["serializer"]["datatype"].Accept(*out);
//   out->FinalizeFromStack();
//   return out;
// };


// rapidjson::Document* type_from_header_doc(const rapidjson::Value &header_doc) {
//   if (!(header_doc.IsObject()))
//     ygglog_throw_error("type_from_header_doc: Parsed document is not an object.");
//   if (!(header_doc.HasMember("serializer")))
//     ygglog_throw_error("type_from_header_doc: Parsed header dosn't contain serializer information.");
//   if (!(header_doc["serializer"].IsObject()))
//     ygglog_throw_error("type_from_header_doc: Serializer info in parsed header is not an object.");
//   if (!(header_doc["serializer"].HasMember("datatype")))
//     ygglog_throw_error("type_from_header_doc: Parsed header dosn't contain type information.");
//   if (!(header_doc["serializer"]["datatype"].IsObject()))
//     ygglog_throw_error("type_from_header_doc: Type information in parsed header is not an object.");
//   // TODO: Add information from header_doc like format_str?
//   return type_from_doc(header_doc["serializer"]["datatype"]);
// };


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

void display_document(rapidjson::Value* rhs, const char* indent="") {
  if (rhs == NULL) {
    ygglog_error("document2string: NULL document");
    printf("\n");
    return;
  }
  std::string s = document2string(*rhs, indent);
  printf("%s\n", s.c_str());
}

rapidjson::Document* create_dtype_format_class(const char *format_str,
					       const int as_array = 0) {
  rapidjson::Document* out = new rapidjson::Document;
  out->StartObject();
  out->Key("serializer", 10, true);
  out->StartObject();
  out->Key("format_str", 10, true);
  out->String(format_str, STRLEN_RJ(format_str), true);
  out->Key("datatype", 8, true);
  out->StartObject();
  int nDtype = 0;
  nDtype++;
  out->Key("type", 4, true);
  out->String("array", 5, true);
  nDtype++;
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
  if (nOuter == 1) {
    nDtype++;
    out->Key("allowSingular", 13, true);
    out->Bool(true);
  }
  out->EndObject(nDtype);
  out->EndObject(2);
  out->EndObject(1);
  out->FinalizeFromStack();
  // if (nOuter == 1) {
  //   typename rapidjson::Document::ValueType tmp;
  //   (*out)["serializer"]["datatype"].Swap(tmp);
  //   (*out)["serializer"]["datatype"].Swap(tmp["items"][0]);
  //   (*out)["serializer"].RemoveMember("format_str");
  // }
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
      rapidjson::StringBuffer sb;
      if (!document->Normalize(s, &sb)) {
	ygglog_throw_error("create_dtype: Failed to normalize schema:\n"
			   "%s\nerror =\n%s",
			   document2string(*document).c_str(),
			   sb.GetString());
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
    out.obj = NULL;
    return out;
  }

  generic_ref_t init_generic_ref(generic_t parent) {
    generic_ref_t out;
    out.obj = parent.obj;
    out.allocator = (void*)(&(((rapidjson::Document*)(parent.obj))->GetAllocator()));
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

  int is_generic_init(generic_t x) {
    return true;
  }
  
  int destroy_generic(generic_t* x) {
    int ret = 0;
    if (x != NULL) {
      if (is_generic_init(*x)) {
	if (x->obj != NULL) {
	  try {
	    rapidjson::Document* obj = (rapidjson::Document*)(x->obj);
	    delete obj;
	    x->obj = NULL;
	  } catch (...) {
	    ygglog_error("destroy_generic: C++ exception thrown in destructor for rapidjson::Document.");
	    ret = -1;
	  }
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
	display_document((rapidjson::Document*)(x.obj));
      }
    } catch (...) {
      ygglog_error("display_generic: C++ exception thrown.");
    }
  }

#define GENERIC_SUCCESS_ 0
#define GENERIC_ERROR_ -1

  void* generic_ref_get_item(generic_ref_t x, const char *type) {
    void* out = NULL;
    try {
      if (x.obj == NULL) {
	ygglog_throw_error("generic_ref_get_item: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      std::string typeS(type);
      document_check_type(x_obj, typeS);
      bool requires_freeing = false;
      out = x_obj->GetDataPtr(requires_freeing);
    } catch (...) {
      ygglog_error("generic_ref_get_item: C++ exception thrown.");
      out = NULL;
    }
    return out;
  }
  void* generic_get_item(generic_t x, const char *type) {
    generic_ref_t x_ref = init_generic_ref(x);
    return generic_ref_get_item(x_ref, type);
  }
  int generic_ref_get_item_nbytes(generic_ref_t x, const char *type) {
    int out = -1;
    try {
      if (x.obj == NULL) {
	ygglog_throw_error("generic_ref_get_item_nbytes: Object is NULL.");
      }
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      std::string typeS(type);
      document_check_type(x_obj, typeS);
      out = x_obj->GetNBytes();
    } catch (...) {
      ygglog_error("generic_ref_get_item_nbytes: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_get_item_nbytes(generic_t x, const char *type) {
    generic_ref_t x_ref = init_generic_ref(x);
    return generic_ref_get_item_nbytes(x_ref, type);
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
      else CASE_(string, SetString(((char*)value), STRLEN_RJ((char*)value),
				   generic_allocator(x))) // Shouuld this be cast to char**?
      else if (typeS == std::string("any") ||
	       typeS == std::string("instance") ||
	       typeS == std::string("schema") ||
	       typeS == std::string("array") ||
	       typeS == std::string("object")) {
	x_obj->CopyFrom(((rapidjson::Value*)value)[0],
			generic_allocator(x), true);
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
  void* generic_ref_get_scalar(generic_ref_t x, const char *subtype, const size_t precision) {
    try {
      std::string typeS("scalar");
      std::string subtypeS(subtype);
      document_check_yggtype((rapidjson::Value*)(x.obj), typeS, subtypeS, precision);
    } catch(...) {
      ygglog_error("generic_ref_get_scalar: C++ exception thrown");
      return NULL;
    }
    return generic_ref_get_item(x, "scalar");
  }
  void* generic_get_scalar(generic_t x, const char *subtype, const size_t precision) {
    generic_ref_t x_ref = init_generic_ref(x);
    return generic_ref_get_scalar(x_ref, subtype, precision);
  }
  size_t generic_ref_get_1darray(generic_ref_t x, const char *subtype, const size_t precision, void** data) {
    size_t new_length = 0;
    try {
      std::string typeS("1darray");
      std::string subtypeS(subtype);
      document_check_yggtype((rapidjson::Value*)(x.obj), typeS, subtypeS, precision);
      void* new_data = generic_ref_get_item(x, "1darray");
      if (new_data == NULL)
	return 0;
      size_t nbytes = generic_ref_get_item_nbytes(x, "1darray");
      if (nbytes == 0)
	return 0;
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      new_length = (size_t)(x_obj->GetNElements());
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_ref_get_1darray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
    } catch (...) {
      ygglog_error("generic_ref_get_1darray: C++ exception thrown");
      return 0;
    }
    return new_length;
  }
  size_t generic_get_1darray(generic_t x, const char *subtype, const size_t precision, void** data) {
    generic_ref_t x_ref = init_generic_ref(x);
    return generic_ref_get_1darray(x_ref, subtype, precision, data);
  }
  size_t generic_ref_get_ndarray(generic_ref_t x, const char *subtype, const size_t precision, void** data, size_t** shape) {
    size_t new_ndim = 0;
    try {
      std::string typeS("ndarray");
      std::string subtypeS(subtype);
      document_check_yggtype((rapidjson::Value*)(x.obj), typeS, subtypeS, precision);
      void* new_data = generic_ref_get_item(x, "ndarray");
      if (new_data == NULL)
	return 0;
      size_t nbytes = generic_ref_get_item_nbytes(x, "ndarray");
      if (nbytes == 0)
	return 0;
      rapidjson::Value* x_obj = (rapidjson::Value*)(x.obj);
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_ref_get_ndarray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
      const rapidjson::Value& rjshape = x_obj->GetShape();
      new_ndim = (size_t)(rjshape.Size());
      size_t i = 0;
      shape[0] = (size_t*)realloc(shape[0], new_ndim);
      if (shape[0] == NULL) {
	ygglog_throw_error("generic_ref_get_ndarray: Failed to reallocate shape.");
      }
      for (rapidjson::Value::ConstValueIterator it = rjshape.Begin();
	   it != rjshape.End(); it++, i++) {
	shape[0][i] = (size_t)(it->GetInt());
      }
    } catch (...) {
      ygglog_error("generic_ref_get_ndarray: C++ exception thrown");
      return 0;
    }
    return new_ndim;
  }
  size_t generic_get_ndarray(generic_t x, const char *subtype, const size_t precision, void** data, size_t** shape) {
    generic_ref_t x_ref = init_generic_ref(x);
    return generic_ref_get_ndarray(x_ref, subtype, precision, data, shape);
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
		       rapidjson::Value(subtype, STRLEN_RJ(subtype),
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetPrecisionString(),
		       rapidjson::Value((unsigned)precision).Move(),
		       schema.GetAllocator());
      if (units && strlen(units) > 0) {
	schema.AddMember(rapidjson::Document::GetUnitsString(),
			 rapidjson::Value(units, STRLEN_RJ(units),
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
		       rapidjson::Value(subtype, STRLEN_RJ(subtype),
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetPrecisionString(),
		       rapidjson::Value((unsigned)precision).Move(),
		       schema.GetAllocator());
      if (units && strlen(units) > 0) {
	schema.AddMember(rapidjson::Document::GetUnitsString(),
			 rapidjson::Value(units, STRLEN_RJ(units),
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
		       rapidjson::Value(subtype, STRLEN_RJ(subtype),
					schema.GetAllocator()).Move(),
		       schema.GetAllocator());
      schema.AddMember(rapidjson::Document::GetPrecisionString(),
		       rapidjson::Value((unsigned)precision).Move(),
		       schema.GetAllocator());
      if (units && strlen(units) > 0) {
	schema.AddMember(rapidjson::Document::GetUnitsString(),
			 rapidjson::Value(units, STRLEN_RJ(units),
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
      generic_ref_t tmp;						\
      if (get_generic_ ## base ## _ref(x, idx, &tmp) != GENERIC_SUCCESS_) { \
	return NULL;							\
      }									\
      return generic_ref_get_item(tmp, type);				\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get: C++ exception thrown");	\
      return NULL;							\
    }									\
  }									\
  int generic_ ## base ## _get_item_nbytes(generic_t x, idxType idx, const char *type) { \
    try {								\
      generic_ref_t tmp;						\
      if (get_generic_ ## base ## _ref(x, idx, &tmp) != GENERIC_SUCCESS_) { \
	return 0;							\
      }									\
      return generic_ref_get_item_nbytes(tmp, type);			\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_nbytes: C++ exception thrown"); \
      return 0;								\
    }									\
  }									\
  void* generic_ ## base ## _get_scalar(generic_t x, idxType idx, const char *subtype, const size_t precision) { \
    try {								\
      generic_ref_t tmp;						\
      if (get_generic_ ## base ## _ref(x, idx, &tmp) != GENERIC_SUCCESS_) { \
	return NULL;							\
      }									\
      return generic_ref_get_scalar(tmp, subtype, precision);		\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_scalar: C++ exception thrown"); \
      return NULL;							\
    }									\
  }									\
  size_t generic_ ## base ## _get_1darray(generic_t x, idxType idx, const char *subtype, const size_t precision, void** data) { \
    try {								\
      generic_ref_t tmp;						\
      if (get_generic_ ## base ## _ref(x, idx, &tmp) != GENERIC_SUCCESS_) { \
	return 0;							\
      }									\
      return generic_ref_get_1darray(tmp, subtype, precision, data);	\
    } catch(...) {							\
      ygglog_error("generic_" #base "_get_1darray: C++ exception thrown"); \
      return 0;								\
    }									\
  }									\
  size_t generic_ ## base ## _get_ndarray(generic_t x, idxType idx, const char *subtype, const size_t precision, void** data, size_t** shape) { \
    try {								\
      generic_ref_t tmp;							\
      if (get_generic_ ## base ## _ref(x, idx, &tmp) != GENERIC_SUCCESS_) { \
	return 0;							\
      }									\
      return generic_ref_get_ndarray(tmp, subtype, precision, data, shape); \
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

  int get_generic_array_ref(generic_t arr, const size_t i, generic_ref_t *x) {
    int out = GENERIC_SUCCESS_;
    x[0] = init_generic_ref(arr);
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("get_generic_array_ref: Array is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("get_generic_array_ref: Array is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      if (!arr_obj->IsArray()) {
	ygglog_throw_error("get_generic_array_ref: Document is not an array.");
      }
      if (arr_obj->Size() <= i) {
	ygglog_throw_error("get_generic_array_ref: Document only has %d elements", (int)(arr_obj->Size()));
      }
      x[0].obj = (void*)(&((*arr_obj)[i]));
      // x[0].allocator = (void*)(&generic_allocator(arr));
    } catch (...) {
      ygglog_error("get_generic_array_ref: C++ exception thrown.");
      out = GENERIC_ERROR_;
    }
    return out;
  }
  int get_generic_array(generic_t arr, const size_t i, generic_t *x) {
    int out = GENERIC_SUCCESS_;
    generic_ref_t tmp;
    if (get_generic_array_ref(arr, i, &tmp) != GENERIC_SUCCESS_)
      return GENERIC_ERROR_;
    try {
      x[0] = init_generic();
      rapidjson::Value* src = (rapidjson::Value*)(tmp.obj);
      rapidjson::Document* cpy = new rapidjson::Document();
      if (!(src->Accept(*cpy))) {
	ygglog_throw_error("get_generic_array: Error in Accept");
      }
      cpy->FinalizeFromStack();
      x[0].obj = (void*)cpy;
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
	rapidjson::Value key(k, STRLEN_RJ(k), generic_allocator(arr));
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

  int get_generic_object_ref(generic_t arr, const char* k, generic_ref_t *x) {
    int out = 0;
    x[0] = init_generic_ref(arr);
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("get_generic_object_ref: Object is not a generic object.");
      }
      if (arr.obj == NULL) {
	ygglog_throw_error("get_generic_object_ref: Object is NULL.");
      }
      rapidjson::Value* arr_obj = (rapidjson::Value*)(arr.obj);
      if (!arr_obj->IsObject()) {
	ygglog_throw_error("get_generic_object_ref: Document is not an object.");
      }
      if (!arr_obj->HasMember(k)) {
	ygglog_throw_error("get_generic_object_ref: Document does not have the requested key.");
      }
      x[0].obj = (void*)(&((*arr_obj)[k]));
      // x[0].allocator = (void*)(&generic_allocator(arr));
    } catch (...) {
      ygglog_error("get_generic_object_ref: C++ exception thrown.");
      out = 1;
    }
    return out;
  }
  int get_generic_object(generic_t arr, const char* k, generic_t *x) {
    int out = GENERIC_SUCCESS_;
    generic_ref_t tmp;
    if (get_generic_object_ref(arr, k, &tmp) != GENERIC_SUCCESS_)
      return GENERIC_ERROR_;
    try {
      x[0] = init_generic();
      rapidjson::Value* src = (rapidjson::Value*)(tmp.obj);
      rapidjson::Document* cpy = new rapidjson::Document();
      if (!(src->Accept(*cpy))) {
	ygglog_throw_error("get_generic_object: Error in Accept");
      }
      cpy->FinalizeFromStack();
      x[0].obj = (void*)cpy;
    } catch (...) {
      ygglog_error("get_generic_object: C++ exception thrown.");
      out = GENERIC_ERROR_;
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
    generic_ref_t item;							\
    type out = defV;							\
    if (get_generic_ ## base ## _ref(x, (idxType)idx, &item) != GENERIC_SUCCESS_) { \
      return out;							\
    }									\
    out = generic_ref_get_ ## name(item, UNPACK_MACRO args);		\
    return out;								\
  }
#define NESTED_BASE_GET_NOARGS_(base, idx, idxType, name, type, defV)	\
  type generic_ ## base ## _get_ ## name(generic_t x, idxType idx) {	\
    generic_ref_t item;							\
    type out = defV;							\
    if (get_generic_ ## base ## _ref(x, (idxType)idx, &item) != GENERIC_SUCCESS_) { \
      return out;							\
    }									\
    out = generic_ref_get_ ## name(item);				\
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
    get_generic_array(x, index, &item);					\
    return item;							\
  }									\
  generic_t generic_map_get_ ## name(generic_t x, const char* key) {	\
    generic_t item;							\
    get_generic_object(x, key, &item);					\
    return item;							\
  }									\
  int generic_array_set_ ## name(generic_t x, const size_t index, generic_t item) { \
    return set_generic_array(x, index, item);				\
  }									\
  int generic_map_set_ ## name(generic_t x, const char* key, generic_t item) { \
    return set_generic_map(x, key, item);				\
  }

  
#define STD_JSON_BASE_(name, type, isMethod, outMethod, setMethod, defV) \
  type generic_ref_get_ ## name(generic_ref_t x) {			\
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
  type generic_get_ ## name(generic_t x) {				\
    generic_ref_t x_ref = init_generic_ref(x);				\
    return generic_ref_get_ ## name(x_ref);				\
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
  type generic_ref_get_ ## name(generic_ref_t x) {			\
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
  type generic_get_ ## name(generic_t x) {				\
    generic_ref_t x_ref = init_generic_ref(x);				\
    return generic_ref_get_ ## name(x_ref);				\
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
  size_t generic_ref_get_1darray_ ## name(generic_ref_t x, type** data) {	\
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
    data[0] = (type*)(d->Get1DArray<rjtype>(nelements, generic_ref_allocator(x))); \
    return (size_t)nelements;						\
  }									\
  size_t generic_get_1darray_ ## name(generic_t x, type** data) {	\
    generic_ref_t x_ref = init_generic_ref(x);				\
    return generic_ref_get_1darray_ ## name(x_ref, data);		\
  }									\
  size_t generic_ref_get_ndarray_ ## name(generic_ref_t x, type** data, size_t** shape) { \
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
    data[0] = (type*)(d->GetNDArray<rjtype>(rjshape, ndim, generic_ref_allocator(x))); \
    shape[0] = (size_t*)(generic_ref_allocator(x).Malloc(ndim * sizeof(size_t))); \
    for (rapidjson::SizeType i = 0; i < ndim; i++) {			\
      (*shape)[i] = rjshape[i];						\
    }									\
    generic_ref_allocator(x).Free(rjshape);				\
    return (size_t)ndim;						\
  }									\
  size_t generic_get_ndarray_ ## name(generic_t x, type** data, size_t** shape) { \
    generic_ref_t x_ref = init_generic_ref(x);				\
    return generic_ref_get_ndarray_ ## name(x_ref, data, shape);	\
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
  type generic_ref_get_ ## name(generic_ref_t x) {			\
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
  type generic_get_ ## name(generic_t x) {				\
    generic_ref_t x_ref = init_generic_ref(x);				\
    return generic_ref_get_ ## name(x_ref);				\
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
  STD_JSON_BASE_(string, const char*, d->IsString(), out = d->GetString(), d->SetString(value, STRLEN_RJ(value), generic_allocator(x)), 0);
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
#if defined(_WIN32) && !defined(_MSC_VER)
      printf("This function was called from outside the MSVC CRT and will be"
	     "skipped in order to avoid a segfault incurred due to the "
	     "Python C API's use of the MSVC CRT (particularly the FILE* "
	     "datatype). To fix this, please ensure "
	     "that the MSVC compiler (cl.exe) is available and cleanup any "
	     "remaining compilation products in order to trigger yggdrasil "
	     "to recompile your model during the next run.\n");
#else
      PyObject_Print(x.obj, stdout, 0);
#endif
#endif // YGGDRASIL_DISABLE_PYTHON_C_API
    } else {
      printf("NULL");
    }
  }

  int skip_va_elements(const dtype_t* dtype, va_list_t *ap, bool set) {
    if (dtype == NULL) {
      return 0;
    }
    if (dtype->schema == NULL) {
      return 0;
    }
    rapidjson::Document tmp;
    return (int)tmp.SkipVarArgs(((rapidjson::Value*)(dtype->schema))[0],
				((rapidjson::VarArgList*)(ap->va))[0],
				set);
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
      (*s)["type"].SetString(name, STRLEN_RJ(name), dtype_allocator(*dtype));
    } else {
      rapidjson::Value v(name, STRLEN_RJ(name), dtype_allocator(*dtype));
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

  dtype_t* create_dtype_from_schema(const char* schema,
				    const bool use_generic) {
    rapidjson::Document* obj = NULL;
    try {
      obj = new rapidjson::Document();
      obj->Parse(schema);
      if (obj->HasParseError()) {
	ygglog_throw_error("create_dtype_from_schema: Error parsing schema");
      }
      typename rapidjson::Value::MemberIterator it = obj->FindMember(rapidjson::Document::GetTypeString());
      if (it != obj->MemberEnd() &&
	  (it->value == rapidjson::Document::GetObjectString() ||
	   it->value == rapidjson::Document::GetSchemaString() ||
	   it->value == rapidjson::Document::GetPythonInstanceString() ||
	   it->value == rapidjson::Document::GetAnyString() ||
	   (it->value == rapidjson::Document::GetArrayString() &&
	    !obj->HasMember(rapidjson::Document::GetItemsString()))))
	return create_dtype(obj, true);
      return create_dtype(obj, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_from_schema: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_empty(const bool use_generic) {
    try {
      return create_dtype(NULL, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_empty: C++ exception thrown.");
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
      obj->String(type, STRLEN_RJ(type), true);
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
	  destroy_dtype(&(items[i]));
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
	  obj->Key(keys[i], STRLEN_RJ(keys[i]), true);
	  rapidjson::Document* iSchema = (rapidjson::Document*)(values[i]->schema);
	  if (!iSchema->Accept(*obj)) {
	    ygglog_throw_error("create_dtype_json_array: Error adding element %d.", i);
	  }
	  destroy_dtype(&(values[i]));
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

#define HEADER_GET_SET_METHOD_(type, method)				\
  int header_GetMeta ## method(comm_head_t head,			\
			       const char* name, type* x) {		\
    try {								\
      if (!head.head)							\
	return 0;							\
      Header* head_ = (Header*)(head.head);				\
      x[0] = head_->GetMeta ## method(name);				\
      return 1;								\
    } catch(...) {							\
      invalidate_header(&head);						\
      return 0;								\
    }									\
  }									\
  int header_SetMeta ## method(comm_head_t* head,			\
			       const char* name, type x) {		\
    if (!head)								\
      return 0;								\
    try {								\
      if (!head->head)							\
	return 0;							\
      Header* head_ = (Header*)(head->head);				\
      return static_cast<int>(head_->SetMeta ## method(name, x));	\
    } catch(...) {							\
      invalidate_header(head);						\
      return 0;								\
    }									\
  }
  HEADER_GET_SET_METHOD_(int, Int)
  HEADER_GET_SET_METHOD_(bool, Bool)
  HEADER_GET_SET_METHOD_(const char*, String)
#undef HEADER_GET_SET_METHOD_
  int header_SetMetaID(comm_head_t* head, const char* name,
		       const char** id) {
    if (!head)
      return 0;
    try {
      if (!head->head)
	return 0;
      Header* head_ = (Header*)(head->head);
      return static_cast<int>(head_->SetMetaID(name, id));
    } catch(...) {
      invalidate_header(head);
      return 0;
    }
  }
  
  int format_comm_header(comm_head_t* head, char **headbuf,
			 const char* buf, size_t buf_siz,
			 const size_t max_size, const int no_type) {
    try {
      Header* head_ = (Header*)(head->head);
      int ret = static_cast<int>(head_->format(buf, buf_siz,
					       max_size, (bool)no_type));
      headbuf[0] = head_->data_;
      ygglog_debug("format_comm_header: Message = '%100s...'", *headbuf);
      return ret;
    } catch(...) {
      ygglog_error("format_comm_header: C++ exception thrown.");
      return -1;
    }
  }

  comm_head_t init_header() {
    comm_head_t out;
    out.head = NULL;
    out.flags = NULL;
    out.size_data = NULL;
    out.size_curr = NULL;
    out.size_head = NULL;
    out.size_buff = NULL;
    out.metadata = NULL;
    try {
      Header* head = new Header();
      out.head = (void*)head;
      out.flags = &(head->flags);
      out.size_data = &(head->size_data);
      out.size_curr = &(head->size_curr);
      out.size_head = &(head->size_head);
      out.size_buff = &(head->size_buff);
      out.metadata = &(head->metadata);
    } catch(...) {
      ygglog_error("create_send_header: C++ exception thrown.");
      invalidate_header(&out);
    }
    return out;
  }

  comm_head_t create_send_header(dtype_t *datatype) {
				 
    comm_head_t out = init_header();
    if (header_is_valid(out)) {
      try {
	Header* head = (Header*)(out.head);
	rapidjson::Document* metadata = (rapidjson::Document*)(datatype->metadata);
	rapidjson::Value* schema = (rapidjson::Value*)(datatype->schema);
	head->for_send(metadata, schema);
      } catch(...) {
	ygglog_error("create_send_header: C++ exception thrown.");
	invalidate_header(&out);
      }
    }
    return out;
  }

  comm_head_t create_recv_header(char** data, const size_t len,
				 size_t msg_len, int allow_realloc,
				 int temp) {
    comm_head_t out = init_header();
    if (header_is_valid(out)) {
      try {
	Header* head = (Header*)(out.head);
	head->for_recv(data, len, msg_len,
		       (bool)allow_realloc, (bool)temp);
      } catch(...) {
	ygglog_error("create_recv_header: C++ exception thrown.");
	invalidate_header(&out);
      }
    }
    return out;
  }

  int destroy_header(comm_head_t* x) {
    try {
      if (x->head) {
	Header* head = (Header*)(x->head);
	x->head = NULL;
	x->flags = NULL;
	x->size_data = NULL;
	x->size_curr = NULL;
	x->size_head = NULL;
	x->size_buff = NULL;
	x->metadata = NULL;
	delete head;
      }
    } catch(...) {
      ygglog_error("destroy_header: C++ exception thrown.");
      return -1;
    }
    return 0;
  }

  void invalidate_header(comm_head_t* x) {
    if (!x->head)
      return;
    Header* head_ = (Header*)(x->head);
    head_->flags &= ~HEAD_FLAG_VALID;
  }
  int header_is_valid(const comm_head_t head) {
    if (!head.head)
      return 0;
    Header* head_ = (Header*)(head.head);
    return (head_->flags & HEAD_FLAG_VALID);
  }
  int header_is_multipart(const comm_head_t head) {
    if (!head.head)
      return 0;
    Header* head_ = (Header*)(head.head);
    return (head_->flags & HEAD_FLAG_MULTIPART);
  }

  void* header_schema(comm_head_t head) {
    if (!head.head)
      return NULL;
    Header* head_ = (Header*)(head.head);
    return (void*)(head_->schema);
  }

  int finalize_header_recv(comm_head_t head, dtype_t* dtype) {
    try {
      Header* head_ = (Header*)(head.head);
      head_->finalize_recv();
      return update_dtype(dtype, header_schema(head));
    } catch(...) {
      ygglog_error("parse_type_in_data: C++ exception thrown.");
      return -1;
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
      if (!((rapidjson::VarArgList*)(ap.va))->get(gen_arg)) {
	ygglog_throw_error("update_dtype_from_generic_ap: Error getting generic argument.");
	return -1;
      }
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

  int deserialize_dtype(const dtype_t *dtype, const char *buf,
			const size_t buf_siz, va_list_t ap) {
    try {
      rapidjson::VarArgList* va = (rapidjson::VarArgList*)(ap.va);
      if (dtype->schema == NULL) {
	ygglog_throw_error("deserialize_dtype: Empty schema.");
	return -1;
      }
      rapidjson::Value* schema = (rapidjson::Value*)(dtype->schema);
      return deserialize_args(buf, buf_siz, *schema, *va);
    } catch (...) {
      ygglog_error("deserialize_dtype: C++ exception thrown.");
      return -1;
    }
  }

  int serialize_dtype(const dtype_t *dtype, char **buf, size_t *buf_siz,
		      const int allow_realloc, va_list_t ap) {
    try {
      rapidjson::VarArgList* va = (rapidjson::VarArgList*)(ap.va);
      if (dtype->schema == NULL) {
	ygglog_throw_error("deserialize_dtype: Empty schema.");
	return -1;
      }
      rapidjson::Value* schema = (rapidjson::Value*)(dtype->schema);
      return serialize_args(buf, buf_siz, *schema, *va);
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

  int nelements_obj(obj_t p, const char* name) {
    if (p.obj == NULL) {
      ygglog_error("nelements_obj: ObjWavefront object is NULL.");
      return -1;
    }
    try {
      rapidjson::ObjWavefront* obj = (rapidjson::ObjWavefront*)(p.obj);
      size_t N = obj->count_elements(std::string(name));
      return static_cast<int>(N);
    } catch (...) {
      ygglog_error("nelements_obj: Error getting number of '%s' elements", name);
      return -1;
    }
  }

  // Ply wrapped methods
  ply_t init_ply() {
    ply_t x;
    x.obj = NULL;
    // x.nvert = 0;
    // x.nedge = 0;
    // x.nface = 0;
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
      // SET_COUNTS_(vertex, x->nvert)
      // SET_COUNTS_(edge, x->nedge)
      // SET_COUNTS_(face, x->nface)
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

  int nelements_ply(ply_t p, const char* name) {
    if (p.obj == NULL) {
      ygglog_error("nelements_ply: Ply object is NULL.");
      return -1;
    }
    try {
      rapidjson::Ply* ply = (rapidjson::Ply*)(p.obj);
      size_t N = ply->count_elements(std::string(name));
      return static_cast<int>(N);
    } catch (...) {
      ygglog_error("nelements_ply: Error getting number of '%s' elements", name);
      return -1;
    }
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
  
  va_list_t init_va_list(size_t *nargs, int allow_realloc,
			 int for_c) {
    va_list_t out;
    rapidjson::VarArgList* out_va = new rapidjson::VarArgList(nargs, allow_realloc, for_c);
    out.va = (void*)out_va;
    return out;
  }

  va_list_t init_va_ptrs(const size_t nptrs, void** ptrs, int allow_realloc,
			 int for_fortran) {
    va_list_t out;
    rapidjson::VarArgList* va = new rapidjson::VarArgList(nptrs, ptrs, allow_realloc, for_fortran);
    out.va = (void*)va;
    return out;
  }
  
  va_list* get_va_list(va_list_t ap) {
    rapidjson::VarArgList* va = (rapidjson::VarArgList*)(ap.va);
    if (!va)
      return NULL;
    return &(va->va);
  }
  
  void end_va_list(va_list_t *ap) {
    if (!ap)
      return;
    rapidjson::VarArgList* va = (rapidjson::VarArgList*)(ap->va);
    if (va) {
      size_t nargs = va->get_nargs();
      if (nargs != 0)
	ygglog_error("%d arguments unused", (int)nargs);
      delete va;
      ap->va = NULL;
    }
  }
  void clear_va_list(va_list_t *ap) {
    rapidjson::VarArgList* va = (rapidjson::VarArgList*)(ap->va);
    if (va) {
      va->clear();
    }
  }
  size_t size_va_list(va_list_t va) {
    if (!va.va) {
      ygglog_error("size_va_list: Argument list is NULL");
      return 0;
    }
    return ((rapidjson::VarArgList*)(va.va))->get_nargs();
  }
  
  void set_va_list_size(va_list_t va, size_t* nargs) {
    if (!va.va) {
      ygglog_error("set_va_list_size: Arugment list is NULL");
      return;
    }
    ((rapidjson::VarArgList*)(va.va))->nargs = nargs;
  }

  va_list_t copy_va_list(va_list_t ap) {
    va_list_t out;
    if (ap.va) {
      rapidjson::VarArgList* va = new rapidjson::VarArgList(((rapidjson::VarArgList*)(ap.va))[0]);
      out.va = (void*)va;
    } else {
      ygglog_error("copy_va_list: Source argument list is NULL");
      out.va = NULL;
    }
    return out;
  }

  void va_list_t_skip(va_list_t *ap, const size_t nbytes) {
    if (!(ap && ap->va)) {
      ygglog_error("va_list_t_skip: Argument list is NULL");
      return;
    }
    ((rapidjson::VarArgList*)(ap->va))->skip_nbytes(nbytes);
  }
  
  
}

#undef STRLEN_RJ

// Local Variables:
// mode: c++
// End:
