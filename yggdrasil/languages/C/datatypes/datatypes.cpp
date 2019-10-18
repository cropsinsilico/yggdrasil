#include "../tools.h"
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
      return new MetaschemaType(type_doc);
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
      return new JSONArrayMetaschemaType(items);
    }
    case T_OBJECT: {
      if (!(type_doc.HasMember("properties")))
	ygglog_throw_error("JSONObjectMetaschemaType: Properties missing.");
      if (!(type_doc["properties"].IsObject()))
	ygglog_throw_error("JSONObjectMetaschemaType: Properties must be an object.");
      std::map<const char*, MetaschemaType*, strcomp> properties;
      for (rapidjson::Value::ConstMemberIterator itr = type_doc["properties"].MemberBegin(); itr != type_doc["properties"].MemberEnd(); ++itr) {
	properties[itr->name.GetString()] = type_from_doc(itr->value);
      }
      return new JSONObjectMetaschemaType(properties);
    }
      // Non-standard types
    case T_DIRECT:
      return new DirectMetaschemaType(type_doc);
    case T_1DARRAY:
      return new OneDArrayMetaschemaType(type_doc);
    case T_NDARRAY:
      return new NDArrayMetaschemaType(type_doc);
    case T_SCALAR:
    case T_FLOAT:
    case T_UINT:
    case T_INT:
    case T_COMPLEX:
    case T_BYTES:
    case T_UNICODE:
      return new ScalarMetaschemaType(type_doc);
    case T_PLY:
      return new PlyMetaschemaType(type_doc);
    case T_OBJ:
      return new ObjMetaschemaType(type_doc);
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

JSONArrayMetaschemaType* create_dtype_format_class(const char *format_str,
						   const int as_array = 0) {
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
      items.push_back(new OneDArrayMetaschemaType(isubtype, iprecision, 0));
    } else {
      items.push_back(new ScalarMetaschemaType(isubtype, iprecision, ""));
    }
    beg = end;
  }
  JSONArrayMetaschemaType* out = new JSONArrayMetaschemaType(items, format_str);
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


dtype_t* create_dtype(MetaschemaType* type_class=NULL) {
  dtype_t* out = NULL;
  out = (dtype_t*)malloc(sizeof(dtype_t));
  if (out == NULL) {
    ygglog_throw_error("create_dtype: Failed to malloc for datatype.");
  }
  out->type[0] = '\0';
  out->obj = NULL;
  if (type_class != NULL) {
    try {
      init_dtype_class(out, type_class);
    } catch (...) {
      free(out);
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
    }
  } else {
    ygglog_throw_error("dtype2class: No handler for type '%s'.", dtype->type);
  }
  return NULL;
};


