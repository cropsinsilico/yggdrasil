#include "../tools.h"
#include "MetaschemaType.h"
#include "DirectMetaschemaType.h"
#include "ScalarMetaschemaType.h"
#include "JSONArrayMetaschemaType.h"
#include "JSONObjectMetaschemaType.h"
#include "PlyMetaschemaType.h"
#include "ObjMetaschemaType.h"
#include "AsciiTableMetaschemaType.h"
#include "PyObjMetaschemaType.h"
#include "PyInstMetaschemaType.h"
#include "SchemaMetaschemaType.h"
#include "AnyMetaschemaType.h"
#include "datatypes.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"


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
MetaschemaType* type_from_doc(const rapidjson::Value &type_doc,
			      const bool use_generic=true,
			      const rapidjson::Value *header_doc=NULL) {
  if (!(type_doc.IsObject()))
    ygglog_throw_error("type_from_doc: Parsed document is not an object.");
  if (!(type_doc.HasMember("type")))
    ygglog_throw_error("type_from_doc: Parsed header dosn't contain a type.");
  if (!(type_doc["type"].IsString()))
    ygglog_throw_error("type_from_doc: Type in parsed header is not a string.");
  const char *type = type_doc["type"].GetString();
  std::map<const char*, int, strcomp> type_map = get_type_map();
  std::map<const char*, int, strcomp>::iterator it = type_map.find(type);
  if (it != type_map.end()) {
    switch (it->second) {
      // Standard types
    case T_BOOLEAN:
    case T_INTEGER:
    case T_NULL:
    case T_NUMBER:
    case T_STRING:
      return new MetaschemaType(type_doc, use_generic);
      // Enhanced types
    case T_ARRAY: {
      char format_str[1001] = "";
      if (header_doc != NULL) {
	if (header_doc->HasMember("format_str")) {
	  if (!((*header_doc)["format_str"].IsString()))
	    ygglog_throw_error("type_from_doc: JSONArrayMetaschemaType: format_str must be a string.");
	  strncpy(format_str, (*header_doc)["format_str"].GetString(), 1000);
	}
      }
      return new JSONArrayMetaschemaType(type_doc, format_str, use_generic);
    }
    case T_OBJECT:
      return new JSONObjectMetaschemaType(type_doc, use_generic);
      // Non-standard types
    case T_DIRECT:
      return new DirectMetaschemaType(type_doc, use_generic);
    case T_1DARRAY:
      return new OneDArrayMetaschemaType(type_doc, use_generic);
    case T_NDARRAY:
      return new NDArrayMetaschemaType(type_doc, use_generic);
    case T_SCALAR:
    case T_FLOAT:
    case T_UINT:
    case T_INT:
    case T_COMPLEX:
    case T_BYTES:
    case T_UNICODE:
      return new ScalarMetaschemaType(type_doc, use_generic);
    case T_PLY:
      return new PlyMetaschemaType(type_doc, use_generic);
    case T_OBJ:
      return new ObjMetaschemaType(type_doc, use_generic);
    case T_CLASS:
    case T_FUNCTION:
      return new PyObjMetaschemaType(type_doc, use_generic);
    case T_INSTANCE:
      return new PyInstMetaschemaType(type_doc, use_generic);
    case T_SCHEMA:
      return new SchemaMetaschemaType(type_doc, use_generic);
    case T_ANY:
      return new AnyMetaschemaType(type_doc, use_generic);
    }
  }
  ygglog_throw_error("Could not find class from doc for type '%s'.", type);
  return NULL;
};


MetaschemaType* type_from_header_doc(const rapidjson::Value &header_doc,
				 const bool use_generic=true) {
  if (!(header_doc.IsObject()))
    ygglog_throw_error("type_from_header_doc: Parsed document is not an object.");
  if (!(header_doc.HasMember("datatype")))
    ygglog_throw_error("type_from_header_doc: Parsed header dosn't contain a 'datatype' entry.");
  if (!(header_doc["datatype"].IsObject()))
    ygglog_throw_error("type_from_header_doc: Parsed datatype is not an object.");
  return type_from_doc(header_doc["datatype"], use_generic, &header_doc);
};


MetaschemaType* type_from_pyobj(PyObject* pyobj,
				const bool use_generic=true) {
  char type[100] = "";
  get_item_python_dict_c(pyobj, "type", type,
			 "type_from_pyobj: type: ",
			 T_STRING, 100);
  std::map<const char*, int, strcomp> type_map = get_type_map();
  std::map<const char*, int, strcomp>::iterator it = type_map.find(type);
  if (it != type_map.end()) {
    switch (it->second) {
      // Standard types
    case T_BOOLEAN:
    case T_INTEGER:
    case T_NULL:
    case T_NUMBER:
    case T_STRING:
      return new MetaschemaType(pyobj, use_generic);
      // Enhanced types
    case T_ARRAY:
      return new JSONArrayMetaschemaType(pyobj, use_generic);
    case T_OBJECT:
      return new JSONObjectMetaschemaType(pyobj, use_generic);
      // Non-standard types
    case T_DIRECT:
      return new DirectMetaschemaType(pyobj, use_generic);
    case T_1DARRAY:
      return new OneDArrayMetaschemaType(pyobj, use_generic);
    case T_NDARRAY:
      return new NDArrayMetaschemaType(pyobj, use_generic);
    case T_SCALAR:
    case T_FLOAT:
    case T_UINT:
    case T_INT:
    case T_COMPLEX:
    case T_BYTES:
    case T_UNICODE:
      return new ScalarMetaschemaType(pyobj, use_generic);
    case T_PLY:
      return new PlyMetaschemaType(pyobj, use_generic);
    case T_OBJ:
      return new ObjMetaschemaType(pyobj, use_generic);
    case T_CLASS:
    case T_FUNCTION:
      return new PyObjMetaschemaType(pyobj, use_generic);
    case T_INSTANCE:
      return new PyInstMetaschemaType(pyobj, use_generic);
    case T_SCHEMA:
      return new SchemaMetaschemaType(pyobj, use_generic);
    case T_ANY:
      return new AnyMetaschemaType(pyobj, use_generic);
    }
  }
  ygglog_throw_error("type_from_pyobj: Could not find class from doc for type '%s'.", type);
  return NULL;
};


