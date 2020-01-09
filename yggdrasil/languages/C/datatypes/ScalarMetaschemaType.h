#ifndef SCALAR_METASCHEMA_TYPE_H_
#define SCALAR_METASCHEMA_TYPE_H_

#include <vector>
#include <cstring>

#include "../tools.h"
#include "../serialize/base64.h"
#include "MetaschemaType.h"
#include "JSONArrayMetaschemaType.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


/*!
  @brief Base class for scalar type definition.

  The ScalarMetaschemaType provides basic functionality for encoding/decoding
  scalar datatypes from/to JSON style strings.
 */
class ScalarMetaschemaType : public MetaschemaType {
public:
  /*!
    @brief Constructor for ScalarMetaschemaType.
    @param[in] subtype const character pointer to the name of the subtype.
    @param[in] precision size_t Type precision in bits.
    @param[in] units const char * (optional) Type units.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  ScalarMetaschemaType(const char *subtype, const size_t precision,
		       const char *units="", const bool use_generic=false) :
    MetaschemaType("scalar", use_generic), subtype_((const char*)malloc(STRBUFF)), subtype_code_(-1),
    precision_(precision), units_((const char*)malloc(STRBUFF)), cast_precision_(0) {
    if (subtype_ == NULL) {
      ygglog_throw_error("ScalarMetaschemaType: Failed to malloc subtype.");
    }
    if (units_ == NULL) {
      ygglog_throw_error("ScalarMetaschemaType: Failed to malloc units.");
    }
    if (precision_ == 0)
      _variable_precision = true;
    else
      _variable_precision = false;
    update_subtype(subtype, true);
    update_units(units, true);
  }
  /*!
    @brief Constructor for ScalarMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  ScalarMetaschemaType(const rapidjson::Value &type_doc,
		       const bool use_generic=false) :
    MetaschemaType(type_doc, use_generic), subtype_((const char*)malloc(STRBUFF)), subtype_code_(-1),
    precision_(0), units_((const char*)malloc(STRBUFF)), cast_precision_(0) {
    if (subtype_ == NULL) {
      ygglog_throw_error("ScalarMetaschemaType: Failed to malloc subtype.");
    }
    if (units_ == NULL) {
      ygglog_throw_error("ScalarMetaschemaType: Failed to malloc units.");
    }
    switch (type_code()) {
    case T_1DARRAY:
    case T_NDARRAY:
    case T_SCALAR:
      // Subtype
      if (!(type_doc.HasMember("subtype"))) {
	ygglog_throw_error("ScalarMetaschemaType: %s type must include 'subtype'.", type());
      }
      if (!(type_doc["subtype"].IsString())) {
	ygglog_throw_error("ScalarMetaschemaType: 'subtype' value must be a string.");
      }
      update_subtype(type_doc["subtype"].GetString(), true);
      break;
    default:
      update_subtype(type(), true);
      update_type("scalar");
    }
    // Precision
    if (!(type_doc.HasMember("precision")))
      ygglog_throw_error("ScalarMetaschemaType: Precision missing.");
    if (type_doc["precision"].IsInt()) {
      set_precision(type_doc["precision"].GetInt(), true);
    } else if (type_doc["precision"].IsDouble()) {
      set_precision((size_t)(type_doc["precision"].GetDouble(), true));
    } else {
      ygglog_throw_error("ScalarMetaschemaType: Precision must be a number.");
    }
    // Units
    if (type_doc.HasMember("units")) {
      if (!type_doc["units"].IsString())
	ygglog_throw_error("ScalarMetaschemaType: Units must be a string.");
      update_units(type_doc["units"].GetString(), true);
    } else {
      update_units("", true);
    }
    // Set variable precision
    if (precision_ == 0)
      _variable_precision = true;
    else
      _variable_precision = false;
  }
  /*!
    @brief Constructor for ScalarMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  ScalarMetaschemaType(PyObject* pyobj, const bool use_generic=false) :
    MetaschemaType(pyobj, use_generic), subtype_((const char*)malloc(STRBUFF)), subtype_code_(-1),
    precision_(0), units_((const char*)malloc(STRBUFF)), cast_precision_(0) {
    // Subtype
    char subtype[STRBUFF] = "";
    get_item_python_dict_c(pyobj, "subtype", subtype,
			   "ScalarMetaschemaType: subtype: ",
			   T_STRING, STRBUFF);
    update_subtype(subtype, true);
    // Precision
    size_t precision = 0;
    get_item_python_dict_c(pyobj, "precision", &precision,
			   "ScalarMetaschemaType: precision: ",
			   T_INT, sizeof(size_t)*8);
    set_precision(precision, true);
    // Units
    char units[STRBUFF] = "";
    get_item_python_dict_c(pyobj, "units", units,
			   "ScalarMetaschemaType: units: ",
			   T_STRING, STRBUFF, true);
    update_units(units, true);
    // Set variable precision
    if (precision_ == 0)
      _variable_precision = true;
    else
      _variable_precision = false;
  }
  /*!
    @brief Copy constructor.
    @param[in] other ScalarMetaschemaType* Instance to copy.
   */
  ScalarMetaschemaType(const ScalarMetaschemaType &other) :
    ScalarMetaschemaType(other.subtype(), other.precision(),
			 other.units(), other.use_generic()) {}
  /*!
    @brief Destructor for ScalarMetaschemaType.
    Free the type string malloc'd during constructor.
   */
  virtual ~ScalarMetaschemaType() {
    free((char*)subtype_);
    free((char*)units_);
  }
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  virtual bool operator==(const MetaschemaType &Ref) const override {
    if (!(MetaschemaType::operator==(Ref)))
      return false;
    const ScalarMetaschemaType* pRef = dynamic_cast<const ScalarMetaschemaType*>(&Ref);
    if (!pRef)
      return false;
    if (strcmp(subtype_, pRef->subtype()) != 0)
      return false;
    if (subtype_code_ != pRef->subtype_code())
      return false;
    if ((!(_variable_precision)) && (precision_ != pRef->precision()))
      return false;
    if (strcmp(units_, pRef->units()) != 0)
      return false;
    return true;
  }
  /*!
    @brief Determine if the datatype is effectively empty.
    @returns bool true if the datatype is empty, false otherwise.
   */
  bool is_empty() const override {
    if ((type_code() == T_SCALAR)
	&& (subtype_code_ == T_BYTES)
	&& (precision_ == 0))
      return true;
    return false;
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new ScalarMetaschemaType instance with the same data.
   */
  ScalarMetaschemaType* copy() const override { return (new ScalarMetaschemaType(subtype_, precision_, units_, use_generic())); }
  /*!
    @brief Print information about the type to stdout.
    @param[in] indent char* Indentation to add to display output.
  */
  void display(const char* indent="") const override {
    MetaschemaType::display(indent);
    printf("%s%-15s = %s\n", indent, "subtype", subtype_);
    printf("%s%-15s = %d\n", indent, "subtype_code", subtype_code_);
    printf("%s%-15s = %zu\n", indent, "precision", precision_);
    printf("%s%-15s = %s\n", indent, "units", units_);
  }
  /*!
    @brief Get type information as a Python dictionary.
    @returns PyObject* Python dictionary.
   */
  PyObject* as_python_dict() const override {
    PyObject* out = MetaschemaType::as_python_dict();
    set_item_python_dict_c(out, "subtype", subtype_,
			   "ScalarMetaschemaType::as_python_dict: ",
			   T_STRING, STRBUFF);
    set_item_python_dict_c(out, "precision", &precision_,
			   "ScalarMetaschemaType::as_python_dict: ",
			   T_INT, sizeof(size_t)*8);
    set_item_python_dict_c(out, "units", units_,
			   "ScalarMetaschemaType::as_python_dict: ",
			   T_STRING, STRBUFF);
    return out;
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(const YggGeneric* data, const char* indent="") const override {
    size_t i;
    if (data == NULL) {
      ygglog_throw_error("ScalarMetaschemaType::display_generic: Generic object is NULL.");
    }
    size_t bytes_precision = (data->get_nbytes())/(data->get_nelements());
    std::cout << indent;
    switch (subtype_code_) {
    case T_INT: {
      switch (precision_) {
      case 8: {
	int8_t* arg = (int8_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      case 16: {
	int16_t* arg = (int16_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      case 32: {
	int32_t* arg = (int32_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      case 64: {
	int64_t* arg = (int64_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      default: {
	ygglog_error("ScalarMetaschemaType::display_generic: Unsupported integer precision '%lu'.",
		     precision_);
	return;
      }
      }
      break;
    }
    case T_UINT: {
      switch (precision_) {
      case 8: {
	uint8_t* arg = (uint8_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      case 16: {
	uint16_t* arg = (uint16_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      case 32: {
	uint32_t* arg = (uint32_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      case 64: {
	uint64_t* arg = (uint64_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      }
      default: {
	ygglog_error("ScalarMetaschemaType::display_generic: Unsupported unsigned integer precision '%lu'.",
		     precision_);
	return;
      }
      }
      break;
    }
    case T_FLOAT: {
      if (sizeof(float) == bytes_precision) {
	float* arg = (float*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      } else if (sizeof(double) == bytes_precision) {
	double* arg = (double*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      } else if (sizeof(long double) == bytes_precision) {
	long double* arg = (long double*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i] << " ";
	std::cout << std::endl;
	return;
      } else {
	ygglog_error("ScalarMetaschemaType::display_generic: Unsupported float precision '%lu bit' (%lu bytes).",
		     precision_, bytes_precision);
	return;
      }
      break;
    }
    case T_COMPLEX: {
      if (sizeof(float) == (bytes_precision / 2)) {
#ifdef _WIN32
	complex_double_t* arg = (complex_double_t*)(data->get_data());
#else
	complex_float_t* arg = (complex_float_t*)(data->get_data());
#endif
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i].re << "+" << arg[i].im << "j ";
	std::cout << std::endl;
	return;
      } else if (sizeof(double) == (bytes_precision / 2)) {
	complex_double_t* arg = (complex_double_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i].re << "+" << arg[i].im << "j ";
	std::cout << std::endl;
	return;
      } else if (sizeof(long double) == (bytes_precision / 2)) {
	complex_long_double_t* arg = (complex_long_double_t*)(data->get_data());
	for (i = 0; i < data->get_nelements(); i++)
	  std::cout << arg[i].re << "+" << arg[i].im << "j ";
	std::cout << std::endl;
	return;
      } else {
	ygglog_error("ScalarMetaschemaType::display_generic: Unsupported complex precision '%lu'.",
		     precision_);
	return;
      }
      break;
    }
    case T_BYTES: {
      // TODO: Handle array of char arrays
      char* arg = (char*)(data->get_data());
      std::cout << arg << std::endl;
      return;
    }
    case T_UNICODE: {
      // TODO: Handle array of char arrays
      char* arg = (char*)(data->get_data());
      for (i = 0; i < data->get_nbytes(); i+=4) {
	std::cout << arg + i;
      }
      std::cout << std::endl;
      return;
    }
    default: {
      ygglog_error("ScalarMetaschemaType::display_generic: Unsupported subtype '%s'.",
		   subtype_);
      return;
    }
    }
  }
  /*!
    @brief Check that the subtype is correct and get the corresponding code.
    @returns int Type code for the instance's subtype.
   */
  int check_subtype() const {
    std::map<const char*, int, strcomp> type_map = get_type_map();
    std::map<const char*, int, strcomp>::iterator it = type_map.find(subtype_);
    if (it == type_map.end()) {
      ygglog_throw_error("ScalarMetaschemaType: Unsupported subtype '%s'.", subtype_);
    }
    return it->second;
  }
  /*!
    @brief Get the subtype code.
    @returns const int Subtype code.
   */
  const int subtype_code() const { return subtype_code_; }
  /*!
    @brief Get the subtype string.
    @returns const char pointer to the subtype string.
   */
  const char* subtype() const { return subtype_; }
  /*!
    @brief Get the type precision.
    @returns size_t Type precision in bytes.
   */
  const size_t precision() const { return precision_; }
  /*!
    @brief Get the type units.
    @returns const char* Type units string.
   */
  const char* units() const { return units_; }
  /*!
    @brief Get the size of the type in bits.
    @returns size_t Type size.
   */
  const size_t nbits() const {
    return precision_ * nelements();
  }
  /*!
    @brief Get the size of the type in bytes.
    @returns size_t Type size.
   */
  const size_t nbytes() const override {
    return nbits() / 8;
  }
  /*!
    @brief Get the number of bytes occupied by a variable of the type in a variable argument list.
    @returns std::vector<size_t> Number of bytes/variables occupied by the type.
   */
  std::vector<size_t> nbytes_va_core() const override {
    std::vector<size_t> out;
    if (!(use_generic())) {
      switch (type_code()) {
      case T_1DARRAY:
      case T_NDARRAY: {
	out.push_back(sizeof(unsigned char*));
	return out;
      }
      case T_SCALAR: {
	switch (subtype_code_) {
	case T_BYTES:
	case T_UNICODE: {
	  out.push_back(sizeof(char*));
	  out.push_back(sizeof(size_t));
	  return out;
	}
	}
      }
      }
    }
    return MetaschemaType::nbytes_va_core();
  }
  /*!
    @brief Determine the dimensions of the equivalent numpy array.
    @param[in, out] nd int* Address of integer where number of dimensions should be stored.
    @param[in, out] dims npy_intp** Address of pointer to memory where dimensions should be stored.
   */
  virtual void numpy_dims(int *nd, npy_intp **dims) const {
    nd[0] = 1;
    npy_intp *idims = (npy_intp*)realloc(dims[0], sizeof(npy_intp));
    if (idims == NULL) {
      ygglog_throw_error("ScalarMetaschemaType::numpy_dims: Failed to realloc dims array.");
    }
    idims[0] = 1;
    dims[0] = idims;
  }
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override {
    if (strcmp(new_info->type(), "array") == 0) {
      const JSONArrayMetaschemaType* new_info_array = dynamic_cast<const JSONArrayMetaschemaType*>(new_info);
      if (new_info_array->nitems() == 1) {
	update(new_info_array->items()[0]);
	return;
      }
    }
    MetaschemaType::update(new_info);
    const ScalarMetaschemaType* new_info_scalar = dynamic_cast<const ScalarMetaschemaType*>(new_info);
    update_subtype(new_info_scalar->subtype());
    if ((strcmp(type(), "scalar") == 0) &&
	((strcmp(subtype(), "bytes") == 0) ||
	 (strcmp(subtype(), "unicode") == 0))) {
      _variable_precision = true;
    }
    set_precision(new_info_scalar->precision());
    update_units(new_info_scalar->units());
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  virtual size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    size_t out = MetaschemaType::update_from_serialization_args(nargs, ap);
    if (use_generic())
      return out;
    size_t bytes_precision = nbytes();
    switch (type_code()) {
    case T_SCALAR: {
      switch (subtype_code_) {
      case T_INT: {
	switch (precision_) {
	case 8:
	case 16: {
	  va_arg(ap.va, int);
	  break;
	}
	case 32: {
	  va_arg(ap.va, int32_t);
	  break;
	}
	case 64: {
	  va_arg(ap.va, int64_t);
	  break;
	}
	}
	out = out + 1;
	break;
      }
      case T_UINT: {
	switch (precision_) {
	case 8:
	case 16: {
	  va_arg(ap.va, unsigned int);
	  break;
	}
	case 32: {
	  va_arg(ap.va, uint32_t);
	  break;
	}
	case 64: {
	  va_arg(ap.va, uint64_t);
	  break;
	}
	}
	out = out + 1;
	break;
      }
      case T_FLOAT: {
	if (sizeof(float) == bytes_precision) {
	  va_arg(ap.va, double);
	} else if (sizeof(double) == bytes_precision) {
	  va_arg(ap.va, double);
	} else if (sizeof(long double) == bytes_precision) {
	  va_arg(ap.va, long double);
	}
	out = out + 1;
	break;
      }
      case T_COMPLEX: {
	if (sizeof(float) == (bytes_precision / 2)) {
	  va_arg(ap.va, complex_float_t);
	} else if (sizeof(double) == (bytes_precision / 2)) {
	  va_arg(ap.va, complex_double_t);
	} else if (sizeof(long double) == (bytes_precision / 2)) {
	  va_arg(ap.va, complex_long_double_t);
	}
	out = out + 1;
	break;
      }
      case T_BYTES:
      case T_UNICODE: {
	if (_variable_precision) {
	  char* arg0 = va_arg(ap.va, char*);
	  UNUSED(arg0); // Parameter extract to get next
	  const size_t arg0_siz = va_arg(ap.va, size_t);
	  set_precision(8 * arg0_siz);
	} else {
	  va_arg(ap.va, char*);
	  va_arg(ap.va, size_t);
	}
	out = out + 2;
	break;
      }
      }
    }
    }
    return out;
  }
  /*!
    @brief Update the instance's type.
    @param[in] new_type const char * String for new type.
   */
  void update_type(const char* new_type) override {
    MetaschemaType::update_type(new_type);
    if (strcmp(type(), "scalar") == 0) {
      _variable_precision = false;
    }
  }
  /*!
    @brief Update the instance's subtype.
    @param[in] new_subtype const char * String for new subtype.
   */
  void update_subtype(const char* new_subtype, bool force=false) {
    if ((!(force)) && (strcmp(subtype_, new_subtype) != 0)) {
      ygglog_throw_error("ScalarMetaschemaType::update_subtype: Cannot update subtype from %s to subtype %s.",
    			 subtype_, new_subtype);
    }
    char **subtype_modifier = const_cast<char**>(&subtype_);
    strncpy(*subtype_modifier, new_subtype, STRBUFF);
    int* subtype_code_modifier = const_cast<int*>(&subtype_code_);
    *subtype_code_modifier = check_subtype();
  }
  /*!
    @brief Update the instance's units.
    @param[in] new_units const char * String for new units.
   */
  void update_units(const char* new_units, bool force=false) {
    if ((!(force)) && (strcmp(units_, new_units) != 0)) {
      if (strlen(new_units) == 0) {
	return;
      } else if (strlen(units_) == 0) {
	// pass
      } else {
	ygglog_throw_error("ScalarMetaschemaType::update_units: Cannot update units %s to %s.",
			   units_, new_units);
      }
    }
    char **units_modifier = const_cast<char**>(&units_);
    strncpy(*units_modifier, new_units, STRBUFF);
  }
  /*!
    @brief Update the instance's precision.
    @param[in] new_precision size_t New precision.
   */
  void set_precision(const size_t new_precision, bool force=false) {
    if (precision_ != new_precision) {
      if (!(force)) {
	if (precision_ == 0) {
	  // Pass
	} else if (_variable_precision) {
	  // Pass
	} else if ((strcmp(subtype(), "float") == 0) &&
	    ((precision_ == 32) || (precision_ == 64)) &&
	    ((new_precision == 32) || (new_precision == 64)) &&
	    (strcmp(type(), "1darray") != 0) &&
	    (strcmp(type(), "ndarray") != 0)) {
	  if (cast_precision_ == 0) {
	    cast_precision_ = precision_;
	  }
	} else {
	  ygglog_throw_error("ScalarMetaschemaType::set_precision: Cannot update precision from %ld to %ld for %s of subtype %s.",
			     precision_, new_precision, type(), subtype());
	}
      }
      size_t *precision_modifier = const_cast<size_t*>(&precision_);
      *precision_modifier = new_precision;
    }
    // if ((strcmp(subtype_, "bytes") != 0) &&
    // 	(strcmp(subtype_, "unicode") != 0)) {
    //   ygglog_throw_error("ScalarMetaschemaType::set_precision: Variable precision only allowed for bytes and unicode, not '%s'.", subtype_);
    // }
    // size_t *precision_modifier = const_cast<size_t*>(&precision_);
    // *precision_modifier = new_precision;
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  virtual size_t nargs_exp() const override {
    switch (subtype_code_) {
    case T_BYTES:
    case T_UNICODE: {
      if (strcmp(type(), "scalar") == 0) {
	return 2;
      }
    }
    }
    return 1;
  }    
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject* pyobj) const override {
    YggGeneric* cobj = new YggGeneric(this, NULL, 0);
    void** data = cobj->get_data_pointer();
    if ((size_t)(PyArray_NBYTES(pyobj)) != nbytes()) {
      ygglog_throw_error("ScalarMetaschemaType::python2c: Python object has a size of %lu bytes, but %lu were expected.",
			 PyArray_NBYTES(pyobj), nbytes());
    }
    void* idata = (void*)realloc(data[0], nbytes());
    if (data == NULL) {
      ygglog_throw_error("ScalarMetaschemaType::python2c: Failed to realloc data.");
    }
    memcpy(idata, PyArray_DATA(pyobj), nbytes());
    data[0] = idata;
    return cobj;
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric* cobj) const override {
    initialize_python("ScalarMetaschemaType::c2python: ");
    int nd = 1;
    npy_intp* dims = NULL;
    numpy_dims(&nd, &dims);
    int np_type = -1;
    void* data = cobj->copy_data();
    if (data == NULL) {
      ygglog_throw_error("ScalarMetaschemaType::c2python: Data pointer is NULL.");
    }
    size_t itemsize = precision_ / 8;
    int flags = NPY_OWNDATA;
    switch (subtype_code_) {
    case T_INT: {
      switch (precision_) {
      case 8: {
	np_type = NPY_INT8;
	break;
      }
      case 16: {
	np_type = NPY_INT16;
	break;
      }
      case 32: {
	np_type = NPY_INT32;
	break;
      }
      case 64: {
	np_type = NPY_INT64;
	break;
      }
      default: {
	ygglog_throw_error("ScalarMetaschemaType::c2python: Unsupported integer precision '%lu'.",
			   precision_);
      }
      }
      break;
    }
    case T_UINT: {
      switch (precision_) {
      case 8: {
	np_type = NPY_UINT8;
	break;
      }
      case 16: {
	np_type = NPY_UINT16;
	break;
      }
      case 32: {
	np_type = NPY_UINT32;
	break;
      }
      case 64: {
	np_type = NPY_UINT64;
	break;
      }
      default: {
	ygglog_throw_error("ScalarMetaschemaType::c2python: Unsupported unsigned integer precision '%lu'.",
			   precision_);
      }
      }
      break;
    }
    case T_FLOAT: {
      switch (precision_) {
      case 16: {
	np_type = NPY_FLOAT16;
	break;
      }
      case 32: {
	np_type = NPY_FLOAT32;
	break;
      }
      case 64: {
	np_type = NPY_FLOAT64;
	break;
      }
      default: {
	ygglog_throw_error("ScalarMetaschemaType::c2python: Unsupported float precision '%lu'.",
			   precision_);
      }
      }
      break;
    }
    case T_COMPLEX: {
      switch (precision_) {
      case 64: {
	np_type = NPY_COMPLEX64;
	break;
      }
      case 128: {
	np_type = NPY_COMPLEX128;
	break;
      }
      default: {
	ygglog_throw_error("ScalarMetaschemaType::c2python: Unsupported complex precision '%lu'.",
			   precision_);
      }
      }
      break;
    }
    case T_BYTES: {
      np_type = NPY_BYTE;
      break;
    }
    case T_UNICODE: {
      np_type = NPY_UNICODE;
      break;
    }
    default: {
      ygglog_throw_error("ScalarMetaschemaType::c2python: Unsupported subtype '%s'.",
			 subtype_);
    }
    }
    PyObject* pyobj = PyArray_New(&PyArray_Type, nd, dims, np_type,
    				  nullptr, data, (int)itemsize, flags, nullptr);
    if (pyobj == NULL) {
      ygglog_throw_error("MetaschemaType::c2python: Creation of Numpy array failed.");
    }
    if (dims != NULL)
      free(dims);
    return pyobj;
  }

  // Encoding
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const override {
    if (!MetaschemaType::encode_type_prop(writer)) { return false; }
    writer->Key("subtype");
    writer->String(subtype_, (rapidjson::SizeType)strlen(subtype_));
    writer->Key("precision");
    writer->Int((rapidjson::SizeType)precision_);
    if (strlen(units_) == 0) {
      writer->Key("units");
      writer->String("");
    } else {
      writer->Key("units");
      writer->String(units_, (rapidjson::SizeType)strlen(units_));
    }
    return true;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in,out] nargs size_t * Pointer to the number of arguments contained in
    ap. On return it will be set to the number of arguments used.
    @param[in] ap va_list_t Variable number of arguments that should be encoded
    as a JSON string.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) const override {
    size_t bytes_precision = nbytes();
    unsigned char* arg = (unsigned char*)malloc(bytes_precision + 1);
    if (arg == NULL) {
      ygglog_error("ScalarMetaschemaType::encode_data: Failed to malloc for %lu bytes (%lu elements w/ precison of %lu bits).",
		   bytes_precision + 1, nelements(), precision());
      return false;
    }
    switch (type_code()) {
    case T_1DARRAY:
    case T_NDARRAY: {
      unsigned char* arg0 = va_arg(ap.va, unsigned char*);
      if (nelements() == 0) {
	ygglog_error("ScalarMetaschemaType::encode_data: Array types require the number of elements be non-zero.");
	return false;
      }
      memcpy(arg, arg0, bytes_precision);
      break;
    }
    case T_SCALAR: {
      switch (subtype_code_) {
      case T_INT: {
	switch (precision_) {
	case 8: {
	  int8_t arg0 = (int8_t)va_arg(ap.va, int);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	case 16: {
	  int16_t arg0 = (int16_t)va_arg(ap.va, int);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	case 32: {
	  int32_t arg0 = va_arg(ap.va, int32_t);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	case 64: {
	  int64_t arg0 = va_arg(ap.va, int64_t);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	default: {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported integer precision '%lu'.",
		       precision_);
	  return false;
	}
	}
	break;
      }
      case T_UINT: {
	switch (precision_) {
	case 8: {
	  uint8_t arg0 = (uint8_t)va_arg(ap.va, unsigned int);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	case 16: {
	  uint16_t arg0 = (uint16_t)va_arg(ap.va, unsigned int);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	case 32: {
	  uint32_t arg0 = va_arg(ap.va, uint32_t);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	case 64: {
	  uint64_t arg0 = va_arg(ap.va, uint64_t);
	  memcpy(arg, &arg0, bytes_precision);
	  break;
	}
	default: {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported unsigned integer precision '%lu'.",
		       precision_);
	  return false;
	}
	}
	break;
      }
      case T_FLOAT: {
	if (sizeof(float) == bytes_precision) {
	  float arg0 = (float)va_arg(ap.va, double);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(double) == bytes_precision) {
	  double arg0 = va_arg(ap.va, double);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(long double) == bytes_precision) {
	  long double arg0 = va_arg(ap.va, long double);
	  memcpy(arg, &arg0, bytes_precision);
	} else {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported float precision '%lu'.",
		       precision_);
	  return false;
	}
	break;
      }
      case T_COMPLEX: {
	if (sizeof(float) == (bytes_precision / 2)) {
    complex_float_t arg0 = (complex_float_t)va_arg(ap.va, complex_float_t);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(double) == (bytes_precision / 2)) {
	  complex_double_t arg0 = va_arg(ap.va, complex_double_t);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(long double) == (bytes_precision / 2)) {
	  complex_long_double_t arg0 = va_arg(ap.va, complex_long_double_t);
	  memcpy(arg, &arg0, bytes_precision);
	} else {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported complex precision '%lu'.",
		       precision_);
	  return false;
	}
	break;
      }
      case T_BYTES:
      case T_UNICODE: {
	char* arg0 = va_arg(ap.va, char*);
	const size_t arg0_siz = va_arg(ap.va, size_t);
	int allow_realloc = (int)_variable_precision;
	(*nargs)--;
	size_t arg_siz = bytes_precision + 1;
	int ret = copy_to_buffer(arg0, arg0_siz, (char**)(&arg), arg_siz,
				 allow_realloc);
	if (ret < 0) {
	  ygglog_error("ScalarMetaschemaType::encode_data: Failed to copy bytes/unicode variable to buffer.");
	  free(arg);
	  return false;
	}
	break;
      }
      default: {
	ygglog_error("ScalarMetaschemaType::encode_data: Unsupported subtype '%s'.",
		     subtype_);
	return false;
      }
      }
    }
    }
    (*nargs)--;
    size_t encoded_len = 0;
    unsigned char* encoded_bytes = base64_encode(arg, nbytes(), &encoded_len);
    bool out = writer->String((char*)encoded_bytes, (rapidjson::SizeType)encoded_len);
    free(arg);
    free(encoded_bytes);
    return out;
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGeneric* x) const override {
    size_t nargs = 1;
    size_t bytes_precision = nbytes();
    switch (type_code()) {
    case T_1DARRAY:
    case T_NDARRAY: {
      void* arg = x->get_data();
      return MetaschemaType::encode_data(writer, &nargs, arg);
    }
    case T_SCALAR: {
      switch (subtype_code_) {
      case T_INT: {
	switch (precision_) {
	case 8: {
	  int8_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	case 16: {
	  int16_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	case 32: {
	  int32_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	case 64: {
	  int64_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	default: {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported integer precision '%lu'.",
		       precision_);
	  return false;
	}
	}
	break;
      }
      case T_UINT: {
	switch (precision_) {
	case 8: {
	  uint8_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	case 16: {
	  uint16_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	case 32: {
	  uint32_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	case 64: {
	  uint64_t arg = 0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	}
	default: {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported unsigned integer precision '%lu'.",
		       precision_);
	  return false;
	}
	}
	break;
      }
      case T_FLOAT: {
	if (sizeof(float) == bytes_precision) {
	  float arg = 0.0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	} else if (sizeof(double) == bytes_precision) {
	  double arg = 0.0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	} else if (sizeof(long double) == bytes_precision) {
	  long double arg = 0.0;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	} else {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported float precision '%lu'.",
		       precision_);
	  return false;
	}
	break;
      }
      case T_COMPLEX: {
	if (sizeof(float) == (bytes_precision / 2)) {
	  complex_float_t arg;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	} else if (sizeof(double) == (bytes_precision / 2)) {
	  complex_double_t arg;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	} else if (sizeof(long double) == (bytes_precision / 2)) {
	  complex_long_double_t arg;
	  x->get_data(arg);
	  return MetaschemaType::encode_data(writer, &nargs, arg);
	} else {
	  ygglog_error("ScalarMetaschemaType::encode_data: Unsupported complex precision '%lu'.",
		       precision_);
	  return false;
	}
	break;
      }
      case T_BYTES:
      case T_UNICODE: {
	nargs = 2;
	char* arg = NULL;
	size_t arg_siz = 0;
	x->get_data_realloc(&arg, &arg_siz);
	bool out = MetaschemaType::encode_data(writer, &nargs, arg, arg_siz);
	if (arg != NULL) {
	  free(arg);
	  arg = NULL;
	}
	return out;
      }
      default: {
	ygglog_error("ScalarMetaschemaType::encode_data: Unsupported subtype '%s'.",
		     subtype_);
	return false;
      }
      }
    }
    }
    ygglog_error("ScalarMetaschemaType::encode_data: Cannot encode data of type '%s'.", type());
    return false;
  }

  // Decoding
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[in] allow_realloc int If 1, the passed variables will be reallocated
    to contain the deserialized data.
    @param[in,out] nargs size_t Number of arguments contained in ap. On return,
    the number of arguments assigned from the deserialized data will be assigned
    to this address.
    @param[out] ap va_list_t Reference to variable argument list containing
    address where deserialized data should be assigned.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) const override {
    if ((data.IsArray()) && (data.Size() == 1)) {
      data = data[0];
    }
    if (!(data.IsString())) {
      ygglog_error("ScalarMetaschemaType::decode_data: Raw data is not a string.");
      return false;
    }
    unsigned char* encoded_bytes = (unsigned char*)data.GetString();
    size_t encoded_len = data.GetStringLength();
    size_t decoded_len = 0;
    unsigned char* decoded_bytes = base64_decode(encoded_bytes, encoded_len,
						 &decoded_len);
    size_t nbytes_expected = nbytes();
    if ((!(_variable_precision)) && (nbytes_expected != decoded_len)) {
	ygglog_error("ScalarMetaschemaType::decode_data: %lu bytes were expected, but %lu were decoded.",
		     nbytes_expected, decoded_len);
      return false;
    }
    // Transfer data to array memory
    char *arg;
    char **p;
    if (allow_realloc) {
      p = va_arg(ap.va, char**);
      arg = *p;
    } else {
      arg = va_arg(ap.va, char*);
      p = &arg;
    }
    (*nargs)--;
    bool skip_terminal;
    if ((type_code() == T_SCALAR) &&
	((subtype_code_ == T_BYTES) || (subtype_code_ == T_UNICODE))) {
      size_t * const arg_siz = va_arg(ap.va, size_t*);
      (*nargs)--;
      skip_terminal = false;
      int ret = copy_to_buffer((char*)decoded_bytes, decoded_len,
			       p, arg_siz[0], allow_realloc, skip_terminal);
      if (ret < 0) {
	ygglog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for %s.",
		     subtype());
	free(decoded_bytes);
	return false;
      }
      arg_siz[0] = (size_t)ret;
    } else {
      size_t *arg_siz = &nbytes_expected;
      if (allow_realloc) {
	arg_siz[0] = 0;
      }
      skip_terminal = true;
      if ((cast_precision_ != 0) && (cast_precision_ != precision_)) {
	try {
	  decoded_len = cast_bytes(&decoded_bytes, decoded_len);
	  
	  if (!(allow_realloc)) {
	    arg_siz[0] = decoded_len;
	  }
	} catch(...) {
	  ygglog_error("ScalarMetaschemaType::decode_data: Cannot cast subtype '%s' and precision %ld to precision %ld.",
		       subtype_, precision_, cast_precision_);
	  free(decoded_bytes);
	  return false;
	}
      }
      // ygglog_info("arg_siz = %ld", *arg_siz);
      int ret = copy_to_buffer((char*)decoded_bytes, decoded_len,
			       p, *arg_siz, allow_realloc, skip_terminal);
      if (ret < 0) {
	ygglog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for %s.",
		     subtype());
	free(decoded_bytes);
	return false;
      }
    }
    free(decoded_bytes);
    return true;
  }
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[out] x YggGeneric* Pointer to generic object where data should be stored.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, YggGeneric* x) const override {
    switch (type_code()) {
    case T_SCALAR: {
      switch (subtype_code_) {
      case T_BYTES:
      case T_UNICODE: {
	size_t nargs = 2;
	int allow_realloc = 1;
	if (x == NULL) {
	  ygglog_throw_error("MetaschemaType::decode_data: Generic wrapper is not initialized.");
	}
	void **arg = x->get_data_pointer();
	size_t *arg_siz = x->get_nbytes_pointer();
	return MetaschemaType::decode_data(data, allow_realloc, &nargs, arg, arg_siz);
      }
      }
    }
    default: {
      return MetaschemaType::decode_data(data, x);
    }
    }
  }
  
  size_t cast_bytes(unsigned char **bytes, const size_t nbytes) const {
    bool raise_error = false;
    size_t from_precision = precision_;
    size_t to_precision = cast_precision_;
    if (((nbytes * to_precision) % from_precision) != 0) {
      ygglog_throw_error("cast_bytes: Cannot cast %ld bytes from precision %ld to %ld.",
			 nbytes, from_precision, to_precision);
    }
    size_t nbytes_new = nbytes*to_precision/from_precision;
    if (strcmp(subtype(), "float") == 0) {
      if (from_precision == 32) {
	float* tmp_val1 = (float*)(bytes[0]);
	if (to_precision == 64) {
	  double tmp_val2 = (double)(tmp_val1[0]);
	  bytes[0] = (unsigned char*)realloc(bytes[0], sizeof(double));
	  if (bytes[0] == NULL) {
	    raise_error = true;
	  } else {
	    memcpy(bytes[0], &tmp_val2, sizeof(double));
	  }
	} else {
	  raise_error = true;
	}
      } else if (from_precision == 64) {
	double* tmp_val1 = (double*)(bytes[0]);
	if (to_precision == 32) {
	  float tmp_val2 = (float)(tmp_val1[0]);
	  bytes[0] = (unsigned char*)realloc(bytes[0], sizeof(float));
	  if (bytes[0] == NULL) {
	    raise_error = true;
	  } else {
	    memcpy(bytes[0], &tmp_val2, sizeof(float));
	  }
	} else {
	  raise_error = true;
	}
      } else {
	raise_error = true;
      }
    } else {
      raise_error = true;
    }
    if (raise_error) {
      ygglog_throw_error("cast_bytes: Cannot change precision of %s type with precision %d to %d.",
			 subtype(), from_precision, to_precision);
    }
    return nbytes_new;
  }
  
private:
  const char *subtype_;
  const int subtype_code_;
  const size_t precision_;
  const char *units_;
  bool _variable_precision;
  size_t cast_precision_;
};


/*!
  @brief Base class for ND array type definition.

  The NDArrayMetaschemaType provides basic functionality for encoding/decoding
  ND array datatypes from/to JSON style strings.
 */
class NDArrayMetaschemaType : public ScalarMetaschemaType {
public:
  /*!
    @brief Constructor for NDArrayMetaschemaType.
    @param[in] subtype const character pointer to the name of the subtype.
    @param[in] precision size_t Type precision in bits.
    @param[in] shape std::vector<size_t> Shape of type array in each dimension.
    @param[in] units const char * (optional) Type units.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  NDArrayMetaschemaType(const char *subtype, const size_t precision,
			const std::vector<size_t> shape, const char *units="",
			const bool use_generic=false);
  /*!
    @brief Constructor for NDArrayMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  NDArrayMetaschemaType(const rapidjson::Value &type_doc,
			const bool use_generic=false);
  /*!
    @brief Constructor for NDArrayMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  NDArrayMetaschemaType(PyObject* pyobj, const bool use_generic=false);
  /*!
    @brief Copy constructor.
    @param[in] other NDArrayMetaschemaType* Instance to copy.
   */
  NDArrayMetaschemaType(const NDArrayMetaschemaType &other);
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  bool operator==(const MetaschemaType &Ref) const override;
  /*!
    @brief Create a copy of the type.
    @returns pointer to new NDArrayMetaschemaType instance with the same data.
   */
  NDArrayMetaschemaType* copy() const override;
  /*!
    @brief Print information about the type to stdout.
    @param[in] indent char* Indentation to add to display output.
  */
  void display(const char* indent="") const override;
  /*!
    @brief Get type information as a Python dictionary.
    @returns PyObject* Python dictionary.
   */
  PyObject* as_python_dict() const override;
  /*!
    @brief Get the number of dimensions in the array.
    @returns size_t Number of dimensions in type.
   */
  const size_t ndim() const;
  /*!
    @brief Get the shape of the array type.
    @returns std::vector<size_t> Shape of type in each dimension.
   */
  std::vector<size_t> shape() const;
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements.
   */
  const size_t nelements() const override;
  /*!
    @brief Determine if the number of elements is variable.
    @returns bool true if the number of elements can change, false otherwise.
  */
  const bool variable_nelements() const override;
  /*!
    @brief Determine the dimensions of the equivalent numpy array.
    @param[in, out] nd int* Address of integer where number of dimensions should be stored.
    @param[in, out] dims npy_intp** Address of pointer to memory where dimensions should be stored.
   */
  void numpy_dims(int *nd, npy_intp **dims) const override;
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override;
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override;
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override;
  /*!
    @brief Update the type object with info from provided variable arguments for deserialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_deserialization_args(size_t *nargs, va_list_t &ap) override;
  /*!
    @brief Update the instance's shape.
    @param[in] new_shape std::vector<size_t> Vector of new array sizes in each dimension.
   */
  void set_shape(std::vector<size_t> new_shape, bool force=false);
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const override;
  
private:
  std::vector<size_t> shape_;
  bool _variable_shape;

};


/*!
  @brief Base class for 1D array type definition.

  The OneDArrayMetaschemaType provides basic functionality for encoding/decoding
  1D array datatypes from/to JSON style strings.
 */
class OneDArrayMetaschemaType : public ScalarMetaschemaType {
 public:
  /*!
    @brief Constructor for OneDArrayMetaschemaType.
    @param[in] subtype const character pointer to the name of the subtype.
    @param[in] precision size_t Type precision in bits.
    @param[in] length size_t Number of elements in the array.
    @param[in] units const char * (optional) Type units.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  OneDArrayMetaschemaType(const char *subtype, const size_t precision,
			  const size_t length, const char *units="",
			  const bool use_generic=false) :
    ScalarMetaschemaType(subtype, precision, units, use_generic), length_(length) {
    update_type("1darray");
    if (length_ == 0)
      _variable_length = true;
    else
      _variable_length = false;
  }
  /*!
    @brief Constructor for OneDArrayMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  OneDArrayMetaschemaType(const rapidjson::Value &type_doc,
			  const bool use_generic=false) :
    ScalarMetaschemaType(type_doc, use_generic) {
    if (!(type_doc.HasMember("length")))
      ygglog_throw_error("OneDArrayMetaschemaType: 1darray types must include 'length'.");
    if (type_doc["length"].IsInt()) {
      length_ = type_doc["length"].GetInt();
    } else if (type_doc["length"].IsDouble()) {
      length_ = (size_t)(type_doc["length"].GetDouble());
    } else {
      ygglog_throw_error("OneDArrayMetaschemaType: 1darray 'length' value must be a number.");
    }
    update_type("1darray");
    if (length_ == 0)
      _variable_length = true;
    else
      _variable_length = false;
  }
  /*!
    @brief Constructor for OneDArrayMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  OneDArrayMetaschemaType(PyObject* pyobj, const bool use_generic=false) :
    ScalarMetaschemaType(pyobj, use_generic), length_(0) {
    update_type("1darray");
    get_item_python_dict_c(pyobj, "length", &length_,
			   "OneDArrayMetaschemaType: length: ",
			   T_INT, sizeof(size_t)*8);
    // Set variable length
    if (length_ == 0)
      _variable_length = true;
    else
      _variable_length = false;
  }
  /*!
    @brief Copy constructor.
    @param[in] other OneDArrayMetaschemaType* Instance to copy.
   */
  OneDArrayMetaschemaType(const OneDArrayMetaschemaType &other) :
    OneDArrayMetaschemaType(other.subtype(), other.precision(),
			    other.length(), other.units(),
			    other.use_generic()) {}
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  bool operator==(const MetaschemaType &Ref) const override {
    if (!(ScalarMetaschemaType::operator==(Ref)))
      return false;
    const OneDArrayMetaschemaType* pRef = dynamic_cast<const OneDArrayMetaschemaType*>(&Ref);
    if (!pRef)
      return false;
    if (length_ != pRef->length())
      return false;
    return true;
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new OneDArrayMetaschemaType instance with the same data.
   */
  OneDArrayMetaschemaType* copy() const override {
    return (new OneDArrayMetaschemaType(subtype(), precision(), length_, units(), use_generic()));
  }
  /*!
    @brief Print information about the type to stdout.
    @param[in] indent char* Indentation to add to display output.
  */
  void display(const char* indent="") const override {
    ScalarMetaschemaType::display(indent);
    printf("%s%-15s = %zu\n", indent, "length", length_);
  }
  /*!
    @brief Get type information as a Python dictionary.
    @returns PyObject* Python dictionary.
   */
  PyObject* as_python_dict() const override {
    PyObject* out = ScalarMetaschemaType::as_python_dict();
    set_item_python_dict_c(out, "length", &length_,
			   "OneDArrayMetaschemaType: as_python_dict: ",
			   T_INT, sizeof(size_t)*8);
    return out;
  }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements.
   */
  const size_t nelements() const override {
    return length_;
  }
  /*!
    @brief Determine if the number of elements is variable.
    @returns bool true if the number of elements can change, false otherwise.
  */
  const bool variable_nelements() const override {
    return _variable_length;
  }
  /*!
    @brief Determine the dimensions of the equivalent numpy array.
    @param[in, out] nd int* Address of integer where number of dimensions should be stored.
    @param[in, out] dims npy_intp** Address of pointer to memory where dimensions should be stored.
   */
  void numpy_dims(int *nd, npy_intp **dims) const override {
    nd[0] = 1;
    npy_intp *idim = (npy_intp*)realloc(dims[0], sizeof(npy_intp));
    if (idim == NULL) {
      ygglog_throw_error("OneDArrayMetaschemaType::numpy_dims: Failed to realloc dims.");
    }
    idim[0] = (npy_intp)(length());
    dims[0] = idim;
  }
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override {
    if (new_info->type_code() == T_NDARRAY) {
      const NDArrayMetaschemaType* new_info_nd = dynamic_cast<const NDArrayMetaschemaType*>(new_info);
      OneDArrayMetaschemaType* new_info_oned = new OneDArrayMetaschemaType(new_info_nd->subtype(), new_info_nd->precision(), new_info_nd->nelements(), new_info_nd->units());
      update(new_info_oned);
      delete new_info_oned;
    } else {
      ScalarMetaschemaType::update(new_info);
      const OneDArrayMetaschemaType* new_info_oned = dynamic_cast<const OneDArrayMetaschemaType*>(new_info);
      set_length(new_info_oned->length());
    }
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    size_t out = ScalarMetaschemaType::update_from_serialization_args(nargs, ap);
    if (use_generic())
      return out;
    if ((_variable_length) && (*nargs >= 2)) {
      unsigned char* temp = va_arg(ap.va, unsigned char*);
      UNUSED(temp); // Parameter extract to get next
      size_t new_length = va_arg(ap.va, size_t);
      skip_after_.push_back(sizeof(size_t));
      set_length(new_length);
      out = out + 2;
    } else {
      va_arg(ap.va, unsigned char*);
      out = out + 1;
    }
    return out;
  }
  /*!
    @brief Update the type object with info from provided variable arguments for deserialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_deserialization_args(size_t *nargs, va_list_t &ap) override {
    size_t out = MetaschemaType::update_from_deserialization_args(nargs, ap);
    if (use_generic())
      return out;
    if ((_variable_length) && (*nargs >= 2)) {
      unsigned char** temp = va_arg(ap.va, unsigned char**);
      UNUSED(temp); // Parameter extracted to get next
      size_t * const new_length = va_arg(ap.va, size_t*);
      new_length[0] = length_;
      skip_after_.push_back(sizeof(size_t*));
      out = out + 2;
    }
    return out;
  }
  /*!
    @brief Update the instance's length.
    @param[in] new_length size_t New length.
   */
  void set_length(size_t new_length, bool force=false) override {
    if (length_ != new_length) {
      if (!(force)) {
	if (length_ == 0) {
	  // Pass
	} else if (_variable_length) {
	  // Pass
	} else {
	  ygglog_throw_error("OneDArrayMetaschemaType::set_length: Cannot update precision from %ld to %ld for %s of subtype %s.",
			     length_, new_length, type(), subtype());
	}
      }
      size_t* length_modifier = const_cast<size_t*>(&length_);
      *length_modifier = new_length;
    }
  }
  /*!
    @brief Set the _variable_length private variable.
    @param[in] new_variable_length bool New value.
   */
  void set_variable_length(bool new_variable_length) override {
    _variable_length = new_variable_length;
  }
  /*!
    @brief Get type length.
    @returns size_t Number of elements in the array.
  */
  size_t length() const {
    return length_;
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    size_t out = 1;
    if (_variable_length)
      out++;
    return out;
  }
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const override {
    if (!(ScalarMetaschemaType::encode_type_prop(writer))) { return false; }
    writer->Key("length");
    writer->Int((int)length_);
    return true;
  }
  
private:
  size_t length_;
  bool _variable_length;
};


NDArrayMetaschemaType::NDArrayMetaschemaType(const char *subtype, const size_t precision,
					     const std::vector<size_t> shape,
					     const char *units,
					     const bool use_generic) :
  ScalarMetaschemaType(subtype, precision, units, use_generic),
  shape_(shape) {
  update_type("ndarray");
  if (shape_.size() == 0) {
    _variable_shape = true;
  } else {
    _variable_shape = false;
  }
};
NDArrayMetaschemaType::NDArrayMetaschemaType(const rapidjson::Value &type_doc,
					     const bool use_generic) :
  ScalarMetaschemaType(type_doc, use_generic) {
  if (!(type_doc.HasMember("shape")))
    ygglog_throw_error("NDArrayMetaschemaType: ndarray types must include 'shape'.");
  if (!(type_doc["shape"].IsArray()))
    ygglog_throw_error("NDArrayMetaschemaType: ndarray 'shape' value must be an array.");
  size_t ndim = type_doc["shape"].Size();
  size_t i;
  for (i = 0; i < ndim; i++) {
    if (type_doc["shape"][(rapidjson::SizeType)i].IsInt()) {
      shape_.push_back(type_doc["shape"][(rapidjson::SizeType)i].GetInt());
    } else if (type_doc["shape"][(rapidjson::SizeType)i].IsDouble()) {
      shape_.push_back((size_t)(type_doc["shape"][(rapidjson::SizeType)i].GetDouble()));
    } else {
      ygglog_throw_error("NDArrayMetaschemaType: ndarray 'shape' elements must be numbers.");
    }
  }
  update_type("ndarray");
};
NDArrayMetaschemaType::NDArrayMetaschemaType(PyObject* pyobj,
					     const bool use_generic) :
  ScalarMetaschemaType(pyobj, use_generic) {
  update_type("ndarray");
  // Shape
  PyObject* pyshape = get_item_python_dict(pyobj, "shape",
					   "NDArrayMetaschemaType: shape: ",
					   T_ARRAY);
  size_t i, ishape, ndim = PyList_Size(pyshape);
  for (i = 0; i < ndim; i++) {
    get_item_python_list_c(pyobj, i, &ishape,
			   "NDArrayMetaschemaType: shape: ",
			   T_INT, sizeof(size_t)*8);
    shape_.push_back(ishape);
  }
  Py_DECREF(pyshape);
  // Set variable shape
  if (shape_.size() == 0) {
    _variable_shape = true;
  } else {
    _variable_shape = false;
  }
};
NDArrayMetaschemaType::NDArrayMetaschemaType(const NDArrayMetaschemaType &other) :
  NDArrayMetaschemaType(other.subtype(), other.precision(),
			other.shape(), other.units(),
			other.use_generic()) {};
bool NDArrayMetaschemaType::operator==(const MetaschemaType &Ref) const {
  if (!(ScalarMetaschemaType::operator==(Ref)))
    return false;
  const NDArrayMetaschemaType* pRef = dynamic_cast<const NDArrayMetaschemaType*>(&Ref);
  if (!pRef)
    return false;
  if (shape_ != pRef->shape())
    return false;
  return true;
};
NDArrayMetaschemaType* NDArrayMetaschemaType::copy() const {
  return (new NDArrayMetaschemaType(subtype(), precision(), shape(), units(), use_generic()));
}
void NDArrayMetaschemaType::display(const char* indent) const {
  ScalarMetaschemaType::display(indent);
  printf("%s%-15s = [ ", indent, "shape");
  if (ndim() > 0) {
    size_t i;
    printf("%zu", shape_[0]);
    for (i = 1; i < ndim(); i++) {
      printf(", %zu", shape_[i]);
    }
  }
  printf(" ]\n");
};
PyObject* NDArrayMetaschemaType::as_python_dict() const {
  PyObject* out = ScalarMetaschemaType::as_python_dict();
  PyObject* pyshape = PyList_New(ndim());
  if (pyshape == NULL) {
    ygglog_throw_error("NDArrayMetaschemaType::as_python_dict: Failed to create new Python list for shape.");
  }
  size_t i;
  for (i = 1; i < ndim(); i++) {
    set_item_python_list_c(pyshape, i, &(shape_[i]),
			   "NDArrayMetaschemaType::as_python_dict: shape: ",
			   T_INT, sizeof(size_t)*8);
  }
  set_item_python_dict(out, "shape", pyshape,
		       "NDArrayMetaschemaType::as_python_dict: ",
		       T_ARRAY);
  return out;
};
const size_t NDArrayMetaschemaType::ndim() const {
  return shape_.size();
};
std::vector<size_t> NDArrayMetaschemaType::shape() const {
  return shape_;
};
const size_t NDArrayMetaschemaType::nelements() const {
  size_t nelements = 0;
  if (ndim() > 0) {
    size_t i;
    nelements = 1;
    for (i = 0; i < ndim(); i++) {
      nelements = nelements * shape_[i];
    }
  }
  return nelements;
};
const bool NDArrayMetaschemaType::variable_nelements() const {
  return _variable_shape;
};
void NDArrayMetaschemaType::numpy_dims(int *nd, npy_intp **dims) const {
  int i;
  nd[0] = (int)ndim();
  npy_intp *idim = (npy_intp*)realloc(dims[0], nd[0]*sizeof(npy_intp));
  if (idim == NULL) {
    ygglog_throw_error("NDArrayMetaschemaType::numpy_dims: Failed to realloc dims.");
  }
  for (i = 0; i < nd[0]; i++) {
    idim[i] = (npy_intp)(shape_[i]);
  }
  dims[0] = idim;
};
size_t NDArrayMetaschemaType::nargs_exp() const {
  size_t out = 1;
  if (_variable_shape)
    out = out + 2;
  return out;
}
void NDArrayMetaschemaType::update(const MetaschemaType* new_info) {
  ScalarMetaschemaType::update(new_info);
  const NDArrayMetaschemaType* new_info_nd = dynamic_cast<const NDArrayMetaschemaType*>(new_info);
  set_shape(new_info_nd->shape());
};
size_t NDArrayMetaschemaType::update_from_serialization_args(size_t *nargs, va_list_t &ap) {
  size_t out = MetaschemaType::update_from_serialization_args(nargs, ap);
  if (use_generic())
    return out;
  if ((_variable_shape) && (*nargs >= 3)) {
    unsigned char* temp = va_arg(ap.va, unsigned char*);
    UNUSED(temp); // Parameter extracted to get next
    size_t new_ndim = va_arg(ap.va, size_t);
    skip_after_.push_back(sizeof(size_t));
    size_t* new_shape_ptr = va_arg(ap.va, size_t*);
    skip_after_.push_back(sizeof(size_t*));
    std::vector<size_t> new_shape(new_shape_ptr, new_shape_ptr + new_ndim);
    set_shape(new_shape);
    out = out + 3;
  } else {
    va_arg(ap.va, unsigned char*);
    out = out + 1;
  }
  return out;
};
size_t NDArrayMetaschemaType::update_from_deserialization_args(size_t *nargs, va_list_t &ap) {
  size_t out = MetaschemaType::update_from_deserialization_args(nargs, ap);
  if (use_generic())
    return out;
  if ((_variable_shape) && (*nargs >= 3)) {
    unsigned char** temp = va_arg(ap.va, unsigned char**);
    UNUSED(temp); // Parameter extracted to get next
    size_t * const new_ndim = va_arg(ap.va, size_t*);
    skip_after_.push_back(sizeof(size_t*));
    size_t** new_shape = va_arg(ap.va, size_t**);
    skip_after_.push_back(sizeof(size_t**));
    new_ndim[0] = ndim();
    size_t* new_shape_temp = (size_t*)realloc(new_shape[0], ndim()*sizeof(size_t));
    if (new_shape_temp == NULL) {
      ygglog_throw_error("NDArrayMetaschemaType::decode_data: Failed to realloc memory for the provided shape array.");
    }
    new_shape[0] = new_shape_temp;
    size_t i;
    for (i = 0; i < ndim(); i++) {
      (*new_shape)[i] = shape_[i];
    }
    out = out + 3;
  }
  return out;
};
void NDArrayMetaschemaType::set_shape(std::vector<size_t> new_shape, bool force) {
  bool match = (ndim() == new_shape.size());
  size_t i;
  if (match) {
    for (i = 0; i < ndim(); i++) {
      if (shape_[i] != new_shape[i]) {
	match = false;
	break;
      }
    }
  }
  if (!(match)) {
    if (!(force)) {
      if (ndim() == 0) {
	// Pass
      } else if (_variable_shape) {
	// Pase
      } else {
	ygglog_throw_error("NDArrayMetaschemaType::set_shape: Cannot update shape.");
      }
    }
    shape_.resize(new_shape.size());
    for (i = 0; i < new_shape.size(); i++) {
      shape_[i] = new_shape[i];
    }
  }
};
bool NDArrayMetaschemaType::encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const {
  if (!(ScalarMetaschemaType::encode_type_prop(writer))) { return false; }
  writer->Key("shape");
  writer->StartArray();
  size_t i;
  for (i = 0; i < ndim(); i++) {
    writer->Int((int)(shape_[i]));
  }
  writer->EndArray();
  return true;
};


#endif /*SCALAR_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
