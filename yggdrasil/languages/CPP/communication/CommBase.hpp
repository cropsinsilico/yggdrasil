#ifndef YGGDRASIL_COMMBASE_HPP
#define YGGDRASIL_COMMBASE_HPP

#include "tools.hpp"
#include "datatypes.hpp"

/*! @brief Bit flags. */
#define COMM_FLAG_VALID   0x00000001  //!< Set if the comm is initialized
#define COMM_FLAG_GLOBAL  0x00000002  //!< Set if the comm is global
#define COMM_FLAG_FILE    0x00000004  //!< Set if the comm connects to a file
#define COMM_FLAG_WORKER  0x00000008  //!< Set if the comm is a work comm
#define COMM_FLAG_CLIENT  0x00000010  //!< Set if the comm is a client
#define COMM_FLAG_SERVER  0x00000020  //!< Set if the comm is a server
#define COMM_FLAG_CLIENT_RESPONSE 0x00000040 //!< Set if the comm is a client response comm
#define COMM_ALWAYS_SEND_HEADER   0x00000080 //!< Set if the comm should always include a header in messages
#define COMM_ALLOW_MULTIPLE_COMMS 0x00000100 //!< Set if the comm should connect in a way that allow multiple connections

/*! @brief Bit flags that can be set for const comm */
#define COMM_FLAGS_USED   0x00000001  //!< Set if the comm has been used
#define COMM_EOF_SENT     0x00000002  //!< Set if EOF has been sent
#define COMM_EOF_RECV     0x00000004  //!< Set if EOF has been received

/*! @brief Set if the comm is the receiving comm for a client/server request connection */
#define COMM_FLAG_RPC     COMM_FLAG_SERVER | COMM_FLAG_CLIENT
#define COMM_NAME_SIZE 100
#define COMM_DIR_SIZE 100

namespace communicator {

/*! @brief Communicator types. */
enum comm_enum {
    NULL_COMM, IPC_COMM, ZMQ_COMM,
    SERVER_COMM, CLIENT_COMM,
    ASCII_FILE_COMM, ASCII_TABLE_COMM, ASCII_TABLE_ARRAY_COMM
};
enum Direction {
    SEND, NONE, RECV
};
typedef enum comm_enum comm_type;

/*!
      @brief Communication structure.
     */
template<typename H, typename R>
class CommBase {
public:
    CommBase(Address *address, const Direction direction,
             const comm_type &t, DataType *datatype);

    explicit CommBase(const std::string &name, const Direction direction = NONE,
                      const comm_type &t = NULL_COMM, DataType *datatype = nullptr);

    ~CommBase();

    //void display_other(CommBase* other);
    //void empty();
    virtual int send(const std::string &data) = 0;

    virtual int send_nolimit(const std::string &data) = 0;

    virtual int recv(std::string &data) = 0;

    //virtual void open();

    //virtual void close();

    virtual int comm_nmsg() = 0;

    bool valid() const {return _valid;}
protected:
    int check(const std::string &data) const;

    comm_type type; //!< Comm type.
    //void *other; //!< Pointer to additional information for the comm.
    std::string name; //!< Comm name.
    Address *address; //!< Comm address.
    Direction direction; //!< send or recv for direction messages will go.
    int flags; //!< Flags describing the status of the comm.
    int *const_flags;  //!< Flags describing the status of the comm that can be est for const.
    H *handle; //!< Pointer to handle for comm.
    void *info; //!< Pointer to any extra info comm requires.
    DataType *datatype; //!< Data type for comm messages.
    size_t maxMsgSize; //!< The maximum message size.
    size_t msgBufSize; //!< The size that should be reserved in messages.
    int index_in_register; //!< Index of the comm in the comm register.
    time_t *last_send; //!< Clock output at time of last send.
    R *reply; //!< Reply information.
    int thread_id; //!< ID for the thread that created the comm.
    bool _valid;
};

/*inline
    CommBase<void>* new_comm_base(const Address &address, const Direction direction, const comm_type &t,
                            DataType* datatype) {
        return new CommBase<void>("", address, direction, t, datatype);
    }

    inline
    CommBase<void>* init_comm_base(const std::string &name, const Direction direction, const comm_type &t,
                             DataType* datatype) {
        return new CommBase<void>(name, Address(), direction, t, datatype);
    }*/

template<typename H, typename R>
CommBase<H, R>::CommBase(Address *address, const Direction direction, const comm_type &t, DataType *datatype) :
        address(address), type(t), _valid(false) {
    type = NULL_COMM;
    //other = NULL_ptr;
    name = "";

    flags |= COMM_FLAG_VALID;
    if (direction == NONE) {
        flags &= ~COMM_FLAG_VALID;
        this->direction = NONE;
    } else {
        this->direction = direction;
    }

    datatype = complete_dtype(datatype, false);
    if (datatype == nullptr)
        EXCEPTION;
    maxMsgSize = YGG_MSG_MAX;
    const_flags = nullptr;
    thread_id = get_thread_id();
    char *allow_threading = getenv("YGG_THREADING");
    if (allow_threading != nullptr)
        flags |= COMM_ALLOW_MULTIPLE_COMMS;

    handle = nullptr;
    info = nullptr;
    msgBufSize = 0;
    index_in_register = -1;
    last_send = nullptr;
    reply = nullptr;
}

template<typename H, typename R>
CommBase<H, R>::CommBase(const std::string &name, const Direction direction, const comm_type &t,
                         DataType *datatype) :
        CommBase(new Address(), direction, t, datatype) {
    std::string full_name;
    if (!name.empty()) {
        full_name = name;
        if (full_name.size() > COMM_NAME_SIZE)
            full_name.resize(COMM_NAME_SIZE);
        if (direction != NONE) {
            if (direction == SEND) {
                full_name += "_OUT";
            } else if (direction == RECV) {
                full_name += "_IN";
            }
        }
        char *model_name = getenv("YGG_MODEL_NAME");
        char *addr = std::getenv(full_name.c_str());
        if (addr == nullptr && model_name != nullptr) {
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
        this->name = full_name;
        if (addr != nullptr) {
            this->address.address(addr);
        }
        this->name = name;
    } else {
        flags &= ~COMM_FLAG_VALID;
    }

    if (!this->address.valid() && t != SERVER_COMM && t != CLIENT_COMM) {
        ygglog_error("init_comm_base: %s not registered as environment variable.\n",
                     full_name.c_str());
        flags &= ~COMM_FLAG_VALID;
    }
    ygglog_debug("init_comm_base(%s): Done", name.c_str());
}

template<typename H, typename R>
CommBase<H, R>::~CommBase() {
    ygglog_debug("~CommBase: Started");
    if (last_send != nullptr)
        delete last_send;
    if (const_flags != nullptr)
        delete const_flags;
    if (datatype != nullptr)
        delete datatype;
    if (address != nullptr)
        delete address;
    ygglog_debug("~CommBase: Finished");
}

/*void CommBase::display_other(CommBase* x) {
        if (x->other != NULL_ptr) {
            comm_t* other = (comm_t*)(x->other);
            printf("type(%s) = %d\n", other->name, (int)(other->type));
        }
    }*/

template<typename H, typename R>
int CommBase<H, R>::check(const std::string &data) const {
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

}

#endif //YGGDRASIL_COMMBASE_HPP
