#ifndef ANY_METASCHEMA_TYPE_H_
#define ANY_METASCHEMA_TYPE_H_

#include "../tools.h"
#include "utils.h"
#include "datatypes.h"
#include "MetaschemaType.h"


/*!
  @brief Base class for metaschema type definition that allows any object.

  The AnyMetaschemaType provides basic functionality for encoding/decoding
  datatypes from/to JSON style strings.
 */
class AnyMetaschemaType : public MetaschemaType{
public:
  /*!
    @brief Constructor for AnyMetaschemaType.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  AnyMetaschemaType(const bool use_generic=true,
		    const MetaschemaType* temp_type=NULL) :
    MetaschemaType("any", true, use_generic), temp_type_(NULL) {
    if (temp_type != NULL)
      temp_type_ = temp_type->copy();
  }
  /*!
    @brief Constructor for AnyMetaschemaType from a JSON type defintion.
    @param[in] type_doc rapidjson::Value rapidjson object containing
    the type definition from a JSON encoded header.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  AnyMetaschemaType(const rapidjson::Value &type_doc,
		    const bool use_generic=true) :
    MetaschemaType(type_doc, true, use_generic), temp_type_(NULL) {
    if (!(type_doc.HasMember("temptype")))
      ygglog_throw_error("AnyMetaschemaType: Parsed header dosn't contain a temptype.");
    if (!(type_doc["temptype"].IsObject()))
      ygglog_throw_error("AnyMetaschemaType: Temporary type in parsed header is not an object.");
    temp_type_ = (MetaschemaType*)type_from_doc_c(&(type_doc["temptype"]), true);
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType: Failed to get temporary type from document.");
    }
  }
  /*!
    @brief Constructor for AnyMetaschemaType from Python dictionary.
    @param[in] pyobj PyObject* Python object.
    @param[in] use_generic bool If true, serialized/deserialized
    objects will be expected to be YggGeneric classes.
   */
  AnyMetaschemaType(PyObject* pyobj, const bool use_generic=true) :
    MetaschemaType(pyobj, true, use_generic) {}
  /*!
    @brief Copy constructor.
    @param[in] other AnyMetaschemaType* Instance to copy.
   */
  AnyMetaschemaType(const AnyMetaschemaType &other) :
    AnyMetaschemaType(other.use_generic()) {}
  /*!
    @brief Destructor for MetaschemaType.
    Free the type string malloc'd during constructor.
   */
  virtual ~AnyMetaschemaType() {
    if (temp_type_ != NULL) {
      delete temp_type_;
      temp_type_ = NULL;
    }
  }
  /*!
    @brief Equivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instance is equivalent, false otherwise.
   */
  bool operator==(const MetaschemaType &Ref) const override {
    if (!(MetaschemaType::operator==(Ref)))
      return false;
    const AnyMetaschemaType* pRef = dynamic_cast<const AnyMetaschemaType*>(&Ref);
    if (pRef->temp_type() == NULL) {
      if (temp_type_ != NULL)
	return false;
    } else if (temp_type_ == NULL) {
      if (pRef->temp_type() != NULL)
	return false;
    } else {
      if ((*(pRef->temp_type())) != (*temp_type_))
	return false;
    }
    return true;
  }
  /*!
    @brief Inequivalence operator.
    @param[in] Ref MetaschemaType instance to compare against.
    @returns bool true if the instances are not equivalent, false otherwise.
   */
  bool operator!=(const AnyMetaschemaType &Ref) const {
    if (operator==(Ref))
      return false;
    else
      return true;
  }
  /*!
    @brief Get the temporary type.
    @returns MetaschemaType* Pointer to temporary type.
   */
  const MetaschemaType* temp_type() const {
    return temp_type_;
  }
  /*!
    @brief Create a copy of the type.
    @returns AnyMetaschemaType* Pointer to new AnyMetaschemaType instance with the same data.
   */
  AnyMetaschemaType* copy() const override {
    return (new AnyMetaschemaType(use_generic(),
				  temp_type()));
  }
  /*!
    @brief Print information about the type to stdout.
    @param[in] indent char* Indentation to add to display output.
  */
  void display(const char* indent="") const override {
    MetaschemaType::display(indent);
    if (temp_type_ != NULL) {
      printf("%s%-15s = %s\n", indent, "temptype", "");
      char new_indent[100] = "";
      strcat(new_indent, indent);
      strcat(new_indent, "    ");
      temp_type_->display(new_indent);
    }
  }
  /*!
    @brief Get type information as a Python dictionary.
    @returns PyObject* Python dictionary.
   */
  PyObject* as_python_dict() const override {
    PyObject* out = MetaschemaType::as_python_dict();
    PyObject* py_temp_type = temp_type_->as_python_dict();
    set_item_python_dict(out, "temptype", py_temp_type,
			 "AnyMetaschemaType::as_python_dict: temptype: ",
			 T_OBJECT);
    return out;
  }
  /*!
    @brief Copy data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
    @returns void* Pointer to copy of data.
   */
  void* copy_generic(const YggGeneric* data, void* orig_data=NULL) const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::copy_generic: Temp type is NULL.");
    }
    return temp_type_->copy_generic(data);
  }
  /*!
    @brief Free data wrapped in YggGeneric class.
    @param[in] data YggGeneric* Pointer to generic object.
   */
  void free_generic(YggGeneric* data) const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::free_generic: Temp type is NULL.");
    }
    temp_type_->free_generic(data);
  }
  /*!
    @brief Display data.
    @param[in] data YggGeneric* Pointer to generic object.
    @param[in] indent char* Indentation to add to display output.
   */
  void display_generic(const YggGeneric* data, const char* indent="") const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::display_generic: Temp type is NULL.");
    }
    temp_type_->display_generic(data, indent);
  }
  /*!
    @brief Update the type object with info from another type object.
    @param[in] new_info MetaschemaType* type object.
   */
  void update(const MetaschemaType* new_info) override {
    if (temp_type_ != NULL) {
      delete temp_type_;
      temp_type_ = NULL;
    }
    MetaschemaType::update(new_info);
    const AnyMetaschemaType* new_info_any = dynamic_cast<const AnyMetaschemaType*>(new_info);
    temp_type_ = new_info_any->temp_type()->copy();
  }
  /*!
    @brief Update the type object with info from provided variable arguments for serialization.
    @param[in,out] nargs size_t Number of arguments contained in ap. On output
    the number of unused arguments will be assigned to this address.
    @param[in] ap va_list_t Variable argument list.
    @returns size_t Number of arguments in ap consumed.
   */
  size_t update_from_serialization_args(size_t *nargs, va_list_t &ap) override {
    size_t out = MetaschemaType::update_from_serialization_args(nargs, ap);
    if (use_generic())
      return out;
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::update_from_serialization_args: Temp type is NULL.");
    }
    return temp_type_->update_from_serialization_args(nargs, ap);
  }
  // /*!
  //   @brief Update the type object with info from provided variable arguments for deserialization.
  //   @param[in,out] x YggGeneric* Pointer to generic object where data will be stored.
  //  */
  // void update_from_deserialization_args(YggGeneric* x) override {
  //   if (temp_type_ == NULL) {
  //     ygglog_throw_error("AnyMetaschemaType::update_from_deserialization_args: Temp type is NULL.");
  //   }
  //   x->free_data();
  //   x->free_type();
  //   x->set_type(temp_type_);
  //   x->set_nbytes(temp_type_->nbytes());
  // }
  /*!
    @brief Get the number of elements in the type.
    @returns size_t Number of elements (1 for scalar).
   */
  const size_t nelements() const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::nelements: Temp type is NULL.");
    }
    return temp_type_->nelements();
  }
  /*!
    @brief Determine if the number of elements is variable.
    @returns bool true if the number of elements can change, false otherwise.
  */
  const bool variable_nelements() const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::variable_nelements: Temp type is NULL.");
    }
    return temp_type_->variable_nelements();
  }
  /*!
    @brief Get the item size.
    @returns size_t Size of item in bytes.
   */
  const size_t nbytes() const override {
    if (temp_type_ == NULL) {
      // ygglog_throw_error("AnyMetaschemaType::nbytes: Temp type is NULL.");
      return 0;
    }
    return temp_type_->nbytes();
  }
  /*!
    @brief Get the number of arguments expected to be filled/used by the type.
    @returns size_t Number of arguments.
   */
  size_t nargs_exp() const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::nargs_exp: Temp type is NULL.");
    }
    return temp_type_->nargs_exp();
  }
  /*!
    @brief Convert a Python representation to a C representation.
    @param[in] pyobj PyObject* Pointer to Python object.
    @returns YggGeneric* Pointer to C object.
   */
  YggGeneric* python2c(PyObject* pyobj) const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::python2c: Temp type is NULL.");
    }
    return temp_type_->python2c(pyobj);
  }
  /*!
    @brief Convert a C representation to a Python representation.
    @param[in] cobj YggGeneric* Pointer to C object.
    @returns PyObject* Pointer to Python object.
   */
  PyObject* c2python(YggGeneric *cobj) const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::c2python: Temp type is NULL.");
    }
    return temp_type_->c2python(cobj);
  }
  
  // Encoding
  /*!
    @brief Encode the type's properties in a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_type_prop(rapidjson::Writer<rapidjson::StringBuffer> *writer) const override {
    MetaschemaType::encode_type_prop(writer);
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::encode_type_prop: Temp type is NULL.");
    }
    writer->Key("temptype");
    return temp_type_->encode_type(writer);
  }
  /*!
    @brief Encode arguments describine an instance of this type into a JSON string.
    @param[in] writer rapidjson::Writer<rapidjson::StringBuffer> rapidjson writer.
    @param[in] x YggGeneric* Pointer to generic wrapper for data.
    @returns bool true if the encoding was successful, false otherwise.
   */
  bool encode_data(rapidjson::Writer<rapidjson::StringBuffer> *writer,
		   YggGeneric* x) const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::encode_data: Temp type is NULL.");
    }
    return temp_type_->encode_data(writer, x);
  }
  
  // Decoding
  /*!
    @brief Decode variables from a JSON string.
    @param[in] data rapidjson::Value Reference to entry in JSON string.
    @param[out] x YggGeneric* Pointer to generic object where data should be stored.
    @returns bool true if the data was successfully decoded, false otherwise.
   */
  bool decode_data(rapidjson::Value &data, YggGeneric* x) const override {
    if (temp_type_ == NULL) {
      ygglog_throw_error("AnyMetaschemaType::decode_data: Temp type is NULL.");
    }
    return temp_type_->decode_data(data, x);
  }
  
private:
  MetaschemaType *temp_type_;
};


#endif /*ANY_METASCHEMA_TYPE_H_*/
// Local Variables:
// mode: c++
// End:
