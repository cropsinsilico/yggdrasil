#include "../../tools.h"
#include "MetaschemaType.h"
#include "DirectMetaschemaType.h"
#include "ScalarMetaschemaType.h"
#include "JSONArrayMetaschemaType.h"
#include "JSONObjectMetaschemaType.h"
#include "PlyMetaschemaType.h"
#include "ObjMetaschemaType.h"
#include "AsciiTableMetaschemaType.h"
#include "datatypes.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"


// C++ functions
MetaschemaType* type_from_doc(const rapidjson::Value &type_doc) {
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
      return (new MetaschemaType(type_doc));
      // Enhanced types
    case T_ARRAY: {
      if (!(type_doc.HasMember("items")))
	ygglog_throw_error("JSONArrayMetaschemaType: Items missing.");
      if (!(type_doc["items"].IsArray()))
	ygglog_throw_error("JSONArrayMetaschemaType: Items must be an array.");
      std::vector<MetaschemaType*> items;
      size_t i;
      for (i = 0; i < (size_t)(type_doc["items"].Size()); i++) {
	items.push_back(type_from_doc(type_doc["items"][i]));
      }
      return (new JSONArrayMetaschemaType(items));
    }
    case T_OBJECT: {
      if (!(type_doc.HasMember("properties")))
	ygglog_throw_error("JSONObjectMetaschemaType: Properties missing.");
      if (!(type_doc["properties"].IsObject()))
	ygglog_throw_error("JSONObjectMetaschemaType: Properties must be an object.");
      std::map<const char*, MetaschemaType*, strcomp> properties;
      for (rapidjson::Value::ConstMemberIterator itr = type_doc.MemberBegin(); itr != type_doc.MemberEnd(); ++itr) {
	properties[itr->name.GetString()] = type_from_doc(itr->value);
      }
      return (new JSONObjectMetaschemaType(properties));
      // Non-standard types
    }
    case T_DIRECT:
      return (new DirectMetaschemaType(type_doc));
    case T_1DARRAY:
      return (new OneDArrayMetaschemaType(type_doc));
    case T_NDARRAY:
      return (new NDArrayMetaschemaType(type_doc));
    case T_SCALAR:
    case T_FLOAT:
    case T_UINT:
    case T_INT:
    case T_COMPLEX:
    case T_BYTES:
    case T_UNICODE:
      return (new ScalarMetaschemaType(type_doc));
    case T_PLY:
      return (new PlyMetaschemaType(type_doc));
    case T_OBJ:
      return (new ObjMetaschemaType(type_doc));
    }
  }
  ygglog_throw_error("Could not find class from doc for type '%s'.", type);
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
    head.multipart = 1;
  } else {
    head.multipart = 0;
  }
  // String fields
  const char **n;
  const char *string_fields[] = {"address", "id", "request_id", "response_address",
				 "zmq_reply", "zmq_reply_worker", ""};
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