bool update_header_from_doc(comm_head_t &head, rapidjson::Value &head_doc) {
  // Type
  if (!(head_doc.IsObject())) {
    ygglog_error("update_header_from_doc: head document must be an object.");
    return false;
  }
  // Size
  if (!(head_doc.HasMember("size"))) {
    ygglog_error("update_header_from_doc: No size information in the header.");
    return false;
  }
  if (!(head_doc["size"].IsInt())) {
    ygglog_error("update_header_from_doc: Size is not integer.");
    return false;
  }
  head.size = (size_t)(head_doc["size"].GetInt());
  if (head.bodysiz < head.size) {
    head.flags = head.flags | HEAD_FLAG_MULTIPART;
  } else {
    head.flags = head.flags & ~HEAD_FLAG_MULTIPART;
  }
  // Flag specifying that type is in data
  if (head_doc.HasMember("type_in_data")) {
    if (!(head_doc["type_in_data"].IsBool())) {
      ygglog_error("update_header_from_doc: type_in_data is not boolean.");
      return false;
    }
    if (head_doc["type_in_data"].GetBool()) {
      head.flags = head.flags | HEAD_TYPE_IN_DATA;
    } else {
      head.flags = head.flags & ~HEAD_TYPE_IN_DATA;
    }
  }
  // String fields
  const char **n;
  const char *string_fields[] = {"address", "id", "request_id", "response_address",
				 "zmq_reply", "zmq_reply_worker",
				 "model", ""};
  n = string_fields;
  while (strcmp(*n, "") != 0) {
    if (head_doc.HasMember(*n)) {
      if (!(head_doc[*n].IsString())) {
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
      const char *str = head_doc[*n].GetString();
      size_t len = head_doc[*n].GetStringLength();
      if (len > target_size) {
	ygglog_error("update_header_from_doc: Size of value for key '%s' (%d) exceeds size of target buffer (%d).",
		     *n, len, target_size);
	return false;
      }
      strncpy(target, str, target_size);
    }
    n++;
  }
  
  // Return
  return true;
};

JSONArrayMetaschemaType* create_dtype_format_class(const char *format_str,
						   const int as_array = 0,
						   const bool use_generic=false) {
  MetaschemaTypeVector items;
  JSONArrayMetaschemaType* out = new JSONArrayMetaschemaType(items, format_str, use_generic);
  // Loop over string
  int mres;
  size_t sind, eind, beg = 0, end;
  char ifmt[FMT_LEN];
  char re_fmt[FMT_LEN];
  char re_fmt_eof[FMT_LEN];
  sprintf(re_fmt, "%%[^%s%s ]+[%s%s ]", "\t", "\n", "\t", "\n");
  sprintf(re_fmt_eof, "%%[^%s%s ]+", "\t", "\n");
  size_t iprecision = 0;
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
      strncpy(isubtype, "bytes", FMT_LEN); // or unicode
      mres = regex_replace_sub(ifmt, FMT_LEN,
			       "%(\\.)?([[:digit:]]*)s(.*)", "$2", 0);
      iprecision = 8 * atoi(ifmt);
      // Complex
#ifdef _WIN32
    } else if (find_match("(%.*[fFeEgG]){2}j", ifmt, &sind, &eind)) {
#else
    } else if (find_match("(\%.*[fFeEgG]){2}j", ifmt, &sind, &eind)) {
#endif
      strncpy(isubtype, "complex", FMT_LEN);
      iprecision = 8 * 2 * sizeof(double);
    }
    // Floats
    else if (find_match("%.*[fFeEgG]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "float", FMT_LEN);
      iprecision = 8 * sizeof(double);
    }
    // Integers
    else if (find_match("%.*hh[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = 8 * sizeof(char);
    } else if (find_match("%.*h[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = 8 * sizeof(short);
    } else if (find_match("%.*ll[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = 8 * sizeof(long long);
    } else if (find_match("%.*l64[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = 8 * sizeof(long long);
    } else if (find_match("%.*l[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = 8 * sizeof(long);
    } else if (find_match("%.*[id]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "int", FMT_LEN);
      iprecision = 8 * sizeof(int);
    }
    // Unsigned integers
    else if (find_match("%.*hh[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = 8 * sizeof(unsigned char);
    } else if (find_match("%.*h[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = 8 * sizeof(unsigned short);
    } else if (find_match("%.*ll[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = 8 * sizeof(unsigned long long);
    } else if (find_match("%.*l64[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = 8 * sizeof(unsigned long long);
    } else if (find_match("%.*l[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = 8 * sizeof(unsigned long);
    } else if (find_match("%.*[uoxX]", ifmt, &sind, &eind)) {
      strncpy(isubtype, "uint", FMT_LEN);
      iprecision = 8 * sizeof(unsigned int);
    } else {
      ygglog_throw_error("create_dtype_format_class: Could not parse format string: %s", ifmt);
    }
    ygglog_debug("isubtype = %s, iprecision = %lu, ifmt = %s",
		 isubtype, iprecision, ifmt);
    if (as_array == 1) {
      items.push_back(new OneDArrayMetaschemaType(isubtype, iprecision, 0, "", out->use_generic()));
    } else {
      items.push_back(new ScalarMetaschemaType(isubtype, iprecision, "", out->use_generic()));
    }
    beg = end;
  }
  out->update_items(items, true);
  for (size_t i = 0; i < items.size(); i++) {
    delete items[i];
    items[i] = NULL;
  }
  return out;
};


void init_dtype_class(dtype_t *dtype, MetaschemaType* type_class) {
  if (dtype == NULL) {
    ygglog_throw_error("init_dtype_class: data type structure is NULL.");
  } else if (dtype->obj != NULL) {
    ygglog_throw_error("init_dtype_class: Data type class already set.");
  } else if (strlen(dtype->type) != 0) {
    ygglog_throw_error("init_dtype_class: Data type string already set.");
  }
  dtype->obj = type_class;
  dtype->use_generic = type_class->use_generic();
  strncpy(dtype->type, type_class->type(), COMMBUFFSIZ);
};


int destroy_dtype_class_safe(MetaschemaType *type_class) {
  if (type_class != NULL) {
    try {
      delete type_class;
    } catch (...) {
      ygglog_error("destroy_dtype_class_safe: C++ exception thrown.");
      return -1;
    }
  }
  return 0;
};


dtype_t* create_dtype(MetaschemaType* type_class=NULL,
		      const bool use_generic=false) {
  dtype_t* out = NULL;
  out = (dtype_t*)malloc(sizeof(dtype_t));
  if (out == NULL) {
    ygglog_throw_error("create_dtype: Failed to malloc for datatype.");
  }
  out->type[0] = '\0';
  out->use_generic = use_generic;
  out->obj = NULL;
  if (type_class != NULL) {
    try {
      init_dtype_class(out, type_class);
    } catch (...) {
      free(out);
      out = NULL;
      ygglog_throw_error("create_dtype: Failed to initialized data type structure with class information.");
    }
  }
  return out;
};


MetaschemaType* dtype2class(const dtype_t* dtype) {
  if (dtype == NULL) {
    ygglog_throw_error("dtype2class: Pointer to data structure is NULL.");
  } else if (dtype->obj == NULL) {
    ygglog_throw_error("dtype2class: C++ data type structure is NULL.");
  }
  std::map<const char*, int, strcomp> type_map = get_type_map();
  std::map<const char*, int, strcomp>::iterator it = type_map.find(dtype->type);
  if (it != type_map.end()) {
    switch (it->second) {
    case T_BOOLEAN:
    case T_INTEGER:
    case T_NULL:
    case T_NUMBER:
    case T_STRING:
      return static_cast<MetaschemaType*>(dtype->obj);
    case T_ARRAY:
      return static_cast<JSONArrayMetaschemaType*>(dtype->obj);
    case T_OBJECT:
      return static_cast<JSONObjectMetaschemaType*>(dtype->obj);
    case T_DIRECT:
      return static_cast<DirectMetaschemaType*>(dtype->obj);
    case T_1DARRAY:
      return static_cast<OneDArrayMetaschemaType*>(dtype->obj);
    case T_NDARRAY:
      return static_cast<NDArrayMetaschemaType*>(dtype->obj);
    case T_SCALAR:
    case T_FLOAT:
    case T_UINT:
    case T_INT:
    case T_COMPLEX:
    case T_BYTES:
    case T_UNICODE:
      return static_cast<ScalarMetaschemaType*>(dtype->obj);
    case T_PLY:
      return static_cast<PlyMetaschemaType*>(dtype->obj);
    case T_OBJ:
      return static_cast<ObjMetaschemaType*>(dtype->obj);
    case T_ASCII_TABLE:
      return static_cast<AsciiTableMetaschemaType*>(dtype->obj);
    case T_CLASS:
    case T_FUNCTION:
      return static_cast<PyObjMetaschemaType*>(dtype->obj);
    case T_INSTANCE:
      return static_cast<PyInstMetaschemaType*>(dtype->obj);
    case T_SCHEMA:
      return static_cast<SchemaMetaschemaType*>(dtype->obj);
    case T_ANY:
      return static_cast<AnyMetaschemaType*>(dtype->obj);
    }
  } else {
    ygglog_throw_error("dtype2class: No handler for type '%s'.", dtype->type);
  }
  return NULL;
};


rapidjson::StringBuffer format_comm_header_json(const comm_head_t head,
						const int no_type,
						const bool type_only=false) {
  rapidjson::StringBuffer head_buf;
  rapidjson::Writer<rapidjson::StringBuffer> head_writer(head_buf);
  head_writer.StartObject();
  // Type
  if ((!(head.flags & HEAD_TYPE_IN_DATA)) && (!(no_type))) {
    if (head.dtype != NULL) {
      head_writer.Key("datatype");
      head_writer.StartObject();
      MetaschemaType* type = dtype2class(head.dtype);
      if (!(type->encode_type_prop(&head_writer))) {
	ygglog_throw_error("format_comm_header_json: Error encoding type.");
      }
      head_writer.EndObject();
      if (strcmp(type->type(), "array") == 0) {
	JSONArrayMetaschemaType* array_type = static_cast<JSONArrayMetaschemaType*>(type);
	size_t format_str_len = strlen(array_type->format_str());
	if (format_str_len > 0) {
	  head_writer.Key("format_str");
	  head_writer.String(array_type->format_str(),
			     (rapidjson::SizeType)format_str_len);
	}
      }
    }
  }
  if (type_only) {
    head_writer.EndObject();
    return head_buf;
  }
  // Generic things
  head_writer.Key("size");
  head_writer.Int((int)(head.size));
  if (head.flags & HEAD_TYPE_IN_DATA) {
    head_writer.Key("type_in_data");
    head_writer.Bool(true);
  }
  // Strings
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
  return head_buf;
};


// C exposed functions
extern "C" {

  void* type_from_doc_c(const void* type_doc, const bool use_generic=false) {
    MetaschemaType* out = NULL;
    try {
      const rapidjson::Value* type_doc_cpp = (const rapidjson::Value*)type_doc;
      out = type_from_doc(*type_doc_cpp, use_generic);
    } catch(...) {
      ygglog_error("type_from_doc_c: C++ exception thrown.");
      if (out != NULL) {
	delete out;
	out = NULL;
      }
    }
    return (void*)out;
  }

  void* type_from_pyobj_c(PyObject* pyobj, const bool use_generic=false) {
    MetaschemaType* out = NULL;
    try {
      out = type_from_pyobj(pyobj, use_generic);
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
    int out = 0;
    try {
      if (type_struct->obj == NULL) {
	return -1;
      }
      MetaschemaType* type = dtype2class(type_struct);
      const char* name = type->type();
      if (strcmp(name, "array") == 0) {
	JSONArrayMetaschemaType* array_type = static_cast<JSONArrayMetaschemaType*>(type);
	if ((array_type->all_arrays()) && (strlen(array_type->format_str()) > 0)) {
	  out = 1;
	}
      }
    } catch(...) {
      ygglog_error("is_dtype_format_array: C++ exception thrown.");
      out = -1;
    }
    return out;
  }

  generic_t init_generic() {
    generic_t out;
    out.prefix = prefix_char;
    out.obj = NULL;
    return out;
  }

  generic_t init_generic_array() {
    generic_t out = init_generic();
    JSONArrayMetaschemaType* type = new JSONArrayMetaschemaType(MetaschemaTypeVector(), "", true);
    YggGenericVector* value = new YggGenericVector();
    YggGeneric* x = new YggGeneric(type, (void*)value);
    out.obj = (void*)x;
    delete type;
    delete value;
    return out;
  }

  generic_t init_generic_map() {
    generic_t out = init_generic();
    JSONObjectMetaschemaType* type = new JSONObjectMetaschemaType(MetaschemaTypeMap(), true);
    YggGenericMap* value = new YggGenericMap();
    YggGeneric* x = new YggGeneric(type, (void*)value);
    out.obj = (void*)x;
    delete type;
    delete value;
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
  
  generic_t create_generic(dtype_t* type_struct, void* data, size_t nbytes) {
    generic_t out = init_generic();
    try {
      MetaschemaType* type = dtype2class(type_struct);
      YggGeneric* obj = new YggGeneric(type, data, nbytes);
      out.obj = (void*)obj;
    } catch(...) {
      ygglog_error("create_generic: C++ exception thrown.");
      destroy_generic(&out);
    }
    return out;
  }

  // generic_t create_generic_array(const size_t nitems,
  // 				 generic_t* items) {
  //   generic_t out = init_generic();
  //   try {
  //     size_t i;
  //     MetaschemaTypeVector *types = new MetaschemaTypeVector();
  //     YggGenericVector *data = new YggGenericVector();
  //     for (i = 0; i < nitems; i++) {
  // 	YggGeneric* iobj = (YggGeneric*)(items[i].obj);
  // 	MetaschemaType* itype = iobj->get_type();
  // 	data->push_back(iobj);
  // 	types->push_back(itype);
  //     }
  //     JSONArrayMetaschemaType *new_type = new JSONArrayMetaschemaType(types, "", true);
  //     YggGeneric* obj = new YggGeneric(new_type, (void*)data, new_type->nbytes);
  //   } catch (...) {
  //     ygglog_error("create_generic_array: C++ exception thrown.");
  //   }
  //   return out;
  // }

  int destroy_generic(generic_t* x) {
    int ret = 0;
    if (x != NULL) {
      if (is_generic_init(*x)) {
	x->prefix = ' ';
	if (x->obj != NULL) {
	  try {
	    YggGeneric* obj = (YggGeneric*)(x->obj);
	    delete obj;
	    x->obj = NULL;
	  } catch (...) {
	    ygglog_error("destroy_generic: C++ exception thrown in destructor for YggGeneric.");
	    ret = -1;
	  }
	}
      }
    }
    return ret;
  }

  generic_t copy_generic(generic_t src) {
    generic_t out = init_generic();
    try {
      if (!(is_generic_init(src))) {
	ygglog_throw_error("copy_generic: Source object not initialized.");
      }
      YggGeneric* src_obj = (YggGeneric*)(src.obj);
      if (src_obj == NULL) {
	ygglog_throw_error("copy_generic: Generic object class is NULL.");
      }
      out.obj = src_obj->copy();
    } catch(...) {
      ygglog_error("copy_generic: C++ exception thrown.");
      destroy_generic(&out);
    }
    return out;
  }

  void display_generic(generic_t x) {
    try {
      if (is_generic_init(x)) {
	YggGeneric* x_obj = (YggGeneric*)(x.obj);
	if (x_obj != NULL) {
	  x_obj->display();
	}
      }
    } catch (...) {
      ygglog_error("display_generic: C++ exception thrown.");
    }
  }

  generic_t get_generic_va(size_t nargs, va_list_t ap) {
    generic_t out;
    if (nargs != 1)
      return out;
    va_list_t ap_copy = copy_va_list(ap);
    if (ap.using_ptrs) {
      CSafe(out = ((generic_t*)get_va_list_ptr_cpp(&ap_copy))[0])
    } else {
      out = va_arg(ap_copy.va, generic_t);
    }
    return out;
  }

  generic_t* get_generic_va_ptr(size_t nargs, va_list_t ap) {
    if (nargs != 1)
      return NULL;
    generic_t *out;
    va_list_t ap_copy = copy_va_list(ap);
    if (ap.using_ptrs) {
      CSafe(out = (generic_t*)get_va_list_ptr_cpp(&ap_copy))
    } else {
      out = va_arg(ap_copy.va, generic_t*);
    }
    if ((out != NULL) || (is_generic_init(*out))) {
      return out;
    } else {
      return NULL;
    }
  }

  generic_t pop_generic_va(size_t* nargs, va_list_t* ap) {
    generic_t out;
    if ((*nargs) < 1) {
      ygglog_error("pop_generic_va: Not enough args (nargs = %lu).", *nargs);
      return out;
    }
    (*nargs)--;
    if (ap->using_ptrs) {
      CSafe(out = ((generic_t*)get_va_list_ptr_cpp(ap))[0])
    } else {
      out = va_arg(ap->va, generic_t);
    }
    return out;
  }

  generic_t* pop_generic_va_ptr(size_t* nargs, va_list_t* ap) {
    if ((*nargs) < 1) {
      ygglog_error("pop_generic_va_ptr: Not enough args (nargs = %lu).", *nargs);
      return NULL;
    }
    (*nargs)--;
    generic_t *out;
    if (ap->using_ptrs) {
      CSafe(out = (generic_t*)get_va_list_ptr_cpp(ap))
    } else {
      out = va_arg(ap->va, generic_t*);
    }
    if (out == NULL) {
      ygglog_error("pop_generic_va_ptr: Object is NULL.");
      return NULL;
    } else if (!(is_generic_init(*out))) {
      ygglog_error("pop_generic_va_ptr: Generic object not intialized.");
      return NULL;
    }
    return out;
  }

  int add_generic_array(generic_t arr, generic_t x) {
    int out = 0;
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("add_generic_array: Array is not a generic object.");
      }
      if (!(is_generic_init(x))) {
	ygglog_throw_error("add_generic_array: New element is not a generic object.");
      }
      YggGeneric* arr_obj = (YggGeneric*)(arr.obj);
      if (arr_obj == NULL) {
	ygglog_throw_error("add_generic_array: Array is NULL.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("add_generic_array: New element is NULL.");
      }
      arr_obj->add_array_element(x_obj);
    } catch (...) {
      ygglog_error("add_generic_array: C++ exception thrown.");
      out = 1;
    }
    return out;
  }

  int set_generic_array(generic_t arr, size_t i, generic_t x) {
    int out = 0;
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("set_generic_array: Array is not a generic object.");
      }
      if (!(is_generic_init(x))) {
	ygglog_throw_error("set_generic_array: New element is not a generic object.");
      }
      YggGeneric* arr_obj = (YggGeneric*)(arr.obj);
      if (arr_obj == NULL) {
	ygglog_throw_error("set_generic_array: Array is NULL.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("set_generic_array: New element is NULL.");
      }
      arr_obj->set_array_element(i, x_obj);
    } catch (...) {
      ygglog_error("set_generic_array: C++ exception thrown.");
      out = 1;
    }
    return out;
  }

  int get_generic_array(generic_t arr, size_t i, generic_t *x) {
    int out = 0;
    x[0] = init_generic();
    try {
      if (!(is_generic_init(arr))) {
  ygglog_throw_error("get_generic_array: Array is not a generic object.");
      }
      YggGeneric* arr_obj = (YggGeneric*)(arr.obj);
      if (arr_obj == NULL) {
  ygglog_throw_error("get_generic_array: Array is NULL.");
      }
      x[0].obj = (void*)(arr_obj->get_array_element(i));
    } catch (...) {
      ygglog_error("get_generic_array: C++ exception thrown.");
      out = 1;
    }
    return out;
  }

  int set_generic_object(generic_t arr, const char* k, generic_t x) {
    int out = 0;
    try {
      if (!(is_generic_init(arr))) {
  ygglog_throw_error("set_generic_object: Object is not a generic object.");
      }
      if (!(is_generic_init(x))) {
  ygglog_throw_error("set_generic_object: New element is not a generic object.");
      }
      YggGeneric* arr_obj = (YggGeneric*)(arr.obj);
      if (arr_obj == NULL) {
  ygglog_throw_error("set_generic_object: Object is NULL.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
  ygglog_throw_error("set_generic_object: New element is NULL.");
      }
      arr_obj->set_object_element(k, x_obj);
    } catch (...) {
      ygglog_error("set_generic_object: C++ exception thrown.");
      out = 1;
    }
    return out;
  }

  int get_generic_object(generic_t arr, const char* k, generic_t *x) {
    int out = 0;
    x[0] = init_generic();
    try {
      if (!(is_generic_init(arr))) {
	ygglog_throw_error("get_generic_object: Object is not a generic object.");
      }
      YggGeneric* arr_obj = (YggGeneric*)(arr.obj);
      if (arr_obj == NULL) {
	ygglog_throw_error("get_generic_object: Object is NULL.");
      }
      x[0].obj = (void*)(arr_obj->get_object_element(k));
    } catch (...) {
      ygglog_error("get_generic_object: C++ exception thrown.");
      out = 1;
    }
    return out;
  }

  // Generic array methods
  size_t generic_array_get_size(generic_t x) {
    size_t out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_size: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_get_size: Object is NULL.");
      }
      out = x_obj->get_data_array_size();
    } catch (...) {
      ygglog_error("generic_array_get_size: C++ exception thrown.");
    }
    return out;
  }

  void* generic_array_get_item(generic_t x, const size_t index,
			       const char *type) {
    void* out = NULL;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_item: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_get_item: Object is NULL.");
      }
      bool use_generic = x_obj->get_type()->use_generic();
      std::map<const char*, int, strcomp> type_map = get_type_map();
      std::map<const char*, int, strcomp>::iterator it = type_map.find(type);
      MetaschemaType* item_type = NULL;
      bool return_generic = false;
      if (it != type_map.end()) {
	switch (it->second) {
	case T_BOOLEAN:
	case T_INTEGER:
	case T_NULL:
	case T_NUMBER:
	case T_STRING: {
	  item_type = new MetaschemaType(type, use_generic);
	  break;
	}
	case T_ARRAY: {
	  return_generic = true;
	  use_generic = true;
	  MetaschemaTypeVector new_items = MetaschemaTypeVector();
	  char new_format_str[1000] = "";
	  const MetaschemaType* item_type0 = x_obj->get_type()->get_item_type(index);
	  if (item_type0->type_code() == T_ARRAY) {
	    const JSONArrayMetaschemaType* item_type0_cast = static_cast<const JSONArrayMetaschemaType*>(item_type0);
	    new_items = item_type0_cast->items();
	    strncpy(new_format_str, item_type0_cast->format_str(), 1000);
	  }
	  item_type = new JSONArrayMetaschemaType(new_items,
						  new_format_str,
						  use_generic);
	  break;
	}
	case T_OBJECT: {
	  return_generic = true;
	  use_generic = true;
	  MetaschemaTypeMap new_props = MetaschemaTypeMap();
	  const MetaschemaType* item_type0 = x_obj->get_type()->get_item_type(index);
	  if (item_type0->type_code() == T_OBJECT) {
	    const JSONObjectMetaschemaType* item_type0_cast = static_cast<const JSONObjectMetaschemaType*>(item_type0);
	    new_props = item_type0_cast->properties();
	  }
	  item_type = new JSONObjectMetaschemaType(new_props,
						   use_generic);
	  break;
	}
	case T_PLY: {
	  item_type = new PlyMetaschemaType(use_generic);
	  break;
	}
	case T_OBJ: {
	  item_type = new ObjMetaschemaType(use_generic);
	  break;
	}
	case T_CLASS:
	case T_FUNCTION: {
	  item_type = new PyObjMetaschemaType(type, use_generic);
	  break;
	}
	case T_SCHEMA: {
	  return_generic = true;
	  item_type = new SchemaMetaschemaType(use_generic);
	  break;
	}
	case T_ANY: {
	  return_generic = true;
	  item_type = new AnyMetaschemaType(use_generic);
	  break;
	}
	}
      }
      if (item_type == NULL) {
	ygglog_throw_error("generic_array_get_item: No handler for type '%s'.", type);
      }
      out = x_obj->get_data_array_item(index, item_type, return_generic);
      delete item_type;
    } catch (...) {
      ygglog_error("generic_array_get_item: C++ exception thrown.");
    }
    return out;
  }
  int generic_array_get_item_nbytes(generic_t x, const size_t index) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_item_nbytes: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_get_item_nbytes: Object is NULL.");
      }
      out = x_obj->get_nbytes_array_item(index);
    } catch (...) {
      ygglog_error("generic_array_get_item_nbytes: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  bool generic_array_get_bool(generic_t x, const size_t index) {
    return ((bool*)generic_array_get_item(x, index, "boolean"))[0];
  }
  int generic_array_get_integer(generic_t x, const size_t index) {
    return ((int*)generic_array_get_item(x, index, "integer"))[0];
  }
  void* generic_array_get_null(generic_t x, const size_t index) {
    return ((void**)generic_array_get_item(x, index, "null"))[0];
  }
  double generic_array_get_number(generic_t x, const size_t index) {
    return ((double*)generic_array_get_item(x, index, "number"))[0];
  }
  char* generic_array_get_string(generic_t x, const size_t index) {
    return ((char**)generic_array_get_item(x, index, "string"))[0];
  }
  generic_t generic_array_get_object(generic_t x, const size_t index) {
    YggGeneric* result = (YggGeneric*)generic_array_get_item(x, index, "object");
    generic_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  generic_t generic_array_get_array(generic_t x, const size_t index) {
    YggGeneric* result = (YggGeneric*)generic_array_get_item(x, index, "array");
    generic_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  ply_t generic_array_get_ply(generic_t x, const size_t index) {
    ply_t* old = (ply_t*)generic_array_get_item(x, index, "ply");
    ply_t out = copy_ply(*old);
    return out;
  }
  obj_t generic_array_get_obj(generic_t x, const size_t index) {
    obj_t* old = (obj_t*)generic_array_get_item(x, index, "obj");
    obj_t out = copy_obj(*old);
    return out;
  }
  python_t generic_array_get_python_class(generic_t x, const size_t index) {
    python_t* old = (python_t*)generic_array_get_item(x, index, "class");
    python_t out = copy_python(*old);
    return out;
  }
  python_t generic_array_get_python_function(generic_t x, const size_t index) {
    python_t* old = (python_t*)generic_array_get_item(x, index, "function");
    python_t out = copy_python(*old);
    return out;
  }
  schema_t generic_array_get_schema(generic_t x, const size_t index) {
    YggGeneric* result = (YggGeneric*)generic_array_get_item(x, index, "schema");
    schema_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  generic_t generic_array_get_any(generic_t x, const size_t index) {
    YggGeneric* result = (YggGeneric*)generic_array_get_item(x, index, "any");
    generic_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  
  void* generic_array_get_scalar(generic_t x, const size_t index,
				 const char *subtype,
				 const size_t precision) {
    void* out = NULL;
    char new_units[100] = "";
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_scalar: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_get_scalar: Object is NULL.");
      }
      const MetaschemaType* item_type0 = x_obj->get_type()->get_item_type(index);
      if (item_type0->type_code() == T_SCALAR) {
	const ScalarMetaschemaType* item_type0_scl = static_cast<const ScalarMetaschemaType*>(item_type0);
	strcpy(new_units, item_type0_scl->units());
      }
      ScalarMetaschemaType* item_type = new ScalarMetaschemaType(subtype, precision, new_units, x_obj->get_type()->use_generic());
      out = x_obj->get_data_array_item(index, item_type);
      delete item_type;
    } catch (...) {
      ygglog_error("generic_array_get_scalar: C++ exception thrown.");
    }
    return out;
  }
  int8_t generic_array_get_int8(generic_t x, const size_t index) {
    return ((int8_t*)generic_array_get_scalar(x, index, "int", 8*sizeof(int8_t)))[0];
  }
  int16_t generic_array_get_int16(generic_t x, const size_t index) {
    return ((int16_t*)generic_array_get_scalar(x, index, "int", 8*sizeof(int16_t)))[0];
  }
  int32_t generic_array_get_int32(generic_t x, const size_t index) {
    return ((int32_t*)generic_array_get_scalar(x, index, "int", 8*sizeof(int32_t)))[0];
  }
  int64_t generic_array_get_int64(generic_t x, const size_t index) {
    return ((int64_t*)generic_array_get_scalar(x, index, "int", 8*sizeof(int64_t)))[0];
  }
  uint8_t generic_array_get_uint8(generic_t x, const size_t index) {
    return ((uint8_t*)generic_array_get_scalar(x, index, "uint", 8*sizeof(uint8_t)))[0];
  }
  uint16_t generic_array_get_uint16(generic_t x, const size_t index) {
    return ((uint16_t*)generic_array_get_scalar(x, index, "uint", 8*sizeof(uint16_t)))[0];
  }
  uint32_t generic_array_get_uint32(generic_t x, const size_t index) {
    return ((uint32_t*)generic_array_get_scalar(x, index, "uint", 8*sizeof(uint32_t)))[0];
  }
  uint64_t generic_array_get_uint64(generic_t x, const size_t index) {
    return ((uint64_t*)generic_array_get_scalar(x, index, "uint", 8*sizeof(uint64_t)))[0];
  }
  float generic_array_get_float(generic_t x, const size_t index) {
    return ((float*)generic_array_get_scalar(x, index, "float", 8*sizeof(float)))[0];
  }
  double generic_array_get_double(generic_t x, const size_t index) {
    return ((double*)generic_array_get_scalar(x, index, "float", 8*sizeof(double)))[0];
  }
  long double generic_array_get_long_double(generic_t x, const size_t index) {
    return ((long double*)generic_array_get_scalar(x, index, "float", 8*sizeof(long double)))[0];
  }
  complex_float_t generic_array_get_complex_float(generic_t x, const size_t index) {
    return ((complex_float_t*)generic_array_get_scalar(x, index, "complex", 8*sizeof(complex_float_t)))[0];
  }
  complex_double_t generic_array_get_complex_double(generic_t x, const size_t index) {
    return ((complex_double_t*)generic_array_get_scalar(x, index, "complex", 8*sizeof(complex_double_t)))[0];
  }
  complex_long_double_t generic_array_get_complex_long_double(generic_t x, const size_t index) {
    return ((complex_long_double_t*)generic_array_get_scalar(x, index, "complex", 8*sizeof(complex_long_double_t)))[0];
  }
  char* generic_array_get_bytes(generic_t x, const size_t index) {
    return ((char**)generic_array_get_scalar(x, index, "bytes", 0))[0];
  }
  char* generic_array_get_unicode(generic_t x, const size_t index) {
    return ((char**)generic_array_get_scalar(x, index, "unicode", 0))[0];
  }
  
  size_t generic_array_get_1darray(generic_t x, const size_t index,
				   const char *subtype, const size_t precision,
				   void** data) {
    size_t out = 0;
    char new_units[100] = "";
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_1darray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_get_1darray: Object is NULL.");
      }
      size_t new_length = 0;
      const MetaschemaType* item_type0 = x_obj->get_type()->get_item_type(index);
      if (item_type0->type_code() == T_1DARRAY) {
	const OneDArrayMetaschemaType* item_type0_arr = static_cast<const OneDArrayMetaschemaType*>(item_type0);
	strcpy(new_units, item_type0_arr->units());
	new_length = item_type0_arr->length();
      }
      OneDArrayMetaschemaType* item_type = new OneDArrayMetaschemaType(subtype, precision, new_length, new_units, x_obj->get_type()->use_generic());
      size_t nbytes = item_type->nbytes();
      void* new_data = x_obj->get_data_array_item(index, item_type);
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_array_get_1darray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
      out = new_length;
      delete item_type;
    } catch (...) {
      ygglog_error("generic_array_get_1darray: C++ exception thrown.");
    }
    return out;
  }
  size_t generic_array_get_1darray_int8(generic_t x, const size_t index, int8_t** data) {
    return generic_array_get_1darray(x, index, "int", 8*sizeof(int8_t), (void**)data);
  }
  size_t generic_array_get_1darray_int16(generic_t x, const size_t index, int16_t** data) {
    return generic_array_get_1darray(x, index, "int", 8*sizeof(int16_t), (void**)data);
  }
  size_t generic_array_get_1darray_int32(generic_t x, const size_t index, int32_t** data) {
    return generic_array_get_1darray(x, index, "int", 8*sizeof(int32_t), (void**)data);
  }
  size_t generic_array_get_1darray_int64(generic_t x, const size_t index, int64_t** data) {
    return generic_array_get_1darray(x, index, "int", 8*sizeof(int64_t), (void**)data);
  }
  size_t generic_array_get_1darray_uint8(generic_t x, const size_t index, uint8_t** data) {
    return generic_array_get_1darray(x, index, "uint", 8*sizeof(uint8_t), (void**)data);
  }
  size_t generic_array_get_1darray_uint16(generic_t x, const size_t index, uint16_t** data) {
    return generic_array_get_1darray(x, index, "uint", 8*sizeof(uint16_t), (void**)data);
  }
  size_t generic_array_get_1darray_uint32(generic_t x, const size_t index, uint32_t** data) {
    return generic_array_get_1darray(x, index, "uint", 8*sizeof(uint32_t), (void**)data);
  }
  size_t generic_array_get_1darray_uint64(generic_t x, const size_t index, uint64_t** data) {
    return generic_array_get_1darray(x, index, "uint", 8*sizeof(uint64_t), (void**)data);
  }
  size_t generic_array_get_1darray_float(generic_t x, const size_t index,
					 float** data) {
    return generic_array_get_1darray(x, index, "float", 8*sizeof(float), (void**)data);
  }
  size_t generic_array_get_1darray_double(generic_t x, const size_t index,
					  double** data) {
    return generic_array_get_1darray(x, index, "float", 8*sizeof(double), (void**)data);
  }
  size_t generic_array_get_1darray_long_double(generic_t x, const size_t index,
					       long double** data) {
    return generic_array_get_1darray(x, index, "float", 8*sizeof(long double), (void**)data);
  }
  size_t generic_array_get_1darray_complex_float(generic_t x, const size_t index, complex_float_t** data) {
    return generic_array_get_1darray(x, index, "complex", 8*sizeof(complex_float_t), (void**)data);
  }
  size_t generic_array_get_1darray_complex_double(generic_t x, const size_t index, complex_double_t** data) {
    return generic_array_get_1darray(x, index, "complex", 8*sizeof(complex_double_t), (void**)data);
  }
  size_t generic_array_get_1darray_complex_long_double(generic_t x, const size_t index, complex_long_double_t** data) {
    return generic_array_get_1darray(x, index, "complex", 8*sizeof(complex_long_double_t), (void**)data);
  }
  size_t generic_array_get_1darray_bytes(generic_t x, const size_t index,  char** data) {
    return generic_array_get_1darray(x, index, "bytes", 0, (void**)data);
  }
  size_t generic_array_get_1darray_unicode(generic_t x, const size_t index,  char** data) {
    return generic_array_get_1darray(x, index, "unicode", 0, (void**)data);
  }

  size_t generic_array_get_ndarray(generic_t x, const size_t index,
				   const char *subtype, const size_t precision,
				   void** data, size_t** shape) {
    size_t out = 0;
    size_t i;
    char new_units[100] = "";
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_get_ndarray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_get_ndarray: Object is NULL.");
      }
      std::vector<size_t> new_shape;
      const MetaschemaType* item_type0 = x_obj->get_type()->get_item_type(index);
      if (item_type0->type_code() == T_NDARRAY) {
	const NDArrayMetaschemaType* item_type0_arr = static_cast<const NDArrayMetaschemaType*>(item_type0);
	strcpy(new_units, item_type0_arr->units());
	new_shape = item_type0_arr->shape();
      }
      NDArrayMetaschemaType* item_type = new NDArrayMetaschemaType(subtype, precision, new_shape, new_units, x_obj->get_type()->use_generic());
      size_t nbytes = item_type->nbytes();
      void* new_data = x_obj->get_data_array_item(index, item_type);
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_array_get_ndarray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
      shape[0] = (size_t*)realloc(shape[0], new_shape.size());
      if (shape[0] == NULL) {
	ygglog_throw_error("generic_array_get_ndarray: Failed to realloc shape.");
      }
      for (i = 0; i < new_shape.size(); i++) {
	shape[0][i] = new_shape[i];
      }
      out = new_shape.size();
      delete item_type;
    } catch (...) {
      ygglog_error("generic_array_get_ndarray: C++ exception thrown.");
    }
    return out;
  }
  size_t generic_array_get_ndarray_int8(generic_t x, const size_t index, int8_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "int", 8*sizeof(int8_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_int16(generic_t x, const size_t index, int16_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "int", 8*sizeof(int16_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_int32(generic_t x, const size_t index, int32_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "int", 8*sizeof(int32_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_int64(generic_t x, const size_t index, int64_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "int", 8*sizeof(int64_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_uint8(generic_t x, const size_t index, uint8_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "uint", 8*sizeof(uint8_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_uint16(generic_t x, const size_t index, uint16_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "uint", 8*sizeof(uint16_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_uint32(generic_t x, const size_t index, uint32_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "uint", 8*sizeof(uint32_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_uint64(generic_t x, const size_t index, uint64_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "uint", 8*sizeof(uint64_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_float(generic_t x, const size_t index,
				       float** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "float", 8*sizeof(float),
				   (void**)data, shape);
  }
  size_t generic_array_get_ndarray_double(generic_t x, const size_t index,
					double** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "float", 8*sizeof(double),
				   (void**)data, shape);
  }
  size_t generic_array_get_ndarray_long_double(generic_t x, const size_t index,
					     long double** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "float", 8*sizeof(long double),
				   (void**)data, shape);
  }
  size_t generic_array_get_ndarray_complex_float(generic_t x, const size_t index, complex_float_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "complex", 8*sizeof(complex_float_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_complex_double(generic_t x, const size_t index, complex_double_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "complex", 8*sizeof(complex_double_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_complex_long_double(generic_t x, const size_t index, complex_long_double_t** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "complex", 8*sizeof(complex_long_double_t), (void**)data, shape);
  }
  size_t generic_array_get_ndarray_bytes(generic_t x, const size_t index, char** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "bytes", 0, (void**)data, shape);
  }
  size_t generic_array_get_ndarray_unicode(generic_t x, const size_t index, char** data, size_t** shape) {
    return generic_array_get_ndarray(x, index, "unicode", 0, (void**)data, shape);
  }
  
  // Generic map methods
  size_t generic_map_get_size(generic_t x) {
    size_t out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_size: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_size: Object is NULL.");
      }
      out = x_obj->get_data_map_size();
    } catch (...) {
      ygglog_error("generic_map_get_size: C++ exception thrown.");
    }
    return out;
  }
  int generic_map_has_key(generic_t x, char* key) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_keys: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_keys: Object is NULL.");
      }
      if (x_obj->has_data_map_key(key)) {
	out = 1;
      }
    } catch (...) {
      ygglog_error("generic_map_get_keys: C++ exception thrown.");
    }
    return out;
  }
  size_t generic_map_get_keys(generic_t x, char*** keys) {
    size_t out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_keys: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_keys: Object is NULL.");
      }
      out = x_obj->get_data_map_keys(keys);
    } catch (...) {
      ygglog_error("generic_map_get_keys: C++ exception thrown.");
    }
    return out;
  }

  void* generic_map_get_item(generic_t x, const char* key,
			     const char *type) {
    void* out = NULL;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_item: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_item: Object is NULL.");
      }
      bool use_generic = x_obj->get_type()->use_generic();
      std::map<const char*, int, strcomp> type_map = get_type_map();
      std::map<const char*, int, strcomp>::iterator it = type_map.find(type);
      MetaschemaType* item_type = NULL;
      bool return_generic = false;
      if (it != type_map.end()) {
	switch (it->second) {
	case T_BOOLEAN:
	case T_INTEGER:
	case T_NULL:
	case T_NUMBER:
	case T_STRING: {
	  item_type = new MetaschemaType(type, use_generic);
	  break;
	}
	case T_ARRAY: {
	  return_generic = true;
	  use_generic = true;
	  MetaschemaTypeVector new_items = MetaschemaTypeVector();
	  char new_format_str[1000] = "";
	  const MetaschemaType* item_type0 = x_obj->get_type()->get_property_type(key);
	  if (item_type0->type_code() == T_ARRAY) {
	    const JSONArrayMetaschemaType* item_type0_cast = static_cast<const JSONArrayMetaschemaType*>(item_type0);
	    new_items = item_type0_cast->items();
	    strncpy(new_format_str, item_type0_cast->format_str(), 1000);
	  }
	  item_type = new JSONArrayMetaschemaType(new_items,
						  new_format_str,
						  use_generic);
	  break;
	}
	case T_OBJECT: {
	  return_generic = true;
	  use_generic = true;
	  MetaschemaTypeMap new_props = MetaschemaTypeMap();
	  const MetaschemaType* item_type0 = x_obj->get_type()->get_property_type(key);
	  if (item_type0->type_code() == T_OBJECT) {
	    const JSONObjectMetaschemaType* item_type0_cast = static_cast<const JSONObjectMetaschemaType*>(item_type0);
	    new_props = item_type0_cast->properties();
	  }
	  item_type = new JSONObjectMetaschemaType(new_props,
						   use_generic);
	  break;
	}
	case T_PLY: {
	  item_type = new PlyMetaschemaType(use_generic);
	  break;
	}
	case T_OBJ: {
	  item_type = new ObjMetaschemaType(use_generic);
	  break;
	}
	case T_CLASS:
	case T_FUNCTION: {
	  item_type = new PyObjMetaschemaType(type, use_generic);
	  break;
	}
	case T_SCHEMA: {
	  return_generic = true;
	  item_type = new SchemaMetaschemaType(use_generic);
	  break;
	}
	case T_ANY: {
	  return_generic = true;
	  item_type = new AnyMetaschemaType(use_generic);
	  break;
	}
	}
      }
      if (item_type == NULL) {
	ygglog_throw_error("generic_map_get_item: No handler for type '%s'.", type);
      }
      out = x_obj->get_data_map_item(key, item_type, return_generic);
      delete item_type;
    } catch (...) {
      ygglog_error("generic_map_get_item: C++ exception thrown.");
    }
    return out;
  }
  int generic_map_get_item_nbytes(generic_t x, const char* key) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_item_nbytes: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_item_nbytes: Object is NULL.");
      }
      out = (int)(x_obj->get_nbytes_map_item(key));
    } catch (...) {
      ygglog_error("generic_map_get_item_nbytes: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  bool generic_map_get_bool(generic_t x, const char* key) {
    return ((bool*)generic_map_get_item(x, key, "boolean"))[0];
  }
  int generic_map_get_integer(generic_t x, const char* key) {
    return ((int*)generic_map_get_item(x, key, "integer"))[0];
  }
  void* generic_map_get_null(generic_t x, const char* key) {
    return ((void**)generic_map_get_item(x, key, "null"))[0];
  }
  double generic_map_get_number(generic_t x, const char* key) {
    return ((double*)generic_map_get_item(x, key, "number"))[0];
  }
  char* generic_map_get_string(generic_t x, const char* key) {
    return ((char**)generic_map_get_item(x, key, "string"))[0];
  }
  generic_t generic_map_get_object(generic_t x, const char* key) {
    YggGeneric* result = (YggGeneric*)generic_map_get_item(x, key, "object");
    generic_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  generic_t generic_map_get_array(generic_t x, const char* key) {
    YggGeneric* result = (YggGeneric*)generic_map_get_item(x, key, "array");
    generic_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  ply_t generic_map_get_ply(generic_t x, const char* key) {
    ply_t* old = (ply_t*)generic_map_get_item(x, key, "ply");
    ply_t out = copy_ply(*old);
    return out;
  }
  obj_t generic_map_get_obj(generic_t x, const char* key) {
    obj_t* old = (obj_t*)generic_map_get_item(x, key, "obj");
    obj_t out = copy_obj(*old);
    return out;
  }
  python_t generic_map_get_python_class(generic_t x, const char* key) {
    python_t* old = (python_t*)generic_map_get_item(x, key, "class");
    python_t out = copy_python(*old);
    return out;
  }
  python_t generic_map_get_python_function(generic_t x, const char* key) {
    python_t* old = (python_t*)generic_map_get_item(x, key, "function");
    python_t out = copy_python(*old);
    return out;
  }
  schema_t generic_map_get_schema(generic_t x, const char* key) {
    YggGeneric* result = (YggGeneric*)generic_map_get_item(x, key, "schema");
    schema_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  generic_t generic_map_get_any(generic_t x, const char* key) {
    YggGeneric* result = (YggGeneric*)generic_map_get_item(x, key, "any");
    generic_t out = init_generic();
    out.obj = (void*)(result->copy());
    return out;
  }
  
  void* generic_map_get_scalar(generic_t x, const char* key,
			       const char *subtype,
			       const size_t precision) {
    void* out = NULL;
    char new_units[100] = "";
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_scalar: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_scalar: Object is NULL.");
      }
      const MetaschemaType* item_type0 = x_obj->get_type()->get_property_type(key);
      if (item_type0->type_code() == T_SCALAR) {
	const ScalarMetaschemaType* item_type0_scl = static_cast<const ScalarMetaschemaType*>(item_type0);
	strcpy(new_units, item_type0_scl->units());
      }
      ScalarMetaschemaType* item_type = new ScalarMetaschemaType(subtype, precision, new_units, x_obj->get_type()->use_generic());
      out = x_obj->get_data_map_item(key, item_type);
      delete item_type;
    } catch (...) {
      ygglog_error("generic_map_get_scalar: C++ exception thrown.");
      out = NULL;
    }
    return out;
  }
  int8_t generic_map_get_int8(generic_t x, const char* key) {
    return ((int8_t*)generic_map_get_scalar(x, key, "int", 8*sizeof(int8_t)))[0];
  }
  int16_t generic_map_get_int16(generic_t x, const char* key) {
    return ((int16_t*)generic_map_get_scalar(x, key, "int", 8*sizeof(int16_t)))[0];
  }
  int32_t generic_map_get_int32(generic_t x, const char* key) {
    return ((int32_t*)generic_map_get_scalar(x, key, "int", 8*sizeof(int32_t)))[0];
  }
  int64_t generic_map_get_int64(generic_t x, const char* key) {
    return ((int64_t*)generic_map_get_scalar(x, key, "int", 8*sizeof(int64_t)))[0];
  }
  uint8_t generic_map_get_uint8(generic_t x, const char* key) {
    return ((uint8_t*)generic_map_get_scalar(x, key, "uint", 8*sizeof(uint8_t)))[0];
  }
  uint16_t generic_map_get_uint16(generic_t x, const char* key) {
    return ((uint16_t*)generic_map_get_scalar(x, key, "uint", 8*sizeof(uint16_t)))[0];
  }
  uint32_t generic_map_get_uint32(generic_t x, const char* key) {
    return ((uint32_t*)generic_map_get_scalar(x, key, "uint", 8*sizeof(uint32_t)))[0];
  }
  uint64_t generic_map_get_uint64(generic_t x, const char* key) {
    return ((uint64_t*)generic_map_get_scalar(x, key, "uint", 8*sizeof(uint64_t)))[0];
  }
  float generic_map_get_float(generic_t x, const char* key) {
    return ((float*)generic_map_get_scalar(x, key, "float", 8*sizeof(float)))[0];
  }
  double generic_map_get_double(generic_t x, const char* key) {
    return ((double*)generic_map_get_scalar(x, key, "float", 8*sizeof(double)))[0];
  }
  long double generic_map_get_long_double(generic_t x, const char* key) {
    return ((long double*)generic_map_get_scalar(x, key, "float", 8*sizeof(long double)))[0];
  }
  complex_float_t generic_map_get_complex_float(generic_t x, const char* key) {
    return ((complex_float_t*)generic_map_get_scalar(x, key, "complex", 8*sizeof(complex_float_t)))[0];
  }
  complex_double_t generic_map_get_complex_double(generic_t x, const char* key) {
    return ((complex_double_t*)generic_map_get_scalar(x, key, "complex", 8*sizeof(complex_double_t)))[0];
  }
  complex_long_double_t generic_map_get_complex_long_double(generic_t x, const char* key) {
    return ((complex_long_double_t*)generic_map_get_scalar(x, key, "complex", 8*sizeof(complex_long_double_t)))[0];
  }
  char* generic_map_get_bytes(generic_t x, const char* key) {
    return ((char**)generic_map_get_scalar(x, key, "bytes", 0))[0];
  }
  char* generic_map_get_unicode(generic_t x, const char* key) {
    return ((char**)generic_map_get_scalar(x, key, "unicode", 0))[0];
  }
  
  size_t generic_map_get_1darray(generic_t x, const char* key,
				 const char *subtype, const size_t precision,
				 void** data) {
    size_t out = 0;
    char new_units[100] = "";
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_1darray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_1darray: Object is NULL.");
      }
      size_t new_length = 0;
      const MetaschemaType* item_type0 = x_obj->get_type()->get_property_type(key);
      if (item_type0->type_code() == T_1DARRAY) {
	const OneDArrayMetaschemaType* item_type0_arr = static_cast<const OneDArrayMetaschemaType*>(item_type0);
	strcpy(new_units, item_type0_arr->units());
	new_length = item_type0_arr->length();
      }
      OneDArrayMetaschemaType* item_type = new OneDArrayMetaschemaType(subtype, precision, new_length, new_units, x_obj->get_type()->use_generic());
      size_t nbytes = item_type->nbytes();
      void* new_data = x_obj->get_data_map_item(key, item_type);
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_map_get_1darray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
      out = new_length;
      delete item_type;
    } catch (...) {
      ygglog_error("generic_map_get_1darray: C++ exception thrown.");
    }
    return out;
  }
  size_t generic_map_get_1darray_int8(generic_t x, const char* key, int8_t** data) {
    return generic_map_get_1darray(x, key, "int", 8*sizeof(int8_t), (void**)data);
  }
  size_t generic_map_get_1darray_int16(generic_t x, const char* key, int16_t** data) {
    return generic_map_get_1darray(x, key, "int", 8*sizeof(int16_t), (void**)data);
  }
  size_t generic_map_get_1darray_int32(generic_t x, const char* key, int32_t** data) {
    return generic_map_get_1darray(x, key, "int", 8*sizeof(int32_t), (void**)data);
  }
  size_t generic_map_get_1darray_int64(generic_t x, const char* key, int64_t** data) {
    return generic_map_get_1darray(x, key, "int", 8*sizeof(int64_t), (void**)data);
  }
  size_t generic_map_get_1darray_uint8(generic_t x, const char* key, uint8_t** data) {
    return generic_map_get_1darray(x, key, "uint", 8*sizeof(uint8_t), (void**)data);
  }
  size_t generic_map_get_1darray_uint16(generic_t x, const char* key, uint16_t** data) {
    return generic_map_get_1darray(x, key, "uint", 8*sizeof(uint16_t), (void**)data);
  }
  size_t generic_map_get_1darray_uint32(generic_t x, const char* key, uint32_t** data) {
    return generic_map_get_1darray(x, key, "uint", 8*sizeof(uint32_t), (void**)data);
  }
  size_t generic_map_get_1darray_uint64(generic_t x, const char* key, uint64_t** data) {
    return generic_map_get_1darray(x, key, "uint", 8*sizeof(uint64_t), (void**)data);
  }
  size_t generic_map_get_1darray_float(generic_t x, const char* key,
				       float** data) {
    return generic_map_get_1darray(x, key, "float", 8*sizeof(float), (void**)data);
  }
  size_t generic_map_get_1darray_double(generic_t x, const char* key,
					double** data) {
    return generic_map_get_1darray(x, key, "float", 8*sizeof(double), (void**)data);
  }
  size_t generic_map_get_1darray_long_double(generic_t x, const char* key,
					     long double** data) {
    return generic_map_get_1darray(x, key, "float", 8*sizeof(long double), (void**)data);
  }
  size_t generic_map_get_1darray_complex_float(generic_t x, const char* key, complex_float_t** data) {
    return generic_map_get_1darray(x, key, "complex", 8*sizeof(complex_float_t), (void**)data);
  }
  size_t generic_map_get_1darray_complex_double(generic_t x, const char* key, complex_double_t** data) {
    return generic_map_get_1darray(x, key, "complex", 8*sizeof(complex_double_t), (void**)data);
  }
  size_t generic_map_get_1darray_complex_long_double(generic_t x, const char* key, complex_long_double_t** data) {
    return generic_map_get_1darray(x, key, "complex", 8*sizeof(complex_long_double_t), (void**)data);
  }
  size_t generic_map_get_1darray_bytes(generic_t x, const char* key,  char** data) {
    return generic_map_get_1darray(x, key, "bytes", 0, (void**)data);
  }
  size_t generic_map_get_1darray_unicode(generic_t x, const char* key,  char** data) {
    return generic_map_get_1darray(x, key, "unicode", 0, (void**)data);
  }

  size_t generic_map_get_ndarray(generic_t x, const char* key,
				 const char *subtype, const size_t precision,
				 void** data, size_t** shape) {
    size_t out = 0;
    size_t i;
    char new_units[100] = "";
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_get_ndarray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_get_ndarray: Object is NULL.");
      }
      std::vector<size_t> new_shape;
      const MetaschemaType* item_type0 = x_obj->get_type()->get_property_type(key);
      if (item_type0->type_code() == T_NDARRAY) {
	const NDArrayMetaschemaType* item_type0_arr = static_cast<const NDArrayMetaschemaType*>(item_type0);
	strcpy(new_units, item_type0_arr->units());
	new_shape = item_type0_arr->shape();
      }
      NDArrayMetaschemaType* item_type = new NDArrayMetaschemaType(subtype, precision, new_shape, new_units, x_obj->get_type()->use_generic());
      size_t nbytes = item_type->nbytes();
      void* new_data = x_obj->get_data_map_item(key, item_type);
      data[0] = (void*)realloc(data[0], nbytes);
      if (data[0] == NULL) {
	ygglog_throw_error("generic_map_get_ndarray: Failed to reallocate array.");
      }
      memcpy(data[0], new_data, nbytes);
      shape[0] = (size_t*)realloc(shape[0], new_shape.size());
      if (shape[0] == NULL) {
	ygglog_throw_error("generic_map_get_ndarray: Failed to realloc shape.");
      }
      for (i = 0; i < new_shape.size(); i++) {
	shape[0][i] = new_shape[i];
      }
      out = new_shape.size();
      delete item_type;
    } catch (...) {
      ygglog_error("generic_map_get_ndarray: C++ exception thrown.");
    }
    return out;
  }
  size_t generic_map_get_ndarray_int8(generic_t x, const char* key, int8_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "int", 8*sizeof(int8_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_int16(generic_t x, const char* key, int16_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "int", 8*sizeof(int16_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_int32(generic_t x, const char* key, int32_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "int", 8*sizeof(int32_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_int64(generic_t x, const char* key, int64_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "int", 8*sizeof(int64_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_uint8(generic_t x, const char* key, uint8_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "uint", 8*sizeof(uint8_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_uint16(generic_t x, const char* key, uint16_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "uint", 8*sizeof(uint16_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_uint32(generic_t x, const char* key, uint32_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "uint", 8*sizeof(uint32_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_uint64(generic_t x, const char* key, uint64_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "uint", 8*sizeof(uint64_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_float(generic_t x, const char* key,
				       float** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "float", 8*sizeof(float),
				   (void**)data, shape);
  }
  size_t generic_map_get_ndarray_double(generic_t x, const char* key,
					double** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "float", 8*sizeof(double),
				   (void**)data, shape);
  }
  size_t generic_map_get_ndarray_long_double(generic_t x, const char* key,
					     long double** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "float", 8*sizeof(long double),
				   (void**)data, shape);
  }
  size_t generic_map_get_ndarray_complex_float(generic_t x, const char* key, complex_float_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "complex", 8*sizeof(complex_float_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_complex_double(generic_t x, const char* key, complex_double_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "complex", 8*sizeof(complex_double_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_complex_long_double(generic_t x, const char* key, complex_long_double_t** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "complex", 8*sizeof(complex_long_double_t), (void**)data, shape);
  }
  size_t generic_map_get_ndarray_bytes(generic_t x, const char* key, char** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "bytes", 0, (void**)data, shape);
  }
  size_t generic_map_get_ndarray_unicode(generic_t x, const char* key, char** data, size_t** shape) {
    return generic_map_get_ndarray(x, key, "unicode", 0, (void**)data, shape);
  }
  
  int generic_array_set_item(generic_t x, const size_t index,
			     const char *type, void* value) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_set_item: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_set_item: Object is NULL.");
      }
      bool use_generic = x_obj->get_type()->use_generic();
      std::map<const char*, int, strcomp> type_map = get_type_map();
      std::map<const char*, int, strcomp>::iterator it = type_map.find(type);
      YggGeneric* generic_value = NULL;
      MetaschemaType* item_type = NULL;
      bool generic_value_created = true;
      if (it != type_map.end()) {
	switch (it->second) {
	case T_BOOLEAN:
	case T_INTEGER:
	case T_NULL:
	case T_NUMBER:
	case T_STRING: {
	  item_type = new MetaschemaType(type, use_generic);
	  break;
	}
	case T_PLY: {
	  item_type = new PlyMetaschemaType(use_generic);
	  break;
	}
	case T_OBJ: {
	  item_type = new ObjMetaschemaType(use_generic);
	  break;
	}
	case T_CLASS:
	case T_FUNCTION: {
	  item_type = new PyObjMetaschemaType(type, use_generic);
	  break;
	}
	case T_ARRAY:
	case T_OBJECT:
	case T_SCHEMA:
	case T_ANY: {
	  generic_value_created = false;
	  generic_t* c_gen_value = (generic_t*)(value);
	  if (!(is_generic_init(*c_gen_value))) {
	    ygglog_throw_error("generic_array_set_item: %s values must be provided as a generic_t object.", type);
	  }
	  generic_value = (YggGeneric*)(c_gen_value->obj);
	  if (generic_value == NULL) {
	    ygglog_throw_error("generic_array_set_item: %s value is generic wrapper around a NULL object.", type);
	  }
	  break;
	}
	}
      }
      if ((generic_value == NULL) && (item_type != NULL)) {
	generic_value_created = true;
	generic_value = new YggGeneric(item_type, value);
      }
      if (generic_value == NULL) {
	ygglog_throw_error("generic_array_set_item: No handler for type '%s'.", type);
      }
      x_obj->set_data_array_item(index, generic_value);
      if (item_type != NULL) {
	delete item_type;
      }
      if (generic_value_created) {
	delete generic_value;
      }
    } catch (...) {
      ygglog_error("generic_array_set_item: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_array_set_bool(generic_t x, const size_t index,
			     bool value) {
    return generic_array_set_item(x, index, "boolean", (void*)(&value));
  }
  int generic_array_set_integer(generic_t x, const size_t index,
				int value) {
    return generic_array_set_item(x, index, "integer", (void*)(&value));
  }
  int generic_array_set_null(generic_t x, const size_t index,
			     void* value) {
    return generic_array_set_item(x, index, "null", (void*)(&value));
  }
  int generic_array_set_number(generic_t x, const size_t index,
			       double value) {
    return generic_array_set_item(x, index, "number", (void*)(&value));
  }
  int generic_array_set_string(generic_t x, const size_t index,
			       char* value) {
    return generic_array_set_item(x, index, "string", (void*)(&value));
  }
  int generic_array_set_object(generic_t x, const size_t index,
			       generic_t value) {
    return generic_array_set_item(x, index, "object", (void*)(&value));
  }
  int generic_array_set_map(generic_t x, const size_t index,
			    generic_t value) {
    return generic_array_set_item(x, index, "object", (void*)(&value));
  }
  int generic_array_set_array(generic_t x, const size_t index,
			      generic_t value) {
    return generic_array_set_item(x, index, "array", (void*)(&value));
  }
  int generic_array_set_direct(generic_t x, const size_t index,
			       char* value) {
    return generic_array_set_item(x, index, "direct", (void*)(&value));
  }
  int generic_array_set_ply(generic_t x, const size_t index,
			    ply_t value) {
    return generic_array_set_item(x, index, "ply", (void*)(&value));
  }
  int generic_array_set_obj(generic_t x, const size_t index,
			    obj_t value) {
    return generic_array_set_item(x, index, "obj", (void*)(&value));
  }
  int generic_array_set_python_class(generic_t x, const size_t index,
				     python_t value) {
    return generic_array_set_item(x, index, "class", (void*)(&value));
  }
  int generic_array_set_python_function(generic_t x, const size_t index,
					python_t value) {
    return generic_array_set_item(x, index, "function", (void*)(&value));
  }
  int generic_array_set_schema(generic_t x, const size_t index,
			       schema_t value) {
    return generic_array_set_item(x, index, "schema", (void*)(&value));
  }
  int generic_array_set_any(generic_t x, const size_t index,
			    generic_t value) {
    return generic_array_set_item(x, index, "any", (void*)(&value));
  }
  
  int generic_array_set_scalar(generic_t x, const size_t index,
			       void* value, const char *subtype,
			       const size_t precision, const char *units) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_set_scalar: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_set_scalar: Object is NULL.");
      }
      ScalarMetaschemaType* item_type = new ScalarMetaschemaType(subtype, precision, units, x_obj->get_type()->use_generic());
      YggGeneric* generic_value = new YggGeneric(item_type, value);
      x_obj->set_data_array_item(index, generic_value);
      delete item_type;
      delete generic_value;
    } catch (...) {
      ygglog_error("generic_array_set_scalar: C++ exception thrown.");
    }
    return out;
  }
  int generic_array_set_int8(generic_t x, const size_t index, int8_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "int", 8*sizeof(int8_t), units);
  }
  int generic_array_set_int16(generic_t x, const size_t index, int16_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "int", 8*sizeof(int16_t), units);
  }
  int generic_array_set_int32(generic_t x, const size_t index, int32_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "int", 8*sizeof(int32_t), units);
  }
  int generic_array_set_int64(generic_t x, const size_t index, int64_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "int", 8*sizeof(int64_t), units);
  }
  int generic_array_set_uint8(generic_t x, const size_t index, uint8_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "int", 8*sizeof(uint8_t), units);
  }
  int generic_array_set_uint16(generic_t x, const size_t index, uint16_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "uint", 8*sizeof(uint16_t), units);
  }
  int generic_array_set_uint32(generic_t x, const size_t index, uint32_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "uint", 8*sizeof(uint32_t), units);
  }
  int generic_array_set_uint64(generic_t x, const size_t index, uint64_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "uint", 8*sizeof(uint64_t), units);
  }
  int generic_array_set_float(generic_t x, const size_t index, float value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "float", 8*sizeof(float), units);
  }
  int generic_array_set_double(generic_t x, const size_t index, double value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "float", 8*sizeof(double), units);
  }
  int generic_array_set_long_double(generic_t x, const size_t index, long double value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "float", 8*sizeof(long double), units);
  }
  int generic_array_set_complex_float(generic_t x, const size_t index,
				      complex_float_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "complex", 8*sizeof(complex_float_t), units);
  }
  int generic_array_set_complex_double(generic_t x, const size_t index,
				       complex_double_t value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "complex", 8*sizeof(complex_double_t), units);
  }
  int generic_array_set_complex_long_double(generic_t x, const size_t index,
					    complex_long_double_t value,
					    const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "complex", 8*sizeof(complex_long_double_t), units);
  }
  int generic_array_set_bytes(generic_t x, const size_t index, char* value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "bytes", 0, units);
  }
  int generic_array_set_unicode(generic_t x, const size_t index, char* value, const char* units) {
    return generic_array_set_scalar(x, index, (void*)(&value), "unicode", 0, units);
  }


  int generic_array_set_1darray(generic_t x, const size_t index,
				void* value, const char *subtype,
				const size_t precision,
				const size_t length,
				const char* units) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_set_1darray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_set_1darray: Object is NULL.");
      }
      OneDArrayMetaschemaType* item_type = new OneDArrayMetaschemaType(subtype, precision, length, units, x_obj->get_type()->use_generic());
      YggGeneric* generic_value = new YggGeneric(item_type, value);
      x_obj->set_data_array_item(index, generic_value);
      delete item_type;
      delete generic_value;
    } catch (...) {
      ygglog_error("generic_array_set_1darray: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_array_set_1darray_int8(generic_t x, const size_t index,
				     int8_t* value, const size_t length,
				     const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "int", 8*sizeof(int8_t), length, units);
  }
  int generic_array_set_1darray_int16(generic_t x, const size_t index,
				      int16_t* value, const size_t length,
				      const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "int", 8*sizeof(int16_t), length, units);
  }
  int generic_array_set_1darray_int32(generic_t x, const size_t index,
				      int32_t* value, const size_t length,
				      const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "int", 8*sizeof(int32_t), length, units);
  }
  int generic_array_set_1darray_int64(generic_t x, const size_t index,
				      int64_t* value, const size_t length,
				      const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "int", 8*sizeof(int64_t), length, units);
  }
  int generic_array_set_1darray_uint8(generic_t x, const size_t index,
				      uint8_t* value, const size_t length,
				      const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "uint", 8*sizeof(uint8_t), length, units);
  }
  int generic_array_set_1darray_uint16(generic_t x, const size_t index,
				       uint16_t* value, const size_t length,
				       const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "uint", 8*sizeof(uint16_t), length, units);
  }
  int generic_array_set_1darray_uint32(generic_t x, const size_t index,
				       uint32_t* value, const size_t length,
				       const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "uint", 8*sizeof(uint32_t), length, units);
  }
  int generic_array_set_1darray_uint64(generic_t x, const size_t index,
				       uint64_t* value, const size_t length,
				       const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "uint", 8*sizeof(uint64_t), length, units);
  }
  int generic_array_set_1darray_float(generic_t x, const size_t index,
				      float* value, const size_t length,
				      const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "float", 8*sizeof(float), length, units);
  }
  int generic_array_set_1darray_double(generic_t x, const size_t index,
				       double* value, const size_t length,
				       const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "float", 8*sizeof(double), length, units);
  }
  int generic_array_set_1darray_long_double(generic_t x, const size_t index, long double* value, const size_t length, const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "float", 8*sizeof(long double), length, units);
  }
  int generic_array_set_1darray_complex_float(generic_t x, const size_t index, complex_float_t* value, const size_t length, const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "complex", 8*sizeof(complex_float_t), length, units);
  }
  int generic_array_set_1darray_complex_double(generic_t x, const size_t index, complex_double_t* value, const size_t length, const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "complex", 8*sizeof(complex_double_t), length, units);
  }
  int generic_array_set_1darray_complex_long_double(generic_t x, const size_t index, complex_long_double_t* value, const size_t length, const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "complex", 8*sizeof(complex_long_double_t), length, units);
  }
  int generic_array_set_1darray_bytes(generic_t x, const size_t index,
				      char** value, const size_t length,
				      const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "bytes", 0, length, units);
  }
  int generic_array_set_1darray_unicode(generic_t x, const size_t index,
					char** value, const size_t length,
					const char* units) {
    return generic_array_set_1darray(x, index, (void*)value, "unicode", 0, length, units);
  }
  
  
  int generic_array_set_ndarray(generic_t x, const size_t index,
				void* data, const char *subtype,
				const size_t precision,
				const size_t ndim, const size_t* shape,
				const char* units) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_array_set_ndarray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_array_set_ndarray: Object is NULL.");
      }
      std::vector<size_t> new_shape;
      size_t i;
      for (i = 0; i < ndim; i++) {
	new_shape.push_back(shape[i]);
      }
      NDArrayMetaschemaType* item_type = new NDArrayMetaschemaType(subtype, precision, new_shape, units, x_obj->get_type()->use_generic());
      YggGeneric* generic_value = new YggGeneric(item_type, data);
      x_obj->set_data_array_item(index, generic_value);
      delete item_type;
      delete generic_value;
    } catch (...) {
      ygglog_error("generic_array_set_ndarray: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_array_set_ndarray_int8(generic_t x, const size_t index,
				     int8_t* data, const size_t ndim,
				     const size_t* shape,
				     const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "int", 8*sizeof(int8_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_int16(generic_t x, const size_t index,
				      int16_t* data, const size_t ndim,
				      const size_t* shape,
				      const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "int", 8*sizeof(int16_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_int32(generic_t x, const size_t index,
				      int32_t* data, const size_t ndim,
				      const size_t* shape,
				      const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "int", 8*sizeof(int32_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_int64(generic_t x, const size_t index,
				      int64_t* data, const size_t ndim,
				      const size_t* shape,
				      const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "int", 8*sizeof(int64_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_uint8(generic_t x, const size_t index,
				      uint8_t* data, const size_t ndim,
				      const size_t* shape,
				      const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "uint", 8*sizeof(uint8_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_uint16(generic_t x, const size_t index,
				       uint16_t* data, const size_t ndim,
				       const size_t* shape,
				       const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "uint", 8*sizeof(uint16_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_uint32(generic_t x, const size_t index,
				       uint32_t* data, const size_t ndim,
				       const size_t* shape,
				       const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "uint", 8*sizeof(uint32_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_uint64(generic_t x, const size_t index,
				       uint64_t* data, const size_t ndim,
				       const size_t* shape,
				       const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "uint", 8*sizeof(uint64_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_float(generic_t x, const size_t index,
				      float* data, const size_t ndim,
				      const size_t* shape,
				      const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "float", 8*sizeof(float), ndim, shape, units);
  }
  int generic_array_set_ndarray_double(generic_t x, const size_t index,
				       double* data, const size_t ndim,
				       const size_t* shape,
				       const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "float", 8*sizeof(double), ndim, shape, units);
  }
  int generic_array_set_ndarray_long_double(generic_t x, const size_t index, long double* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "float", 8*sizeof(long double), ndim, shape, units);
  }
  int generic_array_set_ndarray_complex_float(generic_t x, const size_t index, complex_float_t* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "complex", 8*sizeof(complex_float_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_complex_double(generic_t x, const size_t index, complex_double_t* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "complex", 8*sizeof(complex_double_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_complex_long_double(generic_t x, const size_t index, complex_long_double_t* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "complex", 8*sizeof(complex_long_double_t), ndim, shape, units);
  }
  int generic_array_set_ndarray_bytes(generic_t x, const size_t index, char** data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "bytes", 0, ndim, shape, units);
  }
  int generic_array_set_ndarray_unicode(generic_t x, const size_t index, char** data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_array_set_ndarray(x, index, (void*)data, "unicode", 0, ndim, shape, units);
  }
  
  
  int generic_map_set_item(generic_t x, const char* key,
			   const char* type, void* value) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_set_item: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_set_item: Object is NULL.");
      }
      bool use_generic = x_obj->get_type()->use_generic();
      std::map<const char*, int, strcomp> type_map = get_type_map();
      std::map<const char*, int, strcomp>::iterator it = type_map.find(type);
      YggGeneric* generic_value = NULL;
      MetaschemaType* item_type = NULL;
      bool generic_value_created = true;
      if (it != type_map.end()) {
	switch (it->second) {
	case T_BOOLEAN:
	case T_INTEGER:
	case T_NULL:
	case T_NUMBER:
	case T_STRING: {
	  item_type = new MetaschemaType(type, use_generic);
	  break;
	}
	case T_PLY: {
	  item_type = new PlyMetaschemaType(use_generic);
	  break;
	}
	case T_OBJ: {
	  item_type = new ObjMetaschemaType(use_generic);
	  break;
	}
	case T_CLASS:
	case T_FUNCTION: {
	  item_type = new PyObjMetaschemaType(type, use_generic);
	  break;
	}
	case T_ARRAY:
	case T_OBJECT:
	case T_SCHEMA:
	case T_ANY: {
	  generic_value_created = false;
	  generic_t* c_gen_value = (generic_t*)(value);
	  if (!(is_generic_init(*c_gen_value))) {
	    ygglog_throw_error("generic_map_set_item: %s values must be provided as a generic_t object.", type);
	  }
	  generic_value = (YggGeneric*)(c_gen_value->obj);
	  if (generic_value == NULL) {
	    ygglog_throw_error("generic_map_set_item: %s value is generic wrapper around a NULL object.", type);
	  }
	  break;
	}
	}
      }
      if ((generic_value == NULL) && (item_type != NULL)) {
	generic_value_created = true;
	generic_value = new YggGeneric(item_type, value);
      }
      if (generic_value == NULL) {
	ygglog_throw_error("generic_map_set_item: No handler for type '%s'.", type);
      }
      x_obj->set_data_map_item(key, generic_value);
      if (item_type != NULL) {
	delete item_type;
      }
      if (generic_value_created) {
	delete generic_value;
      }
    } catch (...) {
      ygglog_error("generic_map_set_item: C++ exception thrown.");
      out = -1;
    }
    return out;
  }

  int generic_map_set_bool(generic_t x, const char* key,
			   bool value) {
    return generic_map_set_item(x, key, "boolean", (void*)(&value));
  }
  int generic_map_set_integer(generic_t x, const char* key,
			      int value) {
    return generic_map_set_item(x, key, "integer", (void*)(&value));
  }
  int generic_map_set_null(generic_t x, const char* key,
			   void* value) {
    return generic_map_set_item(x, key, "null", (void*)(&value));
  }
  int generic_map_set_number(generic_t x, const char* key,
			     double value) {
    return generic_map_set_item(x, key, "number", (void*)(&value));
  }
  int generic_map_set_string(generic_t x, const char* key,
			     char* value) {
    return generic_map_set_item(x, key, "string", (void*)(&value));
  }
  int generic_map_set_object(generic_t x, const char* key,
			     generic_t value) {
    return generic_map_set_item(x, key, "object", (void*)(&value));
  }
  int generic_map_set_map(generic_t x, const char* key,
			  generic_t value) {
    return generic_map_set_item(x, key, "object", (void*)(&value));
  }
  int generic_map_set_array(generic_t x, const char* key,
			    generic_t value) {
    return generic_map_set_item(x, key, "array", (void*)(&value));
  }
  int generic_map_set_direct(generic_t x, const char* key,
			     char* value) {
    return generic_map_set_item(x, key, "direct", (void*)(&value));
  }
  int generic_map_set_ply(generic_t x, const char* key,
			  ply_t value) {
    return generic_map_set_item(x, key, "ply", (void*)(&value));
  }
  int generic_map_set_obj(generic_t x, const char* key,
			  obj_t value) {
    return generic_map_set_item(x, key, "obj", (void*)(&value));
  }
  int generic_map_set_python_class(generic_t x, const char* key,
				   python_t value) {
    return generic_map_set_item(x, key, "class", (void*)(&value));
  }
  int generic_map_set_python_function(generic_t x, const char* key,
				      python_t value) {
    return generic_map_set_item(x, key, "function", (void*)(&value));
  }
  int generic_map_set_schema(generic_t x, const char* key,
			     schema_t value) {
    return generic_map_set_item(x, key, "schema", (void*)(&value));
  }
  int generic_map_set_any(generic_t x, const char* key,
			  generic_t value) {
    return generic_map_set_item(x, key, "any", (void*)(&value));
  }
  
  int generic_map_set_scalar(generic_t x, const char* key,
			     void* value, const char *subtype,
			     const size_t precision, const char *units) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_set_scalar: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_set_scalar: Object is NULL.");
      }
      ScalarMetaschemaType* item_type = new ScalarMetaschemaType(subtype, precision, units, x_obj->get_type()->use_generic());
      YggGeneric* generic_value = new YggGeneric(item_type, value);
      x_obj->set_data_map_item(key, generic_value);
      delete item_type;
      delete generic_value;
    } catch (...) {
      ygglog_error("generic_map_set_scalar: C++ exception thrown.");
    }
    return out;
  }
  int generic_map_set_int8(generic_t x, const char* key, int8_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "int", 8*sizeof(int8_t), units);
  }
  int generic_map_set_int16(generic_t x, const char* key, int16_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "int", 8*sizeof(int16_t), units);
  }
  int generic_map_set_int32(generic_t x, const char* key, int32_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "int", 8*sizeof(int32_t), units);
  }
  int generic_map_set_int64(generic_t x, const char* key, int64_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "int", 8*sizeof(int64_t), units);
  }
  int generic_map_set_uint8(generic_t x, const char* key, uint8_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "int", 8*sizeof(uint8_t), units);
  }
  int generic_map_set_uint16(generic_t x, const char* key, uint16_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "uint", 8*sizeof(uint16_t), units);
  }
  int generic_map_set_uint32(generic_t x, const char* key, uint32_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "uint", 8*sizeof(uint32_t), units);
  }
  int generic_map_set_uint64(generic_t x, const char* key, uint64_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "uint", 8*sizeof(uint64_t), units);
  }
  int generic_map_set_float(generic_t x, const char* key, float value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "float", 8*sizeof(float), units);
  }
  int generic_map_set_double(generic_t x, const char* key, double value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "float", 8*sizeof(double), units);
  }
  int generic_map_set_long_double(generic_t x, const char* key, long double value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "float", 8*sizeof(long double), units);
  }
  int generic_map_set_complex_float(generic_t x, const char* key,
				    complex_float_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "complex", 8*sizeof(complex_float_t), units);
  }
  int generic_map_set_complex_double(generic_t x, const char* key,
				     complex_double_t value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "complex", 8*sizeof(complex_double_t), units);
  }
  int generic_map_set_complex_long_double(generic_t x, const char* key,
					  complex_long_double_t value,
					  const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "complex", 8*sizeof(complex_long_double_t), units);
  }
  int generic_map_set_bytes(generic_t x, const char* key, char* value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "bytes", 0, units);
  }
  int generic_map_set_unicode(generic_t x, const char* key, char* value, const char* units) {
    return generic_map_set_scalar(x, key, (void*)(&value), "unicode", 0, units);
  }


  int generic_map_set_1darray(generic_t x, const char* key,
			      void* value, const char *subtype,
			      const size_t precision,
			      const size_t length,
			      const char* units) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_set_1darray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_set_1darray: Object is NULL.");
      }
      OneDArrayMetaschemaType* item_type = new OneDArrayMetaschemaType(subtype, precision, length, units, x_obj->get_type()->use_generic());
      YggGeneric* generic_value = new YggGeneric(item_type, value);
      x_obj->set_data_map_item(key, generic_value);
      delete item_type;
      delete generic_value;
    } catch (...) {
      ygglog_error("generic_map_set_1darray: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_map_set_1darray_int8(generic_t x, const char* key,
				   int8_t* value, const size_t length,
				   const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "int", 8*sizeof(int8_t), length, units);
  }
  int generic_map_set_1darray_int16(generic_t x, const char* key,
				    int16_t* value, const size_t length,
				    const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "int", 8*sizeof(int16_t), length, units);
  }
  int generic_map_set_1darray_int32(generic_t x, const char* key,
				    int32_t* value, const size_t length,
				    const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "int", 8*sizeof(int32_t), length, units);
  }
  int generic_map_set_1darray_int64(generic_t x, const char* key,
				    int64_t* value, const size_t length,
				    const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "int", 8*sizeof(int64_t), length, units);
  }
  int generic_map_set_1darray_uint8(generic_t x, const char* key,
				    uint8_t* value, const size_t length,
				    const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "uint", 8*sizeof(uint8_t), length, units);
  }
  int generic_map_set_1darray_uint16(generic_t x, const char* key,
				     uint16_t* value, const size_t length,
				     const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "uint", 8*sizeof(uint16_t), length, units);
  }
  int generic_map_set_1darray_uint32(generic_t x, const char* key,
				     uint32_t* value, const size_t length,
				     const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "uint", 8*sizeof(uint32_t), length, units);
  }
  int generic_map_set_1darray_uint64(generic_t x, const char* key,
				     uint64_t* value, const size_t length,
				     const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "uint", 8*sizeof(uint64_t), length, units);
  }
  int generic_map_set_1darray_float(generic_t x, const char* key,
				    float* value, const size_t length,
				    const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "float", 8*sizeof(float), length, units);
  }
  int generic_map_set_1darray_double(generic_t x, const char* key,
				     double* value, const size_t length,
				     const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "float", 8*sizeof(double), length, units);
  }
  int generic_map_set_1darray_long_double(generic_t x, const char* key, long double* value, const size_t length, const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "float", 8*sizeof(long double), length, units);
  }
  int generic_map_set_1darray_complex_float(generic_t x, const char* key, complex_float_t* value, const size_t length, const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "complex", 8*sizeof(complex_float_t), length, units);
  }
  int generic_map_set_1darray_complex_double(generic_t x, const char* key, complex_double_t* value, const size_t length, const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "complex", 8*sizeof(complex_double_t), length, units);
  }
  int generic_map_set_1darray_complex_long_double(generic_t x, const char* key, complex_long_double_t* value, const size_t length, const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "complex", 8*sizeof(complex_long_double_t), length, units);
  }
  int generic_map_set_1darray_bytes(generic_t x, const char* key,
				    char** value, const size_t length,
				    const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "bytes", 0, length, units);
  }
  int generic_map_set_1darray_unicode(generic_t x, const char* key,
				      char** value, const size_t length,
				      const char* units) {
    return generic_map_set_1darray(x, key, (void*)value, "unicode", 0, length, units);
  }
  
  
  int generic_map_set_ndarray(generic_t x, const char* key,
			      void* data, const char *subtype,
			      const size_t precision,
			      const size_t ndim, const size_t* shape,
			      const char* units) {
    int out = 0;
    try {
      if (!(is_generic_init(x))) {
	ygglog_throw_error("generic_map_set_ndarray: Object not initialized.");
      }
      YggGeneric* x_obj = (YggGeneric*)(x.obj);
      if (x_obj == NULL) {
	ygglog_throw_error("generic_map_set_ndarray: Object is NULL.");
      }
      std::vector<size_t> new_shape;
      size_t i;
      for (i = 0; i < ndim; i++) {
	new_shape.push_back(shape[i]);
      }
      NDArrayMetaschemaType* item_type = new NDArrayMetaschemaType(subtype, precision, new_shape, units, x_obj->get_type()->use_generic());
      YggGeneric* generic_value = new YggGeneric(item_type, data);
      x_obj->set_data_map_item(key, generic_value);
      delete item_type;
      delete generic_value;
    } catch (...) {
      ygglog_error("generic_map_set_ndarray: C++ exception thrown.");
      out = -1;
    }
    return out;
  }
  int generic_map_set_ndarray_int8(generic_t x, const char* key,
				   int8_t* data, const size_t ndim,
				   const size_t* shape,
				   const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "int", 8*sizeof(int8_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_int16(generic_t x, const char* key,
				    int16_t* data, const size_t ndim,
				    const size_t* shape,
				    const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "int", 8*sizeof(int16_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_int32(generic_t x, const char* key,
				    int32_t* data, const size_t ndim,
				    const size_t* shape,
				    const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "int", 8*sizeof(int32_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_int64(generic_t x, const char* key,
				    int64_t* data, const size_t ndim,
				    const size_t* shape,
				    const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "int", 8*sizeof(int64_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_uint8(generic_t x, const char* key,
				    uint8_t* data, const size_t ndim,
				    const size_t* shape,
				    const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "uint", 8*sizeof(uint8_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_uint16(generic_t x, const char* key,
				     uint16_t* data, const size_t ndim,
				     const size_t* shape,
				     const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "uint", 8*sizeof(uint16_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_uint32(generic_t x, const char* key,
				     uint32_t* data, const size_t ndim,
				     const size_t* shape,
				     const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "uint", 8*sizeof(uint32_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_uint64(generic_t x, const char* key,
				     uint64_t* data, const size_t ndim,
				     const size_t* shape,
				     const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "uint", 8*sizeof(uint64_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_float(generic_t x, const char* key,
				    float* data, const size_t ndim,
				    const size_t* shape,
				    const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "float", 8*sizeof(float), ndim, shape, units);
  }
  int generic_map_set_ndarray_double(generic_t x, const char* key,
				     double* data, const size_t ndim,
				     const size_t* shape,
				     const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "float", 8*sizeof(double), ndim, shape, units);
  }
  int generic_map_set_ndarray_long_double(generic_t x, const char* key, long double* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "float", 8*sizeof(long double), ndim, shape, units);
  }
  int generic_map_set_ndarray_complex_float(generic_t x, const char* key, complex_float_t* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "complex", 8*sizeof(complex_float_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_complex_double(generic_t x, const char* key, complex_double_t* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "complex", 8*sizeof(complex_double_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_complex_long_double(generic_t x, const char* key, complex_long_double_t* data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "complex", 8*sizeof(complex_long_double_t), ndim, shape, units);
  }
  int generic_map_set_ndarray_bytes(generic_t x, const char* key, char** data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "bytes", 0, ndim, shape, units);
  }
  int generic_map_set_ndarray_unicode(generic_t x, const char* key, char** data, const size_t ndim, const size_t* shape, const char* units) {
    return generic_map_set_ndarray(x, key, (void*)data, "unicode", 0, ndim, shape, units);
  }
  
  
  void destroy_python(python_t *x) {
    try {
      PyObjMetaschemaType::free_python_t(x);
    } catch(...) {
      ygglog_error("destroy_python: C++ exception thrown.");
    }
  }

  python_t copy_python(python_t x) {
    python_t out = init_python();
    try {
      out = PyObjMetaschemaType::copy_python_t(x);
    } catch(...) {
      ygglog_error("copy_python: C++ exception thrown.");
      CSafe(destroy_python(&out));
    }
    return out;
  }

  void display_python(python_t x) {
    try {
      PyObjMetaschemaType::display_python_t(x);
    } catch(...) {
      ygglog_error("display_python: C++ exception thrown.");
    }
  }

  int skip_va_elements(const dtype_t* dtype, size_t *nargs, va_list_t *ap) {
    try {
      if (dtype == NULL) {
	return 1;
      }
      if (dtype->obj == NULL) {
	return 1;
      }
      MetaschemaType *obj = dtype2class(dtype);
      obj->skip_va_elements(nargs, ap);
    } catch(...) {
      ygglog_error("skip_va_elements: C++ exception thrown.");
      return 1;
    }
    return 0;
  }
  
  int is_empty_dtype(const dtype_t* dtype) {
    if (dtype == NULL) {
      return 1;
    }
    if (dtype->obj == NULL) {
      return 1;
    }
    if (strlen(dtype->type) == 0) {
      return 1;
    }
    try {
      MetaschemaType *obj = dtype2class(dtype);
      if (obj->is_empty())
	return 1;
    } catch(...) {
      ygglog_error("is_empty_dtype: C++ exception thrown.");
      return 1;
    }
    return 0;
  }
  
  const char* dtype_name(const dtype_t* type_struct) {
    try {
      MetaschemaType* type_class = dtype2class(type_struct);
      return type_class->type();
    } catch(...) {
      ygglog_error("dtype_name: C++ exception thrown.");
      return "";
    }
  }

  const char* dtype_subtype(const dtype_t* type_struct) {
    try {
      if (strcmp(type_struct->type, "scalar") != 0) {
	ygglog_throw_error("dtype_subtype: Only scalars have subtype.");
      }
      ScalarMetaschemaType* scalar_class = static_cast<ScalarMetaschemaType*>(type_struct->obj);
      return scalar_class->subtype();
    } catch(...) {
      ygglog_error("dtype_subtype: C++ exception thrown.");
      return "";
    }
  }

  const size_t dtype_precision(const dtype_t* type_struct) {
    try {
      if (strcmp(type_struct->type, "scalar") != 0) {
	ygglog_throw_error("dtype_precision: Only scalars have precision.");
      }
      ScalarMetaschemaType* scalar_class = static_cast<ScalarMetaschemaType*>(type_struct->obj);
      return scalar_class->precision();
    } catch(...) {
      ygglog_error("dtype_precision: C++ exception thrown.");
      return 0;
    }
  };

  int set_dtype_name(dtype_t *dtype, const char* name) {
    if (dtype == NULL) {
      ygglog_error("set_dtype_name: data type structure is NULL.");
      return -1;
    }
    strncpy(dtype->type, name, COMMBUFFSIZ);
    return 0;
  }

  dtype_t* complete_dtype(dtype_t *dtype, const bool use_generic=false) {
    try {
      if (dtype == NULL) {
	return create_dtype(NULL, use_generic);
      } else if ((dtype->obj != NULL) && (strlen(dtype->type) == 0)){
	int ret = set_dtype_name(dtype, dtype_name(dtype));
	if (ret != 0) {
	  ygglog_throw_error("complete_dtype: Failed to set data type name.");
	}
      }
    } catch (...) {
      ygglog_error("complete_dtype: C++ exception thrown.");
      return NULL;
    }
    return dtype;
  }

  int destroy_dtype(dtype_t **dtype) {
    int ret = 0;
    if (dtype != NULL) {
      if (dtype[0] != NULL) {
	if ((dtype[0])->obj != NULL) {
	  try {
	    MetaschemaType *type_class = dtype2class(dtype[0]);
	    ret = destroy_dtype_class_safe(type_class);
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

  dtype_t* create_dtype_empty(const bool use_generic=false) {
    try {
      return create_dtype(NULL, use_generic);
    } catch(...) {
      ygglog_error("create_dtype_empty: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_doc(void* type_doc, const bool use_generic=false) {
    MetaschemaType* obj = NULL;
    try {
      obj = (MetaschemaType*)type_from_doc_c(type_doc, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_doc: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_python(PyObject* pyobj, const bool use_generic=false) {
    MetaschemaType* obj = NULL;
    try {
      obj = type_from_pyobj(pyobj, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_python: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_direct(const bool use_generic=false) {
    DirectMetaschemaType* obj = NULL;
    try {
      obj = new DirectMetaschemaType(use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_direct: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_default(const char* type, const bool use_generic=false) {
    MetaschemaType* obj = NULL;
    try {
      obj = new MetaschemaType(type, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_default: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_scalar(const char* subtype, const size_t precision,
			       const char* units, const bool use_generic=false) {
    ScalarMetaschemaType* obj = NULL;
    try {
      obj = new ScalarMetaschemaType(subtype, precision, units, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_scalar: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_format(const char *format_str,
			       const int as_array = 0,
			       const bool use_generic=false) {
    JSONArrayMetaschemaType* obj = NULL;
    try {
      obj = create_dtype_format_class(format_str, as_array, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_format: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_1darray(const char* subtype, const size_t precision,
				const size_t length, const char* units,
				const bool use_generic=false) {
    OneDArrayMetaschemaType* obj = NULL;
    try {
      obj = new OneDArrayMetaschemaType(subtype, precision, length, units,
					use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_1darray: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_ndarray(const char* subtype, const size_t precision,
				const size_t ndim, const size_t* shape,
				const char* units, const bool use_generic=false) {
    NDArrayMetaschemaType* obj = NULL;
    try {
      std::vector<size_t> shape_vec;
      size_t i;
      for (i = 0; i < ndim; i++) {
	shape_vec.push_back(shape[i]);
      }
      obj = new NDArrayMetaschemaType(subtype, precision, shape_vec, units, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_ndarray: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ndarray_arr(const char* subtype, const size_t precision,
				    const size_t ndim, const int64_t shape[],
				    const char* units, const bool use_generic=false) {
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
    JSONArrayMetaschemaType* obj = NULL;
    try {
      MetaschemaTypeVector items_vec;
      size_t i;
      if ((nitems > 0) && (items == NULL)) {
	ygglog_throw_error("create_dtype_json_array: %d items expected, but the items parameter is NULL.", nitems);
      }
      for (i = 0; i < nitems; i++) {
	MetaschemaType* iitem = dtype2class(items[i]);
	items_vec.push_back(iitem);
      }
      obj = new JSONArrayMetaschemaType(items_vec, "", use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_json_array: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_json_object(const size_t nitems, char** keys,
				    dtype_t** values,
				    const bool use_generic=true) {
    JSONObjectMetaschemaType* obj = NULL;
    try {
      MetaschemaTypeMap properties;
      size_t i;
      if ((nitems > 0) && ((keys == NULL) || (values == NULL))) {
	ygglog_throw_error("create_dtype_json_object: %d items expected, but the keys and/or values parameter is NULL.", nitems);
      }
      for (i = 0; i < nitems; i++) {
	MetaschemaType* iitem = dtype2class(values[i]);
	properties[keys[i]] = iitem;
      }
      obj = new JSONObjectMetaschemaType(properties, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_json_object: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ply(const bool use_generic=false) {
    PlyMetaschemaType* obj = NULL;
    try {
      obj = new PlyMetaschemaType(use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_ply: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_obj(const bool use_generic=false) {
    ObjMetaschemaType* obj = NULL;
    try {
      obj = new ObjMetaschemaType(use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_obj: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ascii_table(const char *format_str, const int as_array,
				    const bool use_generic=false) {
    AsciiTableMetaschemaType* obj = NULL;
    try {
      obj = new AsciiTableMetaschemaType(format_str, as_array, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_ascii_table: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_pyobj(const char* type, const bool use_generic=false) {
    PyObjMetaschemaType* obj = NULL;
    try {
      obj = new PyObjMetaschemaType(type, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_pyobj: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_pyinst(const char* class_name,
			       const dtype_t* args_dtype,
			       const dtype_t* kwargs_dtype,
			       const bool use_generic=true) {
    PyInstMetaschemaType* obj = NULL;
    JSONArrayMetaschemaType* args_type = NULL;
    JSONObjectMetaschemaType* kwargs_type = NULL;
    try {
      if (args_dtype != NULL) {
	args_type = dynamic_cast<JSONArrayMetaschemaType*>(dtype2class(args_dtype));
      }
      if (kwargs_dtype != NULL) {
	kwargs_type = dynamic_cast<JSONObjectMetaschemaType*>(dtype2class(kwargs_dtype));
      }
      obj = new PyInstMetaschemaType(class_name, args_type, kwargs_type, use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_pyinst: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_schema(const bool use_generic=true) {
    SchemaMetaschemaType* obj = NULL;
    try {
      obj = new SchemaMetaschemaType(use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_schema: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_any(const bool use_generic=true) {
    AnyMetaschemaType* obj = NULL;
    try {
      obj = new AnyMetaschemaType(use_generic);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_any: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
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
	head->flags = head->flags | HEAD_TYPE_IN_DATA;
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
      if (head->flags & HEAD_TYPE_IN_DATA) {
	ret = snprintf(*buf, buf_siz, "%s%s%s%s%s", MSG_HEAD_SEP,
		       head_buf.GetString(), MSG_HEAD_SEP,
		       type_buf.GetString(), MSG_HEAD_SEP);
      } else {
	ret = snprintf(*buf, buf_siz, "%s%s%s", MSG_HEAD_SEP,
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
      if (!(head_doc.IsObject()))
	ygglog_throw_error("parse_comm_header: Parsed header document is not an object.");
      dtype_t* dtype;
      if (head_doc.HasMember("datatype")) {
	dtype = create_dtype(type_from_header_doc(head_doc));
      } else if (head_doc.HasMember("type_in_data")) {
	dtype = NULL;
      } else {
	dtype = create_dtype_direct();
      }
      out.dtype = dtype;
      if (!(update_header_from_doc(out, head_doc))) {
	ygglog_error("parse_comm_header: Error updating header from JSON doc.");
	out.flags = out.flags & ~HEAD_FLAG_VALID;
	destroy_dtype(&(out.dtype));
	out.dtype = NULL;
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

  void* dtype_ascii_table(const dtype_t* dtype) {
    try {
      AsciiTableMetaschemaType *table_type = dynamic_cast<AsciiTableMetaschemaType*>(dtype2class(dtype));
      return (void*)(table_type->table());
    } catch (...) {
      ygglog_error("dtype_ascii_table: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* copy_dtype(const dtype_t* dtype) {
    if (dtype == NULL) {
      return NULL;
    }
    dtype_t* out = NULL;
    try {
      MetaschemaType *type = dtype2class(dtype);
      if (type == NULL) {
	ygglog_throw_error("copy_dtype: Could not recover the type class.");
      }
      out = create_dtype(type->copy());
      return out;
    } catch (...) {
      ygglog_error("copy_dtype: C++ exception thrown.");
      destroy_dtype(&out);
      return NULL;
    }
  }

  int update_dtype(dtype_t* dtype1, dtype_t* dtype2) {
    try {
      if ((dtype2 == NULL) || (dtype2->obj == NULL)) {
	ygglog_throw_error("update_dtype: Could not recover type to update from.");
      } else if (dtype1 == NULL) {
	ygglog_throw_error("update_dtype: Could not recover type for update.");
      } else if (dtype1->obj == NULL) {
	MetaschemaType *type2 = dtype2class(dtype2);
	MetaschemaType *type1 = type2->copy();
	dtype1->obj = type1;
	strcpy(dtype1->type, type1->type());
	type1->update_use_generic(dtype1->use_generic);
      } else {
	MetaschemaType *type1 = dtype2class(dtype1);
	MetaschemaType *type2 = dtype2class(dtype2);
	type1->update(type2);
	strcpy(dtype1->type, type1->type());
      }
    } catch (...) {
      ygglog_error("update_dtype: C++ exception thrown.");
      return -1;
    }
    return 0;
  }

  int update_dtype_from_generic_ap(dtype_t* dtype1, size_t nargs,
				   va_list_t ap) {
    if (!(is_empty_dtype(dtype1))) {
      return 0;
    }
    if (!(dtype1->use_generic)) {
      return 0;
    }
    try {
      generic_t gen_arg = get_generic_va(nargs, ap);
      if (!(is_generic_init(gen_arg))) {
	ygglog_throw_error("update_dtype_from_generic_ap: Type expects generic object, but provided object is not generic.");
      } else {
	dtype_t dtype2;
	YggGeneric* ygg_gen_arg = (YggGeneric*)(gen_arg.obj);
	MetaschemaType *type_class = ygg_gen_arg->get_type();
	if (type_class == NULL) {
	  ygglog_throw_error("update_dtype_from_generic_ap: Type in generic class is NULL.");
	}
	dtype2.obj = (void*)(type_class);
	if (set_dtype_name(&dtype2, type_class->type()) < 0) {
	  return -1;
	}
	if (update_dtype(dtype1, &dtype2) < 0) {
	  return -1;
	}
      }
    } catch (...) {
      ygglog_error("update_dtype_from_generic_ap: C++ exception thrown.");
      return -1;
    }
    return 0;
  }
  
  int update_precision_dtype(const dtype_t* dtype,
			     const size_t new_precision) {
    try {
      if (strcmp(dtype->type, "scalar") != 0) {
	ygglog_throw_error("update_precision_dtype: Can only update precision for bytes or unicode scalars.");
      }
      ScalarMetaschemaType *type = dynamic_cast<ScalarMetaschemaType*>(dtype2class(dtype));
      type->set_precision(new_precision);
    } catch (...) {
      ygglog_error("update_precision_dtype: C++ exception thrown.");
      return -1;
    }
    return 0;
  }

  int deserialize_dtype(const dtype_t *dtype, const char *buf, const size_t buf_siz,
			const int allow_realloc, size_t *nargs, va_list_t ap) {
    try {
      MetaschemaType* type = dtype2class(dtype);
      return type->deserialize(buf, buf_siz, allow_realloc, nargs, ap);
    } catch (...) {
      ygglog_error("deserialize_dtype: C++ exception thrown.");
      return -1;
    }
  }

  int serialize_dtype(const dtype_t *dtype, char **buf, size_t *buf_siz,
		      const int allow_realloc, size_t *nargs, va_list_t ap) {
    try {
      MetaschemaType* type = dtype2class(dtype);
      return type->serialize(buf, buf_siz, allow_realloc, nargs, ap);
    } catch (...) {
      ygglog_error("serialize_dtype: C++ exception thrown.");
      return -1;
    }
  }

  void display_dtype(const dtype_t *dtype, const char* indent="") {
    try {
      MetaschemaType* type = dtype2class(dtype);
      type->display(indent);
    } catch(...) {
      ygglog_error("display_dtype: C++ exception thrown.");
    }
  }

  size_t nargs_exp_dtype(const dtype_t *dtype) {
    try {
      MetaschemaType* type = dtype2class(dtype);
      return type->nargs_exp();
    } catch(...) {
      ygglog_error("nargs_exp_dtype: C++ exception thrown.");
    }
    return 0;
  }

}

// Local Variables:
// mode: c++
// End:
