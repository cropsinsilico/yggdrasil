#include "CommBase.hpp"

CommBase::CommBase() {
    type = NULL_COMM;
    //other = NULL_ptr;
    name = "";
    address = "";
    direction = "";
    flags = COMM_ALWAYS_SEND_HEADER|COMM_FLAG_VALID;
    handle = nullptr;
    info = nullptr;
    datatype = nullptr;
    maxMsgSize = 0;
    msgBufSize = 0;
    index_in_register = -1;
    last_send = nullptr;
    reply = nullptr;
    thread_id = 0;
}

CommBase::CommBase(const std::string &name, const std::string &address, const std::string &direction, const comm_type &t, DataType* datatype) : type(t) {
    std::string inadr = address;
    std::string full_name;
    if (!name.empty()) {
        full_name = name;
        if (full_name.size() > COMM_NAME_SIZE)
            full_name.resize(COMM_NAME_SIZE);
        if (!direction.empty()) {
            if (is_send(direction)) {
                full_name += "_OUT";
            } else if (is_recv(direction)) {
                full_name += "_IN";
            }
        }
        char* model_name = getenv("YGG_MODEL_NAME");
        char* addr = std::getenv(full_name.c_str());
        if (addr == nullptr && model_name!= nullptr) {
            std::string prefix(model_name);
            prefix += ":";
            if (prefix.size() > COMM_NAME_SIZE)
                prefix.resize(COMM_NAME_SIZE);
            if (full_name.rfind(prefix, 0) != 0) {
                prefix += full_name;
                full_name = prefix;
                addr = std::getenv(full_name.c_str());
            }
        }
        if (addr == nullptr) {
            std::string temp_name(full_name);
            size_t loc;
            while ((loc = temp_name.find(":")) != std::string::npos) {
                temp_name.replace(loc, 1, "__COLON__");
            }
            addr = getenv(temp_name.c_str());
        }
        ygglog_debug("init_comm_base: model_name = %s, full_name = %s, address = %s",
                     model_name, full_name.c_str(), addr);
        inadr = addr;
        this->name = full_name;
    } else {
        flags &= ~COMM_FLAG_VALID;
    }
    if (!inadr.empty()) {
        this->address = inadr;
        if (this->address.size() > COMM_ADDRESS_SIZE)
            this->address.resize(COMM_ADDRESS_SIZE);
    }
    if (direction.empty()) {
        flags &= ~COMM_FLAG_VALID;
    } else {
        this->direction = direction;
        if (this->direction.size() > COMM_DIR_SIZE)
            this->direction.resize(COMM_DIR_SIZE);
    }
    datatype = complete_dtype(datatype, false);
    if (datatype == nullptr)
        EXCEPTION;
    maxMsgSize = YGG_MSG_MAX;
    last_send = nullptr;
    const_flags = nullptr;
    thread_id = get_thread_id();
    char *allow_threading = getenv("YGG_THREADING");
    if (allow_threading != nullptr)
        flags |= COMM_ALLOW_MULTIPLE_COMMS;
    if (this->address.empty() && t != SERVER_COMM && t != CLIENT_COMM) {
        ygglog_error("init_comm_base: %s not registered as environment variable.\n",
                     full_name.c_str());
        flags &= ~COMM_FLAG_VALID;
    }
}

CommBase::~CommBase() {
    ygglog_debug("~CommBase: Started");
    if (last_send != nullptr)
        delete last_send;
    if (const_flags != nullptr)
        delete const_flags;
    if (datatype != nullptr)
        delete datatype;
    ygglog_debug("~CommBase: Finished");
}

/*void CommBase::display_other(CommBase* x) {
    if (x->other != NULL_ptr) {
        comm_t* other = (comm_t*)(x->other);
        printf("type(%s) = %d\n", other->name, (int)(other->type));
    }
}*/

int CommBase::send(const std::string &data) {
      // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(data);
#endif
    // Make sure you arn't sending a message that is too big
    if (data.size() > YGG_MSG_MAX) {
        ygglog_error("comm_base_send(%s): message too large for single packet (YGG_MSG_MAX=%d, len=%d)",
                     name.c_str(), YGG_MSG_MAX, data.size());
        return -1;
    }
    return 0;
}
