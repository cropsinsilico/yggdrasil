#ifndef SCALAR_METASCHEMA_TYPE_H_
#define SCALAR_METASCHEMA_TYPE_H_

#define STRBUFF 100

#include <vector>
#include <cstring>

#include "../../tools.h"
#include "../../serialize/base64.h"
#include "MetaschemaType.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


#ifdef _WIN32
#include <complex.h>
typedef _Fcomplex complex_float;
typedef _Dcomplex complex_double;
typedef _Lcomplex complex_long_double;
#else
#include <complex.h>
typedef float _Complex complex_float;
typedef double _Complex complex_double;
typedef long double _Complex complex_long_double;
#endif


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
   */
  ScalarMetaschemaType(const char *subtype, const size_t precision,
		       const char *units="") :
    MetaschemaType("scalar"), subtype_((const char*)malloc(STRBUFF)), subtype_code_(-1),
    precision_(precision), units_((const char*)malloc(STRBUFF)) {
    if (precision_ == 0)
      _variable_precision = true;
    else
      _variable_precision = false;
    update_subtype(subtype);
    update_units(units);
  }
  /*!
    @brief Constructor for ScalarMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  ScalarMetaschemaType(const rapidjson::Value &type_doc) :
    MetaschemaType(type_doc), subtype_((const char*)malloc(STRBUFF)), subtype_code_(-1),
    precision_(0), units_((const char*)malloc(STRBUFF)) {
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
      update_subtype(type_doc["subtype"].GetString());
      break;
    default:
      update_subtype(type());
      update_type("scalar");
    }
    // Precision
    if (!(type_doc.HasMember("precision")))
      ygglog_throw_error("ScalarMetaschemaType: Precision missing.");
    if (!(type_doc["precision"].IsInt()))
      ygglog_throw_error("ScalarMetaschemaType: Precision must be integer.");
    size_t *precision_modifier = const_cast<size_t*>(&precision_);
    *precision_modifier = (size_t)(type_doc["precision"].GetInt());
    // Units
    if (type_doc.HasMember("units")) {
      if (!type_doc["units"].IsString())
	ygglog_throw_error("ScalarMetaschemaType: Units must be a string.");
      update_units(type_doc["units"].GetString());
    } else {
      update_units("");
    }
    // Set variable
    if (precision_ == 0)
      _variable_precision = true;
    else
      _variable_precision = false;
  }
  /*!
    @brief Destructor for ScalarMetaschemaType.
    Free the type string malloc'd during constructor.
   */
  ~ScalarMetaschemaType() {
    free((char*)subtype_);
    free((char*)units_);
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new ScalarMetaschemaType instance with the same data.
   */
  ScalarMetaschemaType* copy() { return (new ScalarMetaschemaType(subtype_, precision_, units_)); }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() {
    MetaschemaType::display();
    printf("%-15s = %s\n", "subtype", subtype_);
    printf("%-15s = %d\n", "subtype_code", subtype_code_);
    printf("%-15s = %lu\n", "precision", precision_);
    printf("%-15s = %s\n", "units", units_);
  }
  /*!
    @brief Check that the subtype is correct and get the corresponding code.
    @returns int Type code for the instance's subtype.
   */
  int check_subtype() {
    std::map<const char*, int, strcomp> type_map = get_type_map();
    std::map<const char*, int, strcomp>::iterator it = type_map.find(subtype_);
    if (it == type_map.end()) {
      ygglog_throw_error("ScalarMetaschemaType: Unsupported subtype '%s'.", subtype_);
    }
    return it->second;
  }
  /*!
    @brief Get the subtype string.
    @returns const char pointer to the subtype string.
   */
  const char* subtype() { return subtype_; }
  /*!
    @brief Get the type precision.
    @returns size_t Type precision in bytes.
   */
  const size_t precision() { return precision_; }
  /*!
    @brief Get the type units.
    @returns const char* Type units string.
   */
  const char* units() { return units_; }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements (1 for scalar).
   */
  virtual const size_t nelements() { return 1; }
  /*!
    @brief Get the size of the type in bits.
    @returns size_t Type size.
   */
  const size_t nbits() {
    return precision_ * nelements();
  }
  /*!
    @brief Get the size of the type in bytes.
    @returns size_t Type size.
   */
  const size_t nbytes() {
    return nbits() / 8;
  }
  /*!
    @brief Update the instance's type.
    @param[in] new_type const char * String for new type.
   */
  void update_type(const char* new_type) {
    MetaschemaType::update_type(new_type);
    if (strcmp(type(), "scalar") == 0) {
      _variable_precision = false;
    }
  }
  /*!
    @brief Update the instance's subtype.
    @param[in] new_subtype const char * String for new subtype.
   */
  void update_subtype(const char* new_subtype) {
    char **subtype_modifier = const_cast<char**>(&subtype_);
    strncpy(*subtype_modifier, new_subtype, STRBUFF);
    int* subtype_code_modifier = const_cast<int*>(&subtype_code_);
    *subtype_code_modifier = check_subtype();
  }
  /*!
    @brief Update the instance's units.
    @param[in] new_units const char * String for new units.
   */
  void update_units(const char* new_units) {
    char **units_modifier = const_cast<char**>(&units_);
    strncpy(*units_modifier, new_units, STRBUFF);
  }
  /*!
    @brief Update the instance's precision.
    @param[in] new_precision size_t New precision.
   */
  void set_precision(const size_t new_precision) {
    if ((strcmp(subtype_, "bytes") != 0) && (strcmp(subtype_, "unicode") != 0)) {
      ygglog_throw_error("ScalarMetaschemaType::set_precision: Variable precision only allowed for bytes and unicode, not '%s'.", subtype_);
    }
    size_t *precision_modifier = const_cast<size_t*>(&precision_);
    *precision_modifier = new_precision;
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() {
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

  // Encoding
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
    if (!MetaschemaType::encode_type_prop(writer)) { return false; }
    writer->Key("subtype");
    writer->String(subtype_, strlen(subtype_));
    writer->Key("precision");
    writer->Int(precision_);
    if (strlen(units_) == 0) {
      writer->Key("units");
      writer->String("");
    } else {
      writer->Key("units");
      writer->String(units_, strlen(units_));
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
		   size_t *nargs, va_list_t &ap) {
    // TODO: case by case for scalar types
    size_t bytes_precision = nbytes();
    unsigned char* arg = (unsigned char*)malloc(bytes_precision + 1);
    if ((strcmp(type(), "1darray") == 0) || (strcmp(type(), "ndarray") == 0)) {
      if (nelements() == 0) {
	ygglog_error("ScalarMetaschemaType::encode_data: Array types require the number of elements be non-zero.");
	return false;
      }
      switch (subtype_code_) {
      case T_COMPLEX:
	// TODO: Split real and imaginary parts?
      default:
	unsigned char* arg0 = va_arg(ap.va, unsigned char*);
	memcpy(arg, arg0, bytes_precision);
      }
    } else {
      if (arg == NULL) {
	ygglog_error("ScalarMetaschemaType::encode_data: Failed to malloc for %lu bytes.",
		     bytes_precision + 1);
	return false;
      }
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
#ifdef _WIN32
	  complex_double arg00 = va_arg(ap.va, complex_double);
	  complex_float arg0 = {(float)creal(arg00), (float)cimag(arg00)};
#else
	  complex_float arg0 = (complex_float)va_arg(ap.va, complex_double);
#endif
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(double) == (bytes_precision / 2)) {
	  complex_double arg0 = va_arg(ap.va, complex_double);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(long double) == (bytes_precision / 2)) {
	  complex_long_double arg0 = va_arg(ap.va, complex_long_double);
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
	} else if ((arg0_siz > bytes_precision) && (_variable_precision)) {
	  //printf("arg0_siz = %lu, bytes_precision = %lu\n", arg0_siz, bytes_precision);
	  set_precision(8 * arg0_siz);
	  bytes_precision = nbytes();
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
    (*nargs)--;
    size_t encoded_len = 0;
    unsigned char* encoded_bytes = base64_encode(arg, nbytes(), &encoded_len);
    bool out = writer->String((char*)encoded_bytes, encoded_len);
    free(arg);
    free(encoded_bytes);
    return out;
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
		   size_t *nargs, va_list_t &ap) {
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
    if ((strcmp(type(), "1darray") == 0) || (strcmp(type(), "ndarray") == 0)) {
      char **temp = (char**)va_arg(ap.va, unsigned char**);
      (*nargs)--;
      size_t temp_siz = 0;
      int allow_realloc0 = 1; // Always assumed to be pointers to buffers
      bool skip_terminal = true;
      int ret = copy_to_buffer((char*)decoded_bytes, decoded_len, temp, temp_siz,
			       allow_realloc0, skip_terminal);
      if (ret < 0) {
	ygglog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for array.");
	free(decoded_bytes);
	if (*temp != NULL)
	  free(*temp);
	*temp = NULL;
	return false;
      }
    } else {
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
      //size_t 
      bool skip_terminal;
      if ((strcmp(subtype(), "bytes") == 0) || (strcmp(subtype(), "unicode") == 0)) {
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
	// if (_variable_precision) {
	//   set_precision(8 * strlen(decoded_bytes));
	// }
      } else {
	size_t *arg_siz = &nbytes_expected;
	skip_terminal = true;
	int ret = copy_to_buffer((char*)decoded_bytes, decoded_len,
				 p, *arg_siz, allow_realloc, skip_terminal);
	if (ret < 0) {
	  ygglog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for %s.",
		       subtype());
	  free(decoded_bytes);
	  return false;
	}
      }
    }
    free(decoded_bytes);
    return true;
  }
  
private:
  const char *subtype_;
  const int subtype_code_;
  const size_t precision_;
  const char *units_;
  bool _variable_precision;
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
   */
  OneDArrayMetaschemaType(const char *subtype, const size_t precision,
			  const size_t length, const char *units="") :
    ScalarMetaschemaType(subtype, precision, units), length_(length) {
    update_type("1darray");
  }
  /*!
    @brief Constructor for OneDArrayMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  OneDArrayMetaschemaType(const rapidjson::Value &type_doc) :
    ScalarMetaschemaType(type_doc) {
    if (!(type_doc.HasMember("length")))
      ygglog_throw_error("OneDArrayMetaschemaType: 1darray types must include 'length'.");
    if (!(type_doc["length"].IsInt()))
      ygglog_throw_error("OneDArrayMetaschemaType: 1darray 'length' value must be an int.");
    length_ = type_doc["length"].GetInt();
    update_type("1darray");
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new OneDArrayMetaschemaType instance with the same data.
   */
  OneDArrayMetaschemaType* copy() {
    return (new OneDArrayMetaschemaType(subtype(), precision(), length_, units()));
  }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() {
    ScalarMetaschemaType::display();
    printf("%-15s = %lu\n", "length", length_);
  }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements.
   */
  const size_t nelements() {
    return length_;
  }
  /*!
    @brief Update the instance's length.
    @param[in] new_length size_t New length.
   */
  void set_length(size_t new_length) {
    size_t* length_modifier = const_cast<size_t*>(&length_);
    *length_modifier = new_length;
  }
  /*!
    @brief Get type length.
    @returns size_t Number of elements in the array.
  */
  size_t get_length() {
    size_t out = length_;
    return out;
  }
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
    if (!(ScalarMetaschemaType::encode_type_prop(writer))) { return false; }
    writer->Key("length");
    writer->Int(length_);
    return true;
  }
private:
  size_t length_;
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
   */
  NDArrayMetaschemaType(const char *subtype, const size_t precision,
			const std::vector<size_t> shape, const char *units="") :
    ScalarMetaschemaType(subtype, precision, units), shape_(shape) {
    update_type("ndarray");
  }
  /*!
    @brief Constructor for NDArrayMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing the type
    definition from a JSON encoded header.
   */
  NDArrayMetaschemaType(const rapidjson::Value &type_doc) :
    ScalarMetaschemaType(type_doc) {
    if (!(type_doc.HasMember("shape")))
      ygglog_throw_error("NDArrayMetaschemaType: ndarray types must include 'shape'.");
    if (!(type_doc["shape"].IsArray()))
      ygglog_throw_error("NDArrayMetaschemaType: ndarray 'shape' value must be an array.");
    size_t ndim = type_doc["shape"].Size();
    size_t i;
    for (i = 0; i < ndim; i++) {
      if (!(type_doc["shape"][i].IsInt()))
	ygglog_throw_error("NDArrayMetaschemaType: ndarray 'shape' elements must be integers.");
      shape_.push_back(type_doc["shape"][i].GetInt());
    }
    update_type("ndarray");
  }
  /*!
    @brief Create a copy of the type.
    @returns pointer to new NDArrayMetaschemaType instance with the same data.
   */
  NDArrayMetaschemaType* copy() {
    return (new NDArrayMetaschemaType(subtype(), precision(), shape(), units()));
  }
  /*!
    @brief Print information about the type to stdout.
  */
  void display() {
    ScalarMetaschemaType::display();
    printf("%-15s = [ ", "shape");
    if (ndim() > 0) {
      size_t i;
      printf("%lu", shape_[0]);
      for (i = 1; i < ndim(); i++) {
	printf(", %lu", shape_[i]);
      }
    }
    printf(" ]\n");
  }
  /*!
    @brief Get the number of dimensions in the array.
    @returns size_t Number of dimensions in type.
   */
  const size_t ndim() { return shape_.size(); }
  /*!
    @brief Get the shape of the array type.
    @returns std::vector<size_t> Shape of type in each dimension.
   */
  std::vector<size_t> shape() { return shape_; }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements.
   */
  const size_t nelements() {
    size_t nelements = 0;
    if (ndim() > 0) {
      size_t i;
      for (i = 0; i < ndim(); i++) {
	nelements = nelements * shape_[i];
      }
    }
    return nelements;
  }
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
    if (!(ScalarMetaschemaType::encode_type_prop(writer))) { return false; }
    writer->Key("shape");
    writer->StartArray();
    size_t i;
    for (i = 0; i < ndim(); i++) {
      writer->Int((int)(shape_[i]));
    }
    writer->EndArray();
    return true;
  }
private:
  std::vector<size_t> shape_;

};


#endif /*SCALAR_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
