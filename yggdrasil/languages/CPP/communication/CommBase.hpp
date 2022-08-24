#ifndef YGGDRASIL_COMMBASE_HPP
#define YGGDRASIL_COMMBASE_HPP

#include "tools.hpp"

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


/*! @brief Communicator types. */
enum comm_enum { NULL_COMM, IPC_COMM, ZMQ_COMM,
    SERVER_COMM, CLIENT_COMM,
    ASCII_FILE_COMM, ASCII_TABLE_COMM, ASCII_TABLE_ARRAY_COMM };
typedef enum comm_enum comm_type;
#define COMM_NAME_SIZE 100
#define COMM_ADDRESS_SIZE 500
#define COMM_DIR_SIZE 100

/*!
  @brief Communication structure.
 */
 template <typename H>
class CommBase {
public:
    CommBase(const std::string &name = "", const std::string &address = "", const std::string & direction = "",
             const comm_type &t = NULL_COMM, DataType* datatype = nullptr);
    ~CommBase();
    //void display_other(CommBase* other);
    //void empty();
    virtual int send(const std::string &data);
    virtual int send_nolimit(const std::string &data);
    virtual int recv(std::string &data);
    virtual void open();
    virtual void close();

protected:
    comm_type type; //!< Comm type.
    //void *other; //!< Pointer to additional information for the comm.
    std::string name; //!< Comm name.
    std::string address; //!< Comm address.
    std::string direction; //!< send or recv for direction messages will go.
    int flags; //!< Flags describing the status of the comm.
    int *const_flags;  //!< Flags describing the status of the comm that can be est for const.
    H *handle; //!< Pointer to handle for comm.   MAKE TEMPLATE???
    void *info; //!< Pointer to any extra info comm requires.
    DataType *datatype; //!< Data type for comm messages.
    size_t maxMsgSize; //!< The maximum message size.
    size_t msgBufSize; //!< The size that should be reserved in messages.
    int index_in_register; //!< Index of the comm in the comm register.
    time_t *last_send; //!< Clock output at time of last send.
    void *reply; //!< Reply information.
    int thread_id; //!< ID for the thread that created the comm.
};

/*inline
CommBase* new_comm_base(const std::string &address, const std::string &direction, const comm_type &t,
                        DataType* datatype) {
    return new CommBase("", address, direction, t, datatype);
}

inline
CommBase* init_comm_base(const std::string &name, const std::string &direction, const comm_type &t,
                         DataType* datatype) {
    return new CommBase(name, "", direction, t, datatype);
}*/
#endif //YGGDRASIL_COMMBASE_HPP