// C exposed functions
extern "C" {

  const char* get_type_name(MetaschemaType* type_class) {
    if (type_class == NULL) {
      return "";
    }
    try {
      return type_class->type();
    } catch(...) {
      ygglog_error("get_type_name: C++ exception thrown.");
      return "";
    }
  }

  const char* get_type_subtype(MetaschemaType* type_class) {
    try {
      if (strcmp(type_class->type(), "scalar") != 0) {
	ygglog_error("get_type_subtype: Only scalars have subtype.");
	return "";
      }
      ScalarMetaschemaType* scalar_class = (ScalarMetaschemaType*)type_class;
      return scalar_class->subtype();
    } catch(...) {
      ygglog_error("get_type_subtype: C++ exception thrown.");
      return "";
    }
  };

  const size_t get_type_precision(MetaschemaType* type_class) {
    try {
      if (strcmp(type_class->type(), "scalar") != 0) {
	ygglog_error("get_type_precision: Only scalars have precision.");
	return 0;
      }
      ScalarMetaschemaType* scalar_class = (ScalarMetaschemaType*)type_class;
      return scalar_class->precision();
    } catch(...) {
      ygglog_error("get_type_precision: C++ exception thrown.");
      return 0;
    }
  };

  MetaschemaType* get_direct_type() {
    try {
      return (new DirectMetaschemaType()); 
    } catch(...) {
      ygglog_error("get_direct_type: Failed to create type.");
      return NULL;
    }
  }

  MetaschemaType* get_scalar_type(const char* subtype, const size_t precision,
				  const char* units) {
    try {
      return (new ScalarMetaschemaType(subtype, precision, units));
    } catch(...) {
      ygglog_error("get_scalar_type: Failed to create type.");
      return NULL;
    }
  }

  MetaschemaType* get_1darray_type(const char* subtype, const size_t precision,
				   const size_t length, const char* units) {
    try {
      return (new OneDArrayMetaschemaType(subtype, precision, length, units));
    } catch(...) {
      ygglog_error("get_1darray_type: Failed to create type.");
      return NULL;
    }
  }

  MetaschemaType* get_ndarray_type(const char* subtype, const size_t precision,
				   const size_t ndim, const size_t* shape,
				   const char* units) {
    try {
      std::vector<size_t> shape_vec;
      size_t i;
      for (i = 0; i < ndim; i++) {
	shape_vec.push_back(shape[i]);
      }
      return (new NDArrayMetaschemaType(subtype, precision, shape_vec, units));
    } catch(...) {
      ygglog_error("get_ndarray_type: Failed to create type.");
      return NULL;
    }
  }
  MetaschemaType* get_json_array_type(const size_t nitems, MetaschemaType** items){
    try {
      std::vector<MetaschemaType*> items_vec;
      size_t i;
      for (i = 0; i < nitems; i++) {
	items_vec.push_back(items[i]);
      }
      return (new JSONArrayMetaschemaType(items_vec));
    } catch(...) {
      ygglog_error("get_json_array_type: Failed to create type.");
      return NULL;
    }
  }
  MetaschemaType* get_json_object_type(const size_t nitems, const char** keys,
				       MetaschemaType** values) {
    try {
      std::map<const char*, MetaschemaType*, strcomp> properties;
      size_t i;
      for (i = 0; i < nitems; i++) {
	properties[keys[i]] = values[i];
      }
      return (new JSONObjectMetaschemaType(properties));
    } catch(...) {
      ygglog_error("get_json_object_type: Failed to create type.");
      return NULL;
    }
  }
  MetaschemaType* get_ply_type() { 
    try {
      return (new PlyMetaschemaType()); 
    } catch(...) {
      ygglog_error("get_ply_type: Failed to create type.");
      return NULL;
    }
  }
  MetaschemaType* get_obj_type() { 
    try {
      return (new ObjMetaschemaType()); 
    } catch(...) {
      ygglog_error("get_obj_type: Failed to create type.");
      return NULL;
    }
  }
  MetaschemaType* get_ascii_table_type(const char *format_str, const int as_array) {
    try {
      return (new AsciiTableMetaschemaType(format_str, as_array)); 
    } catch(...) {
      ygglog_error("get_ascii_table_type: Failed to create type.");
      return NULL;
    }
  }
  MetaschemaType* get_format_type(const char *format_str,
				  const int as_array = 0) {
    try {
      std::vector<MetaschemaType*> items;
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
	  ygglog_throw_error("get_format_type: find_match returned %d", mres);
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
	  /* } else if (find_match("%.*l[fFeEgG]", ifmt, &sind, &eind)) { */
	  /*   isubtype = "float"; */
	  /*   iprecision = 8 * sizeof(double); */
	  /* } else if (find_match("%.*[fFeEgG]", ifmt, &sind, &eind)) { */
	  /*   isubtype = "float"; */
	  /*   iprecision = 8 * sizeof(float); */
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
	  ygglog_throw_error("get_format_type: Could not parse format string: %s", ifmt);
	}
  ygglog_debug("isubtype = %s, iprecision = %lu, ifmt = %s",
               isubtype, iprecision, ifmt);
	if (as_array == 1) {
	  items.push_back(new OneDArrayMetaschemaType(isubtype, iprecision, 0));
	} else {
	  items.push_back(new ScalarMetaschemaType(isubtype, iprecision, ""));
	}
	beg = end;
      }
      MetaschemaType* out = new JSONArrayMetaschemaType(items, format_str);
      //printf("from format\n");
      //out->display();
      return out;
    } catch(...) {
      ygglog_error("get_format_type: Failed to create type from format.");
      return NULL;
    }
  }
  
  MetaschemaType* type_from_void(const char *type_name, const void *type) {
    try {
      if (type == NULL) {
	return NULL;
      }
      std::map<const char*, int, strcomp> type_map = get_type_map();
      std::map<const char*, int, strcomp>::iterator it = type_map.find(type_name);
      if (it != type_map.end()) {
	switch (it->second) {
	case T_BOOLEAN:
	case T_INTEGER:
	case T_NULL:
	case T_NUMBER:
	case T_STRING:
	  return (MetaschemaType*)type;
	case T_ARRAY:
	  return (JSONArrayMetaschemaType*)type;
	case T_OBJECT:
	  return (JSONObjectMetaschemaType*)type;
	case T_DIRECT:
	  return (DirectMetaschemaType*)type;
	case T_1DARRAY:
	  return (OneDArrayMetaschemaType*)type;
	case T_NDARRAY:
	  return (NDArrayMetaschemaType*)type;
	case T_SCALAR:
	case T_FLOAT:
	case T_UINT:
	case T_INT:
	case T_COMPLEX:
	case T_BYTES:
	case T_UNICODE:
	  return (ScalarMetaschemaType*)type;
	case T_PLY:
	  return (PlyMetaschemaType*)type;
	case T_OBJ:
	  return (ObjMetaschemaType*)type;
	case T_ASCII_TABLE:
	  return (AsciiTableMetaschemaType*)type;
	}
      }
      if (strcmp(type_name, "format") == 0) {
	return get_format_type((char*)type);
      } else {
	MetaschemaType* base = (MetaschemaType*)type;
	const char* new_type = base->type();
	if (strcmp(new_type, type_name) != 0) {
	  return type_from_void(new_type, type);
	} else {
	  ygglog_error("type_from_void: No handler for type '%s'.", type_name);
	  return NULL;
	}
      }
    } catch(...) {
      ygglog_error("type_from_void: C++ exception.");
      return NULL;
    }
  }

  int format_comm_header(const comm_head_t head, char *buf, const size_t buf_siz) {
    try {
      // Header
      rapidjson::StringBuffer head_buf;
      rapidjson::Writer<rapidjson::StringBuffer> head_writer(head_buf);
      head_writer.StartObject();
      if (head.serializer_info != NULL) {
	MetaschemaType* type = type_from_void(head.type, head.serializer_info);
	if (!(type->encode_type_prop(&head_writer))) {
	  return -1;
	}
      }
      head_writer.Key("size");
      head_writer.Int((int)(head.size));
      // Strings
      const char **n;
      const char *string_fields[] = {"address", "id", "request_id", "response_address",
				     "zmq_reply", "zmq_reply_worker", ""};
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
	} else {
	  ygglog_error("format_comm_header: '%s' not handled.", *n);
	  return -1;
	}
	if (strlen(target) > 0) {
	  head_writer.Key(*n);
	  head_writer.String(target);
	}
	n++;
      }
      head_writer.EndObject();
      // Combine
      int ret = snprintf(buf, buf_siz, "%s%s%s",
			 MSG_HEAD_SEP, head_buf.GetString(), MSG_HEAD_SEP);
      if (ret > buf_siz) {
	ygglog_error("format_comm_header: Header exceeds buffer size: '%s%s%s'.",
		     MSG_HEAD_SEP, head_buf.GetString(), MSG_HEAD_SEP);
	return -1;
      }
      ygglog_debug("format_comm_header: Header = '%s'", buf);
      return ret;
    } catch(...) {
      ygglog_error("format_comm_header: C++ exception thrown.");
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
	out.valid = 0;
	if (head != NULL) 
	  free(head);
	return out;
      }
      out.bodybeg = headsiz + 2*strlen(MSG_HEAD_SEP);
      out.bodysiz = buf_siz - out.bodybeg;
      // Handle raw data without header
      if (headsiz == 0) {
	out.multipart = 0;
	out.size = out.bodysiz;
	free(head);
	return out;
      }
      // Parse header
      rapidjson::Document head_doc;
      head_doc.Parse(head, headsiz);
      if (!(head_doc.IsObject()))
	ygglog_throw_error("parse_comm_header: Parsed header document is not an object.");
      MetaschemaType* type;
      if (head_doc.HasMember("type")) {
	type = type_from_doc(head_doc);
      } else {
	type = get_direct_type();
      }
      strncpy(out.type, type->type(), COMMBUFFSIZ);
      out.serializer_info = (void*)type;
      if (!(update_header_from_doc(out, head_doc))) {
	ygglog_error("parse_comm_header: Error updating header from JSON doc.");
	out.valid = 0;
	strncpy(out.type, "", COMMBUFFSIZ);
	out.serializer_info = NULL;
	free(head);
	delete(type);
	return out;
      }
      return out;
    } catch(...) {
      ygglog_error("parse_comm_header: C++ exception thrown.");
      out.valid = 0;
      if (head != NULL)
	free(head);
      return out;
    }
  }

  void* get_ascii_table_from_void(const char* name, const void* info) {
    if (info == NULL) {
      return NULL;
    }
    try {
      AsciiTableMetaschemaType *type = (AsciiTableMetaschemaType*)type_from_void(name, info);
      if (type == NULL) {
	return NULL;
      }
      return (void*)(type->table());
    } catch (...) {
      ygglog_error("get_ascii_table_from_void: C++ exception thrown.");
      return NULL;
    }
  }

  const char* get_type_name_from_void(const char* name, const void* info) {
    try {
      MetaschemaType *type = type_from_void(name, info);
      if (type == NULL) {
	return NULL;
      }
      return type->type();
    } catch(...) {
      ygglog_error("get_type_name_from_void: C++ exception thrown.");
      return NULL;
    }
  }
    
  MetaschemaType* copy_from_void(const char* name, const void* info) {
    if (info == NULL) {
      return NULL;
    }
    try {
      MetaschemaType *type = type_from_void(name, info);
      if (type == NULL) {
	return NULL;
      }
      return type->copy();
    } catch (...) {
      ygglog_error("copy_from_void: C++ exception thrown.");
      return NULL;
    }
  }

  int update_precision_from_void(const char* name, void* info,
				 const size_t new_precision) {
    try {
      MetaschemaType *type = type_from_void(name, info);
      if (type == NULL) {
	ygglog_error("update_precision_from_void: Could not recover type.");
	return -1;
      }
      if (strcmp(type->type(), "scalar") != 0) {
	ygglog_throw_error("update_precision_from_void: Can only update precision for bytes or unicode scalars.");
      }
      ScalarMetaschemaType *scalar_type = (ScalarMetaschemaType*)type;
      scalar_type->set_precision(new_precision);
    } catch (...) {
      ygglog_error("update_precision_from_void: C++ exception thrown.");
      return -1;
    }
    return 0;
  }

  int free_type_from_void(const char* name, void* info) {
    if (info != NULL) {
      try {
	MetaschemaType *type = type_from_void(name, info);
	if (type == NULL) {
	  ygglog_error("free_type_from_void: Could not recover type.");
	  return -1;
	}
	delete type;
      } catch (...) {
	ygglog_error("free_type_from_void: C++ exception thrown.");
	return -1;
      }
    }
    return 0;
  }

  int deserialize_from_void(const char* name, const void* info,
			    const char *buf, const size_t buf_siz,
			    const int allow_realloc, size_t *nargs, va_list_t ap) {
    try {
      MetaschemaType* type = type_from_void(name, info);
      if (type == NULL) {
	ygglog_error("deserialize_from_void: Failed to get type from void.");
	return -1;
      }
      return type->deserialize(buf, buf_siz, allow_realloc, nargs, ap);
    } catch (...) {
      ygglog_error("deserialize_from_void: C++ exception thrown.");
      return -1;
    }
  }

  int serialize_from_void(const char* name, const void* info,
			  char **buf, size_t *buf_siz,
			  const int allow_realloc, size_t *nargs, va_list_t ap) {
    try {
      MetaschemaType* type = type_from_void(name, info);
      if (type == NULL) {
	ygglog_error("serialize_from_void: Failed to get type from void.");
	return -1;
      }
      return type->serialize(buf, buf_siz, allow_realloc, nargs, ap);
    } catch (...) {
      ygglog_error("serialize_from_void: C++ exception thrown.");
      return -1;
    }
  }

  void display_from_void(const char* name, const void* info) {
    try {
      MetaschemaType* type = type_from_void(name, info);
      if (type == NULL) {
	ygglog_error("display_from_void: Failed to get type from void.");
	return;
      }
      type->display();
    } catch(...) {
      ygglog_error("display_from_void: C++ exception thrown.");
    }
  }

  size_t nargs_exp_from_void(const char* name, const void* info) {
    try {
      MetaschemaType* type = type_from_void(name, info);
      if (type == NULL) {
	ygglog_error("nargs_exp_from_void: Failed to get type from void.");
	return 0;
      }
      return type->nargs_exp();
    } catch(...) {
      ygglog_error("nargs_exp_from_void: C++ exception thrown.");
    }
    return 0;
  }
  
}

// Local Variables:
// mode: c++
// End:
