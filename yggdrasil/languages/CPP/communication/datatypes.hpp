#ifndef YGGINTERFACEP_DATATYPES_HPP
#define YGGINTERFACEP_DATATYPES_HPP
#include <string>
#include "tools.hpp"
#include "regex.hpp"
#include <map>

#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"

class MetaschemaType;
/*! @brief Bit flags. */
#define HEAD_FLAG_VALID      0x00000001  //!< Set if the header is valid.
#define HEAD_FLAG_MULTIPART  0x00000002  //!< Set if the header is for a multipart message
#define HEAD_TYPE_IN_DATA    0x00000004  //!< Set if the type is stored with the data during serialization
#define HEAD_AS_ARRAY        0x00000008  //!< Set if messages will be serialized arrays
#define MSG_HEAD_SEP "YGG_MSG_HEAD"

enum fields  {ADDRESS, ID, REQUEST_ID, RESPONSE_ADDRESS, ZMQ_REPLY, ZMQ_REPLY_WORKER, MODEL};
const std::map<fields, std::string> string_fields = {{ADDRESS, "address"},
                                                     {ID, "id"},
                                                     {REQUEST_ID, "request_id"},
                                                     {RESPONSE_ADDRESS, "response_address"},
                                                     {ZMQ_REPLY, "zmq_reply"},
                                                     {ZMQ_REPLY_WORKER, "zmq_reply_worker"},
                                                     {MODEL, "model"}};

class DataType {
public:
    DataType(MetaschemaType* type_class=nullptr, const bool use_generic=false);
    DataType(const bool use_generic);
    DataType(void* type_doc, const bool use_generic);
    DataType(PyObject* pyobj, const bool use_generic);
    const size_t precision();
    const std::string subtype();
    const std::string name();
    bool empity();
    ~DataType() {
        delete obj;
    }
protected:
    std::string type; //!< Type name
    bool use_generic; //!< Flag for empty dtypes to specify generic in/out
    MetaschemaType *obj; //!< MetaschemaType Pointer
    void init_dtype_class(MetaschemaType* type_class);
};

class comm_head_t {
public:
    comm_head_t(Address* adr = nullptr, const std::string id = "");
    comm_head_t(const char* buf, const size_t buf_siz);
    ~comm_head_t();

    size_t bodysiz; //!< Size of body.
    size_t bodybeg; //!< Start of body in header.
    int flags; //!< Bit flags encoding the status of the header.
    int nargs_populated; //!< Number of arguments populated during deserialization.
    //
    size_t size; //!< Size of incoming message.
    Address* address; //!< Address that message will comm in on.
    std::string id; //!< Unique ID associated with this message.
    Address* response_address; //!< Response address.
    std::string request_id; //!< Request id.
    Address* zmq_reply; //!< Reply address for ZMQ sockets.
    Address* zmq_reply_worker; //!< Reply address for worker socket.
    std::string model; //!< Name of model that sent the header.
    // These should be removed once JSON fully implemented
    int serializer_type; //!< Code indicating the type of serializer.
    std::string format_str; //!< Format string for serializer.
    std::string field_names; //!< String containing field names.
    std::string field_units; //!< String containing field units.
    //
    DataType* dtype; //!< Type structure.
private:
    bool update_header_from_doc(rapidjson::Value &head_doc);
};

int split_head_body(const char *buf, const size_t buf_siz,
                    char **head, size_t *headsiz);

#endif //YGGINTERFACEP_DATATYPES_HPP
