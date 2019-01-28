#ifndef SCALAR_METASCHEMA_TYPE_H_
#define SCALAR_METASCHEMA_TYPE_H_

#define STRBUFF 100

#include <vector>
#include <cstring>
#ifdef _WIN32
#include <complex>
typedef std::complex<float> complex_float;
typedef std::complex<double> complex_double;
typedef std::complex<long double> complex_long_double;
// using complex_float = complex<float>;
// using complex_double = complex<double>;
// using complex_long_double = complex<long double>;
#else
#include <complex.h>
typedef float _Complex complex_float;
typedef double _Complex complex_double;
typedef long double _Complex complex_long_double;
#endif

#include "../../tools.h"
#include "../../serialize/base64.h"
#include "MetaschemaType.h"

#include "rapidjson/document.h"
#include "rapidjson/writer.h"


class ScalarMetaschemaType : public MetaschemaType {
public:
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
  ScalarMetaschemaType(const rapidjson::Value &type_doc) :
    MetaschemaType(type_doc), subtype_((const char*)malloc(STRBUFF)), subtype_code_(-1),
    precision_(0), units_((const char*)malloc(STRBUFF)) {
    switch (type_code()) {
    case T_1DARRAY:
    case T_NDARRAY:
    case T_SCALAR:
      // Subtype
      if (!(type_doc.HasMember("subtype"))) {
	cislog_throw_error("ScalarMetaschemaType: %s type must include 'subtype'.", type());
      }
      if (!(type_doc["subtype"].IsString())) {
	cislog_throw_error("ScalarMetaschemaType: 'subtype' value must be a string.");
      }
      update_subtype(type_doc["subtype"].GetString());
      break;
    default:
      update_subtype(type());
      update_type("scalar");
    }
    // Precision
    if (!(type_doc.HasMember("precision")))
      cislog_throw_error("ScalarMetaschemaType: Precision missing.");
    if (!(type_doc["precision"].IsInt()))
      cislog_throw_error("ScalarMetaschemaType: Precision must be integer.");
    size_t *precision_modifier = const_cast<size_t*>(&precision_);
    *precision_modifier = (size_t)(type_doc["precision"].GetInt());
    // Units
    if (type_doc.HasMember("units")) {
      if (!type_doc["units"].IsString())
	cislog_throw_error("ScalarMetaschemaType: Units must be a string.");
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
  ~ScalarMetaschemaType() {
    free((char*)subtype_);
    free((char*)units_);
  }
  ScalarMetaschemaType* copy() { return (new ScalarMetaschemaType(subtype_, precision_, units_)); }
  void display() {
    MetaschemaType::display();
    printf("%-15s = %s\n", "subtype", subtype_);
    printf("%-15s = %d\n", "subtype_code", subtype_code_);
    printf("%-15s = %lu\n", "precision", precision_);
    printf("%-15s = %s\n", "units", units_);
  }
  int check_subtype() {
    std::map<const char*, int, strcomp> type_map = get_type_map();
    std::map<const char*, int, strcomp>::iterator it = type_map.find(subtype_);
    if (it == type_map.end()) {
      cislog_throw_error("ScalarMetaschemaType: Unsupported subtype '%s'.", subtype_);
    }
    return it->second;
  }
  const char* subtype() { return subtype_; }
  const size_t precision() { return precision_; }
  const char* units() { return units_; }
  virtual const size_t nelements() { return 1; }
  const size_t nbits() {
    return precision_ * nelements();
  }
  const size_t nbytes() {
    return nbits() / 8;
  }
  void update_type(const char* new_type) {
    MetaschemaType::update_type(new_type);
    if (strcmp(type(), "scalar") == 0) {
      _variable_precision = false;
    }
  }
  void update_subtype(const char* new_subtype) {
    char **subtype_modifier = const_cast<char**>(&subtype_);
    strncpy(*subtype_modifier, new_subtype, STRBUFF);
    int* subtype_code_modifier = const_cast<int*>(&subtype_code_);
    *subtype_code_modifier = check_subtype();
  }
  void update_units(const char* new_units) {
    char **units_modifier = const_cast<char**>(&units_);
    strncpy(*units_modifier, new_units, STRBUFF);
  }
  void set_precision(const size_t new_precision) {
    if ((strcmp(subtype_, "bytes") != 0) && (strcmp(subtype_, "unicode") != 0)) {
      cislog_throw_error("ScalarMetaschemaType::set_precision: Variable precision only allowed for bytes and unicode, not '%s'.", subtype_);
    }
    size_t *precision_modifier = const_cast<size_t*>(&precision_);
    *precision_modifier = new_precision;
  }
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
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   size_t *nargs, va_list_t &ap) {
    // TODO: case by case for scalar types
    size_t bytes_precision = nbytes();
    unsigned char* arg = (unsigned char*)malloc(bytes_precision + 1);
    if ((strcmp(type(), "1darray") == 0) || (strcmp(type(), "ndarray") == 0)) {
      if (nelements() == 0) {
	cislog_error("ScalarMetaschemaType::encode_data: Array types require the number of elements be non-zero.");
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
	cislog_error("ScalarMetaschemaType::encode_data: Failed to malloc for %lu bytes.",
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
	  cislog_error("ScalarMetaschemaType::encode_data: Unsupported integer precision '%lu'.",
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
	  cislog_error("ScalarMetaschemaType::encode_data: Unsupported unsigned integer precision '%lu'.",
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
	  cislog_error("ScalarMetaschemaType::encode_data: Unsupported float precision '%lu'.",
		       precision_);
	  return false;
	}
	break;
      }
      case T_COMPLEX: {
	if (sizeof(float) == (bytes_precision / 2)) {
	  complex_float arg0 = (complex_float)va_arg(ap.va, complex_double);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(double) == (bytes_precision / 2)) {
	  complex_double arg0 = va_arg(ap.va, complex_double);
	  memcpy(arg, &arg0, bytes_precision);
	} else if (sizeof(long double) == (bytes_precision / 2)) {
	  complex_long_double arg0 = va_arg(ap.va, complex_long_double);
	  memcpy(arg, &arg0, bytes_precision);
	} else {
	  cislog_error("ScalarMetaschemaType::encode_data: Unsupported complex precision '%lu'.",
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
	  cislog_error("ScalarMetaschemaType::encode_data: Failed to copy bytes/unicode variable to buffer.");
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
	cislog_error("ScalarMetaschemaType::encode_data: Unsupported subtype '%s'.",
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
  bool decode_data(rapidjson::Value &data, const int allow_realloc,
		   size_t *nargs, va_list_t &ap) {
    if (!(data.IsString())) {
      cislog_error("ScalarMetaschemaType::decode_data: Raw data is not a string.");
      return false;
    }
    unsigned char* encoded_bytes = (unsigned char*)data.GetString();
    size_t encoded_len = data.GetStringLength();
    size_t decoded_len = 0;
    unsigned char* decoded_bytes = base64_decode(encoded_bytes, encoded_len,
						 &decoded_len);
    size_t nbytes_expected = nbytes();
    if ((!(_variable_precision)) && (nbytes_expected != decoded_len)) {
	cislog_error("ScalarMetaschemaType::decode_data: %lu bytes were expected, but %lu were decoded.",
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
	cislog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for array.");
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
	  cislog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for %s.",
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
	  cislog_error("ScalarMetaschemaType::decode_data: Failed to copy buffer for %s.",
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


class OneDArrayMetaschemaType : public ScalarMetaschemaType {
 public:
  OneDArrayMetaschemaType(const char *subtype, const size_t precision,
			  const size_t length, const char *units="") :
    ScalarMetaschemaType(subtype, precision, units), length_(length) {
    update_type("1darray");
  }
  OneDArrayMetaschemaType(const rapidjson::Value &type_doc) :
    ScalarMetaschemaType(type_doc) {
    if (!(type_doc.HasMember("length")))
      cislog_throw_error("OneDArrayMetaschemaType: 1darray types must include 'length'.");
    if (!(type_doc["length"].IsInt()))
      cislog_throw_error("OneDArrayMetaschemaType: 1darray 'length' value must be an int.");
    length_ = type_doc["length"].GetInt();
    update_type("1darray");
  }
  OneDArrayMetaschemaType* copy() {
    return (new OneDArrayMetaschemaType(subtype(), precision(), length_, units()));
  }
  void display() {
    ScalarMetaschemaType::display();
    printf("%-15s = %lu\n", "length", length_);
  }
  const size_t nelements() {
    return length_;
  }
  void set_length(size_t new_length) {
    size_t* length_modifier = const_cast<size_t*>(&length_);
    *length_modifier = new_length;
  }
  size_t get_length() {
    size_t out = length_;
    return out;
  }
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) {
    if (!(ScalarMetaschemaType::encode_type_prop(writer))) { return false; }
    writer->Key("length");
    writer->Int(length_);
    return true;
  }
private:
  size_t length_;
};


class NDArrayMetaschemaType : public ScalarMetaschemaType {
public:
  NDArrayMetaschemaType(const char *subtype, const size_t precision,
			const std::vector<size_t> shape, const char *units="") :
    ScalarMetaschemaType(subtype, precision, units), shape_(shape) {
    update_type("ndarray");
  }
  NDArrayMetaschemaType(const rapidjson::Value &type_doc) :
    ScalarMetaschemaType(type_doc) {
    if (!(type_doc.HasMember("shape")))
      cislog_throw_error("NDArrayMetaschemaType: ndarray types must include 'shape'.");
    if (!(type_doc["shape"].IsArray()))
      cislog_throw_error("NDArrayMetaschemaType: ndarray 'shape' value must be an array.");
    size_t ndim = type_doc["shape"].Size();
    size_t i;
    for (i = 0; i < ndim; i++) {
      if (!(type_doc["shape"][i].IsInt()))
	cislog_throw_error("NDArrayMetaschemaType: ndarray 'shape' elements must be integers.");
      shape_.push_back(type_doc["shape"][i].GetInt());
    }
    update_type("ndarray");
  }
  NDArrayMetaschemaType* copy() {
    return (new NDArrayMetaschemaType(subtype(), precision(), shape(), units()));
  }
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
  const size_t ndim() { return shape_.size(); }
  std::vector<size_t> shape() { return shape_; }
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
