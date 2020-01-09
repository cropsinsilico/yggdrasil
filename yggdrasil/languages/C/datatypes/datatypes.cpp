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
			      const bool use_generic=true) {
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
    case T_ARRAY:
      return new JSONArrayMetaschemaType(type_doc, "", use_generic);
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

  generic_t init_generic() {
    generic_t out;
    out.prefix = prefix_char;
    out.obj = NULL;
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

  int destroy_generic(generic_t* x) {
    int ret = 0;
    if (x != NULL) {
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
    va_list ap_copy;
    va_copy(ap_copy, ap.va);
    out = va_arg(ap_copy, generic_t);
    return out;
  }

  generic_t* get_generic_va_ptr(size_t nargs, va_list_t ap) {
    if (nargs != 1)
      return NULL;
    va_list ap_copy;
    va_copy(ap_copy, ap.va);
    generic_t *out = va_arg(ap_copy, generic_t*);
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
    out = va_arg(ap->va, generic_t);
    return out;
  }

  generic_t* pop_generic_va_ptr(size_t* nargs, va_list_t* ap) {
    if ((*nargs) < 1) {
      ygglog_error("pop_generic_va_ptr: Not enough args (nargs = %lu).", *nargs);
      return NULL;
    }
    (*nargs)--;
    generic_t *out = va_arg(ap->va, generic_t*);
    if (out == NULL) {
      ygglog_error("pop_generic_va_ptr: Object is NULL.");
      return NULL;
    } else if (!(is_generic_init(*out))) {
      ygglog_error("pop_generic_va_ptr: Generic object not intialized.");
      return NULL;
    }
    return out;
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

  int is_empty_dtype(const dtype_t* dtype) {
    if (dtype == NULL) {
      return 1;
    }
    if (dtype->obj == NULL) {
      return 1;
    }
    MetaschemaType *obj = dtype2class(dtype);
    if (obj->is_empty())
      return 1;
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
				    const size_t ndim, const size_t shape[],
				    const char* units, const bool use_generic=false) {
    const size_t* shape_ptr = shape;
    return create_dtype_ndarray(subtype, precision, ndim, shape_ptr, units, use_generic);
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
      if ((size_t)ret > buf_siz) {
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
	destroy_dtype(&(out.dtype));
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