// C exposed functions
extern "C" {

  generic_t* init_generic() {
    try {
      generic_t* out = (generic_t*)malloc(sizeof(generic_t));
      if (out == NULL) {
      	ygglog_throw_error("init_generic: Failed to malloc for generic type structure.");
      }
      out->prefix = '@';
      out->obj = NULL;
      return out;
    } catch(...) {
      ygglog_error("init_generic: C++ exception thrown.");
      return NULL;
    }
  }
  
  generic_t* create_generic(dtype_t* type_struct, void* data, size_t nbytes) {
    try {
      MetaschemaType* type = dtype2class(type_struct);
      YggGeneric* obj = new YggGeneric(type, data, nbytes);
      generic_t* out = init_generic();
      out->obj = (void*)obj;
      return out;
    } catch(...) {
      ygglog_error("create_generic: C++ exception thrown.");
      return NULL;
    }
  }

  int destroy_generic(generic_t** x) {
    int ret = 0;
    if (x != NULL) {
      if (x[0] != NULL) {
	if (x[0]->obj != NULL) {
	  try {
	    YggGeneric* obj = (YggGeneric*)(x[0]->obj);
	    delete obj;
	    x[0]->obj = NULL;
	  } catch (...) {
	    ygglog_error("destroy_generic: C++ exception thrown in destructor for YggGeneric.");
	    ret = -1;
	  }
	}
	free(x[0]);
	x[0] = NULL;
      }
    }
    return ret;
  }

  int copy_generic(generic_t* dst, generic_t* src) {
    try {
      if (dst == NULL) {
	ygglog_throw_error("copy_generic: Destination object not initialized.");
	return -1;
      }
      if (src == NULL) {
	ygglog_throw_error("copy_generic: Source object not initialized.");
	return -1;
      }
      YggGeneric* dst_obj = (YggGeneric*)(dst->obj);
      YggGeneric* src_obj = (YggGeneric*)(src->obj);
      if (src_obj == NULL) {
	ygglog_throw_error("copy_generic: Generic object class is NULL.");
	return -1;
      }
      if (dst_obj != NULL) {
	delete dst_obj;
      }
      dst->obj = src_obj->copy();
      return 0;
    } catch(...) {
      ygglog_error("copy_generic: C++ exception thrown.");
      return -1;
    }
  }

  void display_generic(generic_t* x) {
    try {
      if (is_generic((void*)x)) {
	YggGeneric* x_obj = (YggGeneric*)(x->obj);
	if (x_obj != NULL) {
	  x_obj->display();
	}
      } else if (x != NULL) {
	void** xx = (void**)x;
	if (xx[0] != NULL) {
	  display_generic((generic_t*)(xx[0]));
	}
      }
    } catch (...) {
      ygglog_error("display_generic: C++ exception thrown.");
    }
  }
  
  int is_generic(void* x) {
    if (x != NULL) {
      generic_t* xgen = (generic_t*)x;
      if (xgen->prefix == '@') {
	return 1;
      }
    }
    return 0;
  }

  generic_t* get_generic(void* x, int is_pointer) {
    generic_t* out = NULL;
    if ((is_pointer) && (x != NULL)) {
      void** x2 = (void**)x;
      if (is_generic(x2[0])) {
	out = (generic_t*)(x2[0]);
      }
    } else if (is_generic(x)) {
      out = (generic_t*)x;
    }
    return out;
  }

  generic_t* get_generic_va(size_t nargs, va_list_t ap, int is_pointer) {
    va_list ap_copy;
    va_copy(ap_copy, ap.va);
    void* arg = va_arg(ap_copy, void*);
    return get_generic(arg, is_pointer);
  }

  int is_empty_dtype(const dtype_t* dtype) {
    if (dtype == NULL) {
      return 1;
    }
    if (dtype->obj == NULL) {
      return 1;
    }
    if ((strcmp(dtype_name(dtype), "scalar") == 0) &&
	(strcmp(dtype_subtype(dtype), "bytes") == 0) &&
	(dtype_precision(dtype) == 0)) {
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

  dtype_t* init_dtype(dtype_t *dtype) {
    try {
      if (dtype == NULL) {
	return create_dtype();
      } else if ((dtype->obj != NULL) && (strlen(dtype->type) == 0)){
	int ret = set_dtype_name(dtype, dtype_name(dtype));
	if (ret != 0) {
	  ygglog_throw_error("init_dtype: Failed to set data type name.");
	}
      }
    } catch (...) {
      ygglog_error("init_dtype: C++ exception thrown.");
      return NULL;
    }
    return dtype;
  }

  int destroy_dtype(dtype_t *dtype) {
    int ret = 0;
    if (dtype != NULL) {
      if (dtype->obj != NULL) {
	try {
	  MetaschemaType *type_class = dtype2class(dtype);
	  ret = destroy_dtype_class_safe(type_class);
	} catch (...) {
	  ygglog_error("destroy_dtype: C++ exception thrown in dtype2class.");
	  ret = -1;
	}
      }
      free(dtype);
    }
    return ret;
  }

  dtype_t* create_dtype_empty() {
    try {
      return create_dtype();
    } catch(...) {
      ygglog_error("create_dtype_empty: C++ exception thrown.");
      return NULL;
    }
  }

  dtype_t* create_dtype_direct() {
    DirectMetaschemaType* obj = NULL;
    try {
      obj = new DirectMetaschemaType();
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_direct: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_default(const char* type) {
    MetaschemaType* obj = NULL;
    try {
      obj = new MetaschemaType(type);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_default: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_scalar(const char* subtype, const size_t precision,
			       const char* units) {
    ScalarMetaschemaType* obj = NULL;
    try {
      obj = new ScalarMetaschemaType(subtype, precision, units);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_scalar: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_format(const char *format_str,
			       const int as_array = 0) {
    JSONArrayMetaschemaType* obj = NULL;
    try {
      obj = create_dtype_format_class(format_str, as_array);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_format: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_1darray(const char* subtype, const size_t precision,
				const size_t length, const char* units) {
    OneDArrayMetaschemaType* obj = NULL;
    try {
      obj = new OneDArrayMetaschemaType(subtype, precision, length, units);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_1darray: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }

  dtype_t* create_dtype_ndarray(const char* subtype, const size_t precision,
				const size_t ndim, const size_t* shape,
				const char* units) {
    NDArrayMetaschemaType* obj = NULL;
    try {
      std::vector<size_t> shape_vec;
      size_t i;
      for (i = 0; i < ndim; i++) {
	shape_vec.push_back(shape[i]);
      }
      obj = new NDArrayMetaschemaType(subtype, precision, shape_vec, units);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_ndarray: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ndarray_arr(const char* subtype, const size_t precision,
				    const size_t ndim, const size_t shape[],
				    const char* units) {
    const size_t* shape_ptr = shape;
    return create_dtype_ndarray(subtype, precision, ndim, shape_ptr, units);
  }
  dtype_t* create_dtype_json_array(const size_t nitems, dtype_t** items){
    JSONArrayMetaschemaType* obj = NULL;
    try {
      std::vector<MetaschemaType*> items_vec;
      size_t i;
      for (i = 0; i < nitems; i++) {
	MetaschemaType* iitem = dtype2class(items[i]);
	items_vec.push_back(iitem);
      }
      obj = new JSONArrayMetaschemaType(items_vec);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_json_array: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_json_object(const size_t nitems, const char** keys,
				    dtype_t** values) {
    JSONObjectMetaschemaType* obj = NULL;
    try {
      std::map<const char*, MetaschemaType*, strcomp> properties;
      size_t i;
      for (i = 0; i < nitems; i++) {
	MetaschemaType* iitem = dtype2class(values[i]);
	properties[keys[i]] = iitem;
      }
      obj = new JSONObjectMetaschemaType(properties);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_json_object: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ply() {
    PlyMetaschemaType* obj = NULL;
    try {
      obj = new PlyMetaschemaType();
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_ply: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_obj() {
    ObjMetaschemaType* obj = NULL;
    try {
      obj = new ObjMetaschemaType();
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_obj: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  dtype_t* create_dtype_ascii_table(const char *format_str, const int as_array) {
    AsciiTableMetaschemaType* obj = NULL;
    try {
      obj = new AsciiTableMetaschemaType(format_str, as_array);
      return create_dtype(obj);
    } catch(...) {
      ygglog_error("create_dtype_ascii_table: C++ exception thrown.");
      CSafe(delete obj);
      return NULL;
    }
  }
  int format_comm_header(const comm_head_t head, char *buf, const size_t buf_siz) {
    try {
      // Header
      rapidjson::StringBuffer head_buf;
      rapidjson::Writer<rapidjson::StringBuffer> head_writer(head_buf);
      head_writer.StartObject();
      if (head.dtype != NULL) {
	MetaschemaType* type = dtype2class(head.dtype);
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
      dtype_t* dtype;
      if (head_doc.HasMember("type")) {
	dtype = create_dtype(type_from_doc(head_doc));
      } else {
	dtype = create_dtype_direct();
      }
      out.dtype = dtype;
      if (!(update_header_from_doc(out, head_doc))) {
	ygglog_error("parse_comm_header: Error updating header from JSON doc.");
	out.valid = 0;
	destroy_dtype(out.dtype);
	out.dtype = NULL;
	free(head);
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
      destroy_dtype(out);
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
    try {
      generic_t* gen_arg = get_generic_va(nargs, ap, 0);
      if (gen_arg != NULL) {
	dtype_t dtype2;
	YggGeneric* ygg_gen_arg = (YggGeneric*)(gen_arg->obj);
	MetaschemaType *type_class = ygg_gen_arg->get_type();
	if (type_class == NULL) {
	  ygglog_throw_error("update_dtype_from_generic_ap: Type in generic class is NULL.");
	}
	dtype2.obj = (void*)(type_class);
	if (set_dtype_name(&dtype2, type_class->type()) < 0) {
	  return -1;
	}
	if (dtype1 != NULL) {
	  if (is_empty_dtype(dtype1)) {
	    if (dtype1->obj != NULL) {
	      MetaschemaType *type_class1 = dtype2class(dtype1);
	      if (destroy_dtype_class_safe(type_class1) < 0) {
		return -1;
	      }
	    }
	    dtype1->obj = NULL;
	    strncpy(dtype1->type, "", COMMBUFFSIZ);
	  }
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
      generic_t* gen_arg = get_generic_va(*nargs, ap, 1);
      if (gen_arg != NULL) {
	if (gen_arg->obj == NULL) {
	  gen_arg->obj = (void*)(new YggGeneric(type, NULL));
	}
	return type->deserialize(buf, buf_siz,
				 (YggGeneric*)(gen_arg->obj));
      }
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
      generic_t* gen_arg = get_generic_va(*nargs, ap, 0);
      if (gen_arg != NULL) {
	return type->serialize(buf, buf_siz, allow_realloc,
			       (YggGeneric*)(gen_arg->obj));
      }
      return type->serialize(buf, buf_siz, allow_realloc, nargs, ap);
    } catch (...) {
      ygglog_error("serialize_dtype: C++ exception thrown.");
      return -1;
    }
  }

  void display_dtype(const dtype_t *dtype) {
    try {
      MetaschemaType* type = dtype2class(dtype);
      type->display();
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
