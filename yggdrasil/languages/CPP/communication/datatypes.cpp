#include "datatypes.hpp"

comm_head_t::comm_head_t(Address* adr, std::string id): address(adr), id(id){
    // Parameters set during read
    bodysiz = 0;
    bodybeg = 0;
    flags = HEAD_FLAG_VALID;
    nargs_populated = 0;
    // Parameters sent in header
    //out.size = size;
    response_address = nullptr;
    request_id = "";
    zmq_reply = nullptr;
    zmq_reply_worker = nullptr;
    model = "";
    // Parameters that will be removed
    serializer_type = -1;
    format_str = "";
    // Parameters used for type
    dtype = nullptr;
}

/*!
  @brief Split header and body of message.
  @param[in] buf const char* Message that should be split.
  @param[in] buf_siz size_t Size of buf.
  @param[out] head const char** pointer to buffer where the extracted header
  should be stored.
  @param[out] headsiz size_t reference to memory where size of extracted header
  should be stored.
  @returns: int 0 if split is successful, -1 if there was an error.
*/
int split_head_body(const char *buf, const size_t buf_siz,
                    char **head, size_t *headsiz) {
    // Split buffer into head and body
    int ret;
    size_t sind, eind, sind_head, eind_head;
    sind = 0;
    eind = 0;
#ifdef _WIN32
    // Windows regex of newline is buggy
  UNUSED(buf_siz);
  size_t sind1, eind1, sind2, eind2;
  char re_head_tag[COMMBUFFSIZ];
  sprintf(re_head_tag, "(%s)", MSG_HEAD_SEP);
  ret = find_match(re_head_tag, buf, &sind1, &eind1);
  if (ret > 0) {
    sind = sind1;
    ret = find_match(re_head_tag, buf + eind1, &sind2, &eind2);
    if (ret > 0)
      eind = eind1 + eind2;
  }
#else
    // Extract just header
    char re_head[COMMBUFFSIZ] = MSG_HEAD_SEP;
    strcat(re_head, "(.*)");
    strcat(re_head, MSG_HEAD_SEP);
    // strcat(re_head, ".*");
    ret = find_match(re_head, buf, &sind, &eind);
#endif
    if (ret < 0) {
        ygglog_error("split_head_body: Could not find header in '%.1000s'", buf);
        return -1;
    } else if (ret == 0) {
#ifdef YGG_DEBUG
        ygglog_debug("split_head_body: No header in '%.1000s...'", buf);
#endif
        sind_head = 0;
        eind_head = 0;
    } else {
        sind_head = sind + strlen(MSG_HEAD_SEP);
        eind_head = eind - strlen(MSG_HEAD_SEP);
    }
    headsiz[0] = (eind_head - sind_head);
    char* temp = (char*)realloc(*head, *headsiz + 1);
    if (temp == nullptr) {
        ygglog_error("split_head_body: Failed to reallocate header.");
        return -1;
    }
    *head = temp;
    memcpy(*head, buf + sind_head, *headsiz);
    (*head)[*headsiz] = '\0';
    return 0;
};

comm_head_t::comm_head_t(const char *buf, const size_t buf_siz) {
    int ret;
    char *head = nullptr;
    size_t headsiz;
    try {
        // Split header/body
        ret = split_head_body(buf, buf_siz, &head, &headsiz);
        if (ret < 0) {
            ygglog_error("parse_comm_header: Error splitting head and body.");
            flags &= ~HEAD_FLAG_VALID;
            if (head != NULL)
                free(head);
            return;
        }
        bodybeg = headsiz + 2*strlen(MSG_HEAD_SEP);
        bodysiz = buf_siz - bodybeg;
        // Handle raw data without header
        if (headsiz == 0) {
            flags &= ~HEAD_FLAG_MULTIPART;
            size = bodysiz;
            free(head);
            return;
        }
        // Parse header
        rapidjson::Document head_doc;
        head_doc.Parse(head, headsiz);
        if (!(head_doc.IsObject()))
            ygglog_throw_error("parse_comm_header: Parsed header document is not an object.");
        DataType* dtype;
        if (head_doc.HasMember("datatype")) {
            dtype = new DataType(type_from_header_doc(head_doc));
        } else if (head_doc.HasMember("type_in_data")) {
            dtype = NULL;
        } else {
            dtype = create_dtype_direct();
        }
        if (!(update_header_from_doc(head_doc))) {
            ygglog_error("parse_comm_header: Error updating header from JSON doc.");
            flags &= ~HEAD_FLAG_VALID;
            delete dtype;
            dtype = nullptr;
            free(head);
            return;
        }
        free(head);
    } catch(...) {
        ygglog_error("parse_comm_header: C++ exception thrown.");
        flags &= ~HEAD_FLAG_VALID;
        if (head != nullptr)
            free(head);
    }
}

bool comm_head_t::update_header_from_doc(rapidjson::Value &head_doc) {
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
    size = (size_t)(head_doc["size"].GetInt());
    if (bodysiz < size) {
        flags |= HEAD_FLAG_MULTIPART;
    } else {
        flags &= ~HEAD_FLAG_MULTIPART;
    }
    // Flag specifying that type is in data
    if (head_doc.HasMember("type_in_data")) {
        if (!(head_doc["type_in_data"].IsBool())) {
            ygglog_error("update_header_from_doc: type_in_data is not boolean.");
            return false;
        }
        if (head_doc["type_in_data"].GetBool()) {
            flags |= HEAD_TYPE_IN_DATA;
        } else {
            flags &= ~HEAD_TYPE_IN_DATA;
        }
    }
    // String fields


    for (const auto& n : string_fields) {
        if (head_doc.HasMember(n.second.c_str())) {
            if (!(head_doc[n.second.c_str()].IsString())) {
                ygglog_error("update_header_from_doc: '%s' is not a string.", n.second.c_str());
                return false;
            }
            const std::string value(head_doc[n.second.c_str()].GetString());
            if (value.size() > COMMBUFFSIZ) {
                ygglog_error("update_header_from_doc: Size of value for key '%s' (%d) exceeds size of target buffer (%d).",
                             n.second.c_str(), std::to_string(value.size()).c_str(), COMMBUFFSIZ);
                return false;
            }
            switch (n.first) {
                case ADDRESS:
                    if (address != nullptr)
                        delete address;
                    address = new Address(value);
                    break;
                case ID:
                    id = value;
                    break;
                case REQUEST_ID:
                    request_id = value;
                    break;
                case RESPONSE_ADDRESS:
                    if (response_address != nullptr)
                        delete response_address;
                    response_address = new Address(value);
                    break;
                case ZMQ_REPLY:
                    if (zmq_reply != nullptr)
                        delete zmq_reply;
                    zmq_reply = new Address(value);
                    break;
                case ZMQ_REPLY_WORKER:
                    if (zmq_reply_worker != nullptr)
                        delete zmq_reply_worker;
                    zmq_reply_worker = new Address(value);
                    break;
                case MODEL:
                    model = value;
                    break;
            }
        }
    }

    // Return
    return true;
}

comm_head_t::~comm_head_t() {
    if (dtype != nullptr)
        delete dtype;
    if (address != nullptr)
        delete address;
    if (response_address != nullptr)
        delete response_address;
    if (zmq_reply != nullptr)
        delete zmq_reply;
    if (zmq_reply_worker != nullptr)
        delete zmq_reply_worker;
}
DataType::DataType(MetaschemaType* type_class, const bool use_generic) {
    type = "";
    this->use_generic = use_generic;
    obj = nullptr;
    if (type_class != nullptr) {
        try {
            init_dtype_class(type_class);
        } catch (...) {
            ygglog_throw_error("create_dtype: Failed to initialized data type structure with class information.");
        }
    }
}

void DataType::init_dtype_class(MetaschemaType* type_class) {
    if (obj != nullptr) {
        ygglog_throw_error("init_dtype_class: Data type class already set.");
    } else if (!type.empty()) {
        ygglog_throw_error("init_dtype_class: Data type string already set.");
    }
    obj = type_class;
    //TODO:
    ///use_generic = type_class->use_generic();
    ///strncpy(dtype->type, type_class->type(), COMMBUFFSIZ);
}