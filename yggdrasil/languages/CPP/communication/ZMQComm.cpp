#include "ZMQComm.hpp"

#ifdef ZMQINSTALLED
#include "datatypes.hpp"
void* ZMQComm::ygg_s_process_ctx = nullptr;

/*!
  @brief Initialize a ZeroMQ communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
ZMQComm::ZMQComm(const std::string &name, Address *address, const Direction direction, DataType* datatype) :
        CommBase(address, direction, IPC_COMM, datatype) {
    sock = nullptr;

    if (!(flags & COMM_FLAG_VALID))
        return;
    msgBufSize = 100;
    if (flags & (COMM_FLAG_SERVER | COMM_ALLOW_MULTIPLE_COMMS)) {
        handle = create_zsock(ZMQ_DEALER);
    } else {
        handle = create_zsock(ZMQ_PAIR);
    }
    if (handle == nullptr) {
        ygglog_error("init_zmq_address: Could not initialize empty socket.");
        flags &= ~COMM_FLAG_VALID;
        return;
    }
    int ret = zsock_connect(handle, "%s", this->address->address().c_str());
    if (ret == -1) {
        ygglog_error("init_zmq_address: Could not connect socket to address = %s",
                     this->address->address().c_str());
#ifdef _OPENMP
        ygg_zsock_destroy(&handle);
#else
        zsock_destroy(&handle);
#endif
        flags &= ~COMM_FLAG_VALID;
        return;
    }
    ygglog_debug("init_zmq_address: Connected socket to %s", this->address->address().c_str());
    if (this->name.empty()) {
        if (name.empty()) {
            this->name = "tempinitZMQ-" + this->address->address();
        }
        else {
            this->name = name;
        }
    }
    // Asign to void pointer
    init_reply();
    flags |= COMM_ALWAYS_SEND_HEADER;
}

void ZMQComm::init_reply() {
    if (reply != nullptr)
        delete reply;
    reply = new zmq_reply_t;
    reply->n_msg = 0;
    reply->n_rep = 0;
}
/*!
  @brief Initialize zeromq.
  @returns A zeromq context.
*/
#ifdef _OPENMP
void ZMQComm::init() {
#pragma omp critical (zmq)
    {
        if (ZMQComm::ygg_s_process_ctx == nullptr) {
            if (get_thread_id() == 0) {
                ygglog_debug("ygg_zsys_init: Creating ZMQ context.");
                ZMQComm::ygg_s_process_ctx = zsys_init();
                if (ZMQComm::ygg_s_process_ctx == nullptr) {
                    ygglog_error("ygg_zsys_init: ZMQ context is nullptr.");
                }
            } else {
                ygglog_error("ygg_zsys_init: Can only initialize the "
                             "zeromq context on the main thread. Call ygg_init "
                             "before the threaded portion of your model.");
            }
        }
    }
}
#else
#define ygg_zsys_init zsys_init
#endif


/*!
  @brief Shutdown zeromq.
 */
void ZMQComm::shutdown() {
#ifdef _OPENMP
#pragma omp critical (zmq)
    {
        zsys_shutdown();
        ZMQComm::ygg_s_process_ctx = nullptr;
    }
#else
    zsys_shutdown();
#endif
}

/*!
  @brief Get a new socket, using the exising context.
  @param[in] type int Socket type.
  @returns zsock_t* CZMQ socket wrapper struct.
*/
zsock_t* ZMQComm::new_zsock(const int &type) {
#ifdef _OPENMP
    // Recreation of czmq zsock_new that is OMP aware
    auto *self = new ygg_zsock_t();
    self->tag = 0xcafe0004;
    self->type = type;
    ZMQComm::init();
    if (ZMQComm::ygg_s_process_ctx == nullptr) {
        ygglog_error("ygg_zsock_new: Context is nullptr.");
        freen(self);
    }
#pragma omp critical (zmq)
    {
        self->handle = zmq_socket (ZMQComm::ygg_s_process_ctx, type);
    }
    if (!(self->handle)) {
        ygglog_error("ygg_zsock_new: Error creating new socket.");
        delete self;
        return nullptr;
    }
    return (zsock_t*)(self);
#else
    return zsock_new(type);
#endif
}

zsock_t* ZMQComm::create_zsock(const int &type) {
    zsock_t* out = new_zsock(type);
    zsock_set_linger(out, 0);
    zsock_set_immediate(out, 1);
    return out;
}


/*!
  @brief Add empty reply structure information to comm.
  @param[in] comm comm_t * Comm to initialize reply for.
  @returns int 0 if successfull, -1 otherwise.
 */

void ZMQComm::init_zmq_reply() {
    if (reply == nullptr)
        reply = new zmq_reply_t();
    else {
        reply->sockets.clear();
        reply->addresses.clear();
        reply->n_msg = 0;
        reply->n_rep = 0;
    }
}

/*!
  @brief Locate matching reply socket.
  @param[in] comm comm_t* Comm that should be checked for matching reply socket.
  @param[in] address char* Address that should be matched against.
  @returns int Index of matched socket, -1 if no match, -2 if error.
 */
int ZMQComm::find_reply_socket(Address *address) {
    Address* adr;
    if (address == nullptr)
        adr = this->address;
    else
        adr = address;
    // Get reply
    if (reply == nullptr) {
        ygglog_error("find_reply_socket(%s): Reply structure not initialized.", name.c_str());
        return -2;
    }
    for (int i = 0; i < reply->nsockets(); i++) {
        if (reply->addresses[i] == adr) {
            return i;
        }
    }
    return -1;
}

/*!
  @brief Request confirmation from receiving socket.
  @param[in] comm comm_t* Comm structure to do reply for.
  @returns int 0 if successful, -2 on EOF, -1 otherwise.
 */

int ZMQComm::do_reply_send() {
    // Get reply
    if (reply == nullptr) {
        ygglog_error("do_reply_send(%s): Reply structure not initialized.", name.c_str());
        return -1;
    }
    reply->n_msg++;
    if (reply->nsockets() == 0 || reply->sockets[0] == nullptr) {
        ygglog_error("do_reply_send(%s): Socket is nullptr.", name.c_str());
        return -1;
    }
    sock = reply->sockets[0];
    // Poll
    ygglog_debug("do_reply_send(%s): address=%s, begin", name.c_str(),
                 reply->addresses[0]->address().c_str());
#if defined(__cplusplus) && defined(_WIN32)
    // TODO: There seems to be an error in the poller when using it in C++
#else
    zpoller_t *poller = zpoller_new(sock, nullptr);
    if (!(poller)) {
        ygglog_error("do_reply_send(%s): Could not create poller", name.c_str());
        return -1;
    }
    assert(poller);
    ygglog_debug("do_reply_send(%s): waiting on poller...", name.c_str());
    void *p = zpoller_wait(poller, -1);
    //void *p = zpoller_wait(poller, 1000);
    ygglog_debug("do_reply_send(%s): poller returned", name.c_str());
    if (p == nullptr) {
        if (zpoller_terminated(poller)) {
            ygglog_error("do_reply_send(%s): Poller interrupted", name.c_str());
        } else if (zpoller_expired(poller)) {
            ygglog_error("do_reply_send(%s): Poller expired", name.c_str());
        } else {
            ygglog_error("do_reply_send(%s): Poller failed", name.c_str());
        }
        zpoller_destroy(&poller);
        return -1;
    }
    zpoller_destroy(&poller);
#endif
    // Receive
    zframe_t *msg = zframe_recv(sock);
    if (msg == nullptr) {
        ygglog_error("do_reply_send(%s): did not receive", name.c_str());
        return -1;
    }
    char *msg_data = (char*)zframe_data(msg);
    // Check for EOF
    int is_purge = 0;
    if (strcmp(msg_data, YGG_MSG_EOF) == 0) {
        ygglog_debug("do_reply_send(%s): EOF received", name.c_str());
        reply->n_msg = 0;
        reply->n_rep = 0;
        return -2;
    } else if (strcmp(msg_data, _purge_msg) == 0) {
        is_purge = 1;
    }
    // Send
    // zsock_set_linger(s, _zmq_sleeptime);
    int ret = zframe_send(&msg, sock, 0);
    // Check for purge or EOF
    if (ret < 0) {
        ygglog_error("do_reply_send(%s): Error sending reply frame.", name.c_str());
        zframe_destroy(&msg);
    } else {
        if (is_purge == 1) {
            ygglog_debug("do_reply_send(%s): PURGE received", name.c_str());
            reply->n_msg = 0;
            reply->n_rep = 0;
            ret = do_reply_send();
        } else {
            reply->n_rep++;
        }
    }
    ygglog_debug("do_reply_send(%s): address=%s, end", name.c_str(),
                 reply->addresses[0]->address().c_str());
#if defined(__cplusplus) && defined(_WIN32)
    // TODO: There seems to be an error in the poller when using it in C++
#else
    if (ret >= 0) {
        poller = zpoller_new(sock, nullptr);
        if (!(poller)) {
            ygglog_error("do_reply_send(%s): Could not create poller", name.c_str());
            return -1;
        }
        assert(poller);
        ygglog_debug("do_reply_send(%s): waiting on poller...", name.c_str());
        p = zpoller_wait(poller, 10);
        ygglog_debug("do_reply_send(%s): poller returned", name.c_str());
        zpoller_destroy(&poller);
    }
#endif
    return ret;
};

/*!
  @brief Send confirmation to sending socket.
  @param[in] comm comm_t* Comm structure to do reply for.
  @param[in] isock int Index of socket that reply should be done for.
  @param[in] msg char* Mesage to send/recv.
  @returns int 0 if successfule, -1 otherwise.
 */
int ZMQComm::do_reply_recv(const int &isock, const char *msg) {
    // Get reply

    if (reply->sockets.at(isock) == nullptr) {
        ygglog_error("do_reply_recv(%s): Socket is nullptr.", name.c_str());
        return -1;
    }
    sock = reply->sockets[isock];
    ygglog_debug("do_reply_recv(%s): address=%s, begin", name.c_str(),
                 reply->addresses[isock]->address().c_str());
    zframe_t *msg_send = zframe_new(msg, strlen(msg));
    if (msg_send == nullptr) {
        ygglog_error("do_reply_recv(%s): Error creating frame.", name.c_str());
        return -1;
    }
    // Send
    int ret = zframe_send(&msg_send, sock, 0);
    if (ret < 0) {
        ygglog_error("do_reply_recv(%s): Error sending confirmation.", name.c_str());
        zframe_destroy(&msg_send);
        return -1;
    }
    if (strcmp(msg, YGG_MSG_EOF) == 0) {
        ygglog_info("do_reply_recv(%s): EOF confirmation.", name.c_str());
        reply->n_msg = 0;
        reply->n_rep = 0;
        zsock_set_linger(sock, _zmq_sleeptime);
        return -2;
    }
    // Poll to prevent block
    ygglog_debug("do_reply_recv(%s): address=%s, polling for reply", name.c_str(),
                 reply->addresses[isock]->address().c_str());
#if defined(__cplusplus) && defined(_WIN32)
    // TODO: There seems to be an error in the poller when using it in C++
#else
    zpoller_t *poller = zpoller_new(sock, nullptr);
    if (!(poller)) {
        ygglog_error("do_reply_send(%s): Could not create poller", name.c_str());
        return -1;
    }
    assert(poller);
    ygglog_debug("do_reply_recv(%s): waiting on poller...", name.c_str());
    void *p = zpoller_wait(poller, 1000);
    ygglog_debug("do_reply_recv(%s): poller returned", name.c_str());
    if (p == nullptr) {
        if (zpoller_terminated(poller)) {
            ygglog_error("do_reply_recv(%s): Poller interrupted", name.c_str());
        } else if (zpoller_expired(poller)) {
            ygglog_error("do_reply_recv(%s): Poller expired", name.c_str());
        } else {
            ygglog_error("do_reply_recv(%s): Poller failed", name.c_str());
        }
        zpoller_destroy(&poller);
        return -1;
    }
    zpoller_destroy(&poller);
#endif
    // Receive
    zframe_t *msg_recv = zframe_recv(sock);
    if (msg_recv == nullptr) {
        ygglog_error("do_reply_recv(%s): did not receive", name.c_str());
        return -1;
    }
    zframe_destroy(&msg_recv);
    reply->n_rep++;
    ygglog_debug("do_reply_recv(%s): address=%s, end", name.c_str(),
                 reply->addresses[isock]->address().c_str());
    return 0;
};

/*!
  @brief Add reply socket information to a send comm.
  @param[in] comm comm_t* Comm that confirmation is for.
  @returns char* Reply socket address.
*/
std::string ZMQComm::set_reply_send() {
    std::string out = "";

    if (reply == nullptr) {
        ygglog_error("set_reply_send(%s): Reply structure not initialized.", name.c_str());
        return out;
    }
    // Create socket
    if (reply->nsockets() == 0) {
        reply->sockets.push_back(create_zsock(ZMQ_REP));
        if (reply->sockets[0] == nullptr) {
            ygglog_error("set_reply_send(%s): Could not initialize empty socket.",
                         name.c_str());
            return out;
        }
        char protocol[50] = "tcp";
        char host[50] = "localhost";
        if (strcmp(host, "localhost") == 0)
            strncpy(host, "127.0.0.1", 50);
        char address[100];
        int port = -1;
#ifdef _OPENMP
#pragma omp critical (zmqport)
        {
#endif
            if (_last_port_set == 0) {
                ygglog_debug("model_index = %s", getenv("YGG_MODEL_INDEX"));
                _last_port = 49152 + 1000 * atoi(getenv("YGG_MODEL_INDEX"));
                _last_port_set = 1;
                ygglog_debug("_last_port = %d", _last_port);
            }
            sprintf(address, "%s://%s:*[%d-]", protocol, host, _last_port + 1);
            port = zsock_bind(reply->sockets[0], "%s", address);
            if (port != -1)
                _last_port = port;
#ifdef _OPENMP
        }
#endif
        if (port == -1) {
            ygglog_error("set_reply_send(%s): Could not bind socket to address = %s",
                         name.c_str(), address);
            return out;
        }
        //sprintf(address, "%s://%s:%d", protocol, host, port);
        auto *adr = new Address(address);

        reply->addresses.push_back(adr);
        ygglog_debug("set_reply_send(%s): New reply socket: %s", name.c_str(), address);
    }
    return reply->addresses[0]->address();
}

/*!
  @brief Add reply socket information to a recv comm.
  @param[in] comm comm_t* Comm that confirmation is for.
  @returns int Index of the reply socket.
*/
int ZMQComm::set_reply_recv(Address* adr) {
    int out = -1;
    // Get reply
    if (reply == nullptr) {
        ygglog_error("set_reply_recv(%s): Reply structure not initialized.", name.c_str());
        return out;
    }
    // Match address and create if it dosn't exist
    int isock = find_reply_socket(adr);
    if (isock < 0) {
        if (isock == -2) {
            ygglog_error("set_reply_recv(%s): Error locating socket.", name.c_str());
            return out;
        }
        // Create new socket
        isock = reply->nsockets();
        reply->sockets.push_back(create_zsock(ZMQ_REQ));
        if (reply->sockets[isock] == nullptr) {
            ygglog_error("set_reply_recv(%s): Could not initialize empty socket.",
                         name.c_str());
            return out;
        }
        reply->addresses.push_back(adr);
        int ret = zsock_connect(reply->sockets[isock], "%s", adr->address().c_str());
        if (ret < 0) {
            ygglog_error("set_reply_recv(%s): Could not connect to socket.",
                         name.c_str());
            return out;
        }
        ygglog_debug("set_reply_recv(%s): New recv socket: %s", name.c_str(), address);
    }
    return isock;
};

/*!
  @brief Add information about reply socket to outgoing message.
  @param[in] comm comm_t* Comm that confirmation is for.
  @param[in] data char* Message that reply info should be added to.
  @param[in] len int Length of the outgoing message.
  @returns char* Message with reply information added.
 */
std::string ZMQComm::check_reply_send(const std::string& data) {
    return data;
};


/*!
  @brief Get reply information from message.
  @param[in] comm comm_* Comm structure for incoming message.
  @param[in, out] data char* Received message containing reply info that will be
  removed on return.
  @param[in] len size_t Length of received message.
  @returns int Length of message without the reply info. -1 if there is an error.
 */
int ZMQComm::check_reply_recv(std::string &data, const size_t &len) {
    int new_len = (int)len;
    int ret = 0;
    // Get reply
    if (reply == nullptr) {
        ygglog_error("check_reply_recv(%s): Reply structure not initialized.", name.c_str());
        return -1;
    }
    reply->n_msg++;
    // Extract address
    comm_head_t head(data.c_str(), len);
    if (!(head.flags & HEAD_FLAG_VALID)) {
        ygglog_error("check_reply_recv(%s): Invalid header.", name.c_str());
        return -1;
    }
    Address *adr;
    if ((flags & COMM_FLAG_WORKER) && (reply->nsockets() == 1)) {
        adr = reply->addresses[0];
    } else if (head.zmq_reply != nullptr) {
        adr = new Address(*head.zmq_reply);
    } else {
        ygglog_error("check_reply_recv(%s): Error parsing reply header in '%s'",
                     name.c_str(), data.c_str());
        return -1;
    }

    // Match address and create if it dosn't exist
    int isock = set_reply_recv(address);
    if (isock < 0) {
        ygglog_error("check_reply_recv(%s): Error setting reply socket.");
        return -1;
    }
    // Confirm message receipt
    ret = do_reply_recv(isock, _reply_msg);
    if (ret < 0) {
        ygglog_error("check_reply_recv(%s): Error during reply.", name.c_str());
        return -1;
    }
    return new_len;
};

/*!
  @brief Create a new socket.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
int ZMQComm::new_zmq_address() {
    // TODO: Get protocol/host from input
    std::string protocol = "tcp";
    std::string host = "localhost";
    auto *adr = new Address();
    msgBufSize = 100;
    if (host == "localhost")
        host = "127.0.0.1";
    if (protocol == "inproc" || protocol == "ipc") {
        // TODO: small chance of reusing same number
        int key = 0;
#ifdef _OPENMP
#pragma omp critical (zmqport)
        {
#endif
            if (!(_zmq_rand_seeded)) {
                srand(ptr2seed(this));
                _zmq_rand_seeded = 1;
            }
#ifdef _OPENMP
        }
#endif
        while (key == 0) key = rand();
        if (name.empty())
            name = "tempnewZMQ-" + std::to_string(key);
        adr->address(protocol + "://" + name);
    } else {
#ifdef _OPENMP
#pragma omp critical (zmqport)
        {
#endif
            if (_last_port_set == 0) {
                ygglog_debug("model_index = %s", getenv("YGG_MODEL_INDEX"));
                _last_port = 49152 + 1000 * atoi(getenv("YGG_MODEL_INDEX"));
                _last_port_set = 1;
                ygglog_debug("_last_port = %d", _last_port);
            }
            adr->address( protocol + "://" + host + ":" +std::to_string(_last_port + 1));
#ifdef _OPENMP
        }
#endif
        /* strcat(address, ":!"); // For random port */
    }
    // Bind
    if (handle != nullptr) {
        delete handle;
        handle = nullptr;
    }

    if (flags & COMM_FLAG_CLIENT_RESPONSE) {
        handle = create_zsock(ZMQ_ROUTER);
    } else if (flags & COMM_ALLOW_MULTIPLE_COMMS) {
        handle = create_zsock(ZMQ_DEALER);
    } else {
        handle = create_zsock(ZMQ_PAIR);
    }
    if (handle == nullptr) {
        ygglog_error("new_zmq_address: Could not initialize empty socket.");
        return -1;
    }
    int port = zsock_bind(handle, "%s", adr->address().c_str());
    if (port == -1) {
        ygglog_error("new_zmq_address: Could not bind socket to address = %s",
                     adr->address().c_str());
        return -1;
    }
    // Add port to address
#ifdef _OPENMP
#pragma omp critical (zmqport)
    {
#endif
        if (protocol != "inproc" && protocol != "ipc") {
            _last_port = port;
            adr->address(protocol + "://" +  host + ":" + std::to_string(port));
        }
#ifdef _OPENMP
    }
#endif
    if (address == nullptr)
        delete address;
    address = adr;
    ygglog_debug("new_zmq_address: Bound socket to %s", address->address().c_str());
    if (name.empty())
        name = "tempnewZMQ-" + std::to_string(port);

    // Init reply
    init_zmq_reply();
    return 0;
};



ZMQComm::~ZMQComm() {
    destroy();
}

void ZMQComm::destroy() {
    // Drain input
    if (direction == RECV && flags & COMM_FLAG_VALID
        && (!(const_flags[0] & COMM_EOF_RECV))) {
        if (_ygg_error_flag == 0) {
            size_t data_len = 100;
            std::string data;
            comm_head_t head;
            bool is_eof_flag = false;
            while (comm_nmsg() > 0) {
                if (int ret = recv(data) >= 0) {
                    head = comm_head_t(data.c_str(), ret);
                    if (strncmp(YGG_MSG_EOF, data.c_str() + head.bodybeg, strlen(YGG_MSG_EOF)) == 0)
                        is_eof_flag = true;

                    if ((head.flags & HEAD_FLAG_VALID) && is_eof_flag) {
                        const_flags[0] |= COMM_EOF_RECV;
                        break;
                    }
                }
            }
        }
    }
    // Free reply
    if (reply != nullptr) {
        delete reply;
        reply = nullptr;
    }
    if (handle != nullptr) {
        delete handle;
        ygglog_debug("Destroying socket: %s", address->address().c_str());
        handle = nullptr;
    }
    ygglog_debug("free_zmq_comm: finished");

    //TODO: THERE IS MORE TO DELETE?
}

/*!
  @brief Get number of messages in the comm.
  @returns int Number of messages. -1 indicates an error.
 */
int ZMQComm::comm_nmsg() {
    int out = 0;
    if (direction == RECV) {
        if (handle != nullptr) {
            zpoller_t *poller = zpoller_new(handle, nullptr);
            if (poller == nullptr) {
                ygglog_error("zmq_comm_nmsg: Could not create poller");
                return -1;
            }
            void *p = zpoller_wait(poller, 1);
            if (p == nullptr) {
                if (zpoller_terminated(poller)) {
                    ygglog_error("zmq_comm_nmsg: Poller interrupted");
                    out = -1;
                } else {
                    out = 0;
                }
            } else {
                out = 1;
            }
            zpoller_destroy(&poller);
        }
    } else {
        /* if (x->last_send[0] != 0) { */
        /*   time_t now; */
        /*   time(&now); */
        /*   double elapsed = difftime(now, x->last_send[0]); */
        /*   if (elapsed > _wait_send_t) */
        /* 	out = 0; */
        /*   else */
        /* 	out = 1; */
        /* } */
        if (reply != nullptr) {
            ygglog_debug("zmq_comm_nmsg(%s): nmsg = %d, nrep = %d",
                         name.c_str(), reply->n_msg, reply->n_rep);
            out = reply->n_msg - reply->n_rep;
        }
    }
    return out;
}

/*!
  @brief Send a message to the comm.
  Send a message smaller than YGG_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
int ZMQComm::send(const std::string &data) {
    ygglog_debug("zmq_comm_send(%s): %d bytes", name.c_str(), data.size());
    if (check(data) == -1)
        return -1;
    if (handle == nullptr) {
        ygglog_error("zmq_comm_send(%s): socket handle is nullptr", name.c_str());
        return -1;
    }
    int new_len = 0;
    std::string new_data = check_reply_send(data);
    if (new_data.empty()) {
        ygglog_error("zmq_comm_send(%s): Adding reply address failed.", name.c_str());
        return -1;
    }
    zframe_t *f = zframe_new(new_data.c_str(), new_data.size());
    int ret = -1;
    if (f == nullptr) {
        ygglog_error("zmq_comm_send(%s): frame handle is nullptr", name.c_str());
    } else {
        ret = zframe_send(&f, handle, 0);
        if (ret < 0) {
            ygglog_error("zmq_comm_send(%s): Error in zframe_send", name.c_str());
            zframe_destroy(&f);
        }
    }
    // Get reply
    if (ret >= 0) {
        ret = do_reply_send();
        if (ret < 0) {
            if (ret == -2) {
                ygglog_error("zmq_comm_send(%s): EOF received", name.c_str());
            } else {
                ygglog_error("zmq_comm_send(%s): Error in do_reply_send", name.c_str());
            }
        }
    }
    ygglog_debug("zmq_comm_send(%s): returning %d", name.c_str(), ret);
    return ret;
};

zframe_t* ZMQComm::recv_zframe() {
    ygglog_debug("zmq_comm_recv_zframe(%s)", name.c_str());
    if (handle == nullptr) {
        ygglog_error("zmq_comm_recv_zframe(%s): socket handle is nullptr", name.c_str());
        return nullptr;
    }
    clock_t start = clock();
    while ((((double)(clock() - start))/CLOCKS_PER_SEC) < 180) {
        int nmsg = comm_nmsg();
        if (nmsg < 0)
            return nullptr;
        else if (nmsg > 0)
            break;
        else {
            ygglog_debug("zmq_comm_recv_zframe(%s): no messages, sleep %d", name.c_str(),
                         YGG_SLEEP_TIME);
            usleep(YGG_SLEEP_TIME);
        }
    }
    ygglog_debug("zmq_comm_recv_zframe(%s): receiving", name.c_str());
    zframe_t *out = nullptr;
    if (flags & COMM_FLAG_CLIENT_RESPONSE) {
        out = zframe_recv(handle);
        if (out == nullptr) {
            ygglog_debug("zmq_comm_recv_zframe(%s): did not receive identity", name.c_str());
            return nullptr;
        }
        zframe_destroy(&out);
        out = nullptr;
    }
    out = zframe_recv(handle);
    if (out == nullptr) {
        ygglog_debug("zmq_comm_recv_zframe(%s): did not receive", name.c_str());
        return nullptr;
    }
    return out;
}

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than YGG_MSG_MAX bytes from an input comm.
  @param[in] x comm_t* structure that message should be sent to.
  @param[out] data char ** pointer to allocated buffer where the message
  should be saved. This should be a malloc'd buffer if allow_realloc is 1.
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @param[in] allow_realloc const int If 1, the buffer will be realloced if it
  is not large enought. Otherwise an error will be returned.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
int ZMQComm::recv(std::string &data) {
    int ret = -1;
    ygglog_debug("zmq_comm_recv(%s)", name.c_str());
    if (handle == nullptr) {
        ygglog_error("zmq_comm_recv(%s): socket handle is nullptr", name.c_str());
        return ret;
    }
    zframe_t *out = recv_zframe();
    if (out == nullptr) {
        ygglog_debug("zmq_comm_recv(%s): did not receive", name.c_str());
        return ret;
    }
    // Check for server signon and respond
    while (strncmp((char*)zframe_data(out), "ZMQ_SERVER_SIGNING_ON::", 23) == 0) {
        ygglog_debug("zmq_comm_recv(%s): Received sign-on", name.c_str());
        char* client_address = (char*)zframe_data(out) + 23;
        // create a DEALER socket and connect to address
        zsock_t *client_socket = create_zsock(ZMQ_DEALER);
        if (client_socket == nullptr) {
            ygglog_error("zmq_comm_recv(%s): Could not initalize the client side of the proxy socket to confirm signon", name.c_str());
            zframe_destroy(&out);
            return ret;
        }
        zsock_set_sndtimeo(client_socket, _zmq_sleeptime);
        zsock_set_immediate(client_socket, 1);
        zsock_set_linger(client_socket, _zmq_sleeptime);
        if (zsock_connect(client_socket, "%s", client_address) < 0) {
            ygglog_error("zmq_comm_recv(%s): Error when connecting to the client proxy socket to respond to signon: %s", name.c_str(), client_address);
            zframe_destroy(&out);
            ygg_zsock_destroy(&client_socket);
            return ret;
        }
        zframe_t *response = zframe_new(zframe_data(out), zframe_size(out));
        if (response == nullptr) {
            ygglog_error("zmq_comm_recv(%s): Error creating response message frame.", name.c_str());
            zframe_destroy(&out);
            zframe_destroy(&response);
            ygg_zsock_destroy(&client_socket);
            return ret;
        }
        if (zframe_send(&response, client_socket, 0) < 0) {
            ygglog_error("zmq_comm_recv(%s): Error sending response message.", name.c_str());
            zframe_destroy(&out);
            zframe_destroy(&response);
            ygg_zsock_destroy(&client_socket);
            return ret;
        }
        zframe_destroy(&response);
        ygg_zsock_destroy(&client_socket);
        zframe_destroy(&out);
        out = recv_zframe();
        if (out == nullptr) {
            ygglog_debug("zmq_comm_recv(%s): did not receive", name.c_str());
            return ret;
        }
    }
    // Realloc and copy data
    size_t len_recv = zframe_size(out) + 1;
    // size_t len_recv = (size_t)ret + 1;
    char** temp;
    memcpy(*temp, zframe_data(out), len_recv - 1);
    data = *temp;
    zframe_destroy(&out);

    ret = (int)len_recv - 1;
    /*
    if (strlen(*data) != ret) {
      ygglog_error("zmq_comm_recv(%s): Size of string (%d) doesn't match expected (%d)",
           name.c_str(), strlen(*data), ret);
      return -1;
    }
    */
    // Check reply
    ret = check_reply_recv(data, ret);
    if (ret < 0) {
        ygglog_error("zmq_comm_recv(%s): failed to check for reply socket.", name.c_str());
        return ret;
    }
    ygglog_debug("zmq_comm_recv(%s): returning %d", name.c_str(), ret);
    return ret;
};


// Definitions in the case where ZMQ libraries not installed
#else /*ZMQINSTALLED*/

/*!
  @brief Print error message about ZMQ library not being installed.
 */
static inline
void ygg_zsys_shutdown() {
  ygglog_error("Compiler flag 'ZMQINSTALLED' not defined so ZMQ bindings are disabled.");
};

/*!
  @brief Print error message about ZMQ library not being installed.
 */
static inline
void* ygg_zsys_init() {
  ygglog_error("Compiler flag 'ZMQINSTALLED' not defined so ZMQ bindings are disabled.");
  return nullptr;
};

/*!
  @brief Print error message about ZMQ library not being installed.
 */
static inline
void zmq_install_error() {
  ygglog_error("Compiler flag 'ZMQINSTALLED' not defined so ZMQ bindings are disabled.");
};

/*!
  @brief Perform deallocation for ZMQ communicator.
  @param[in] x comm_t Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_zmq_comm(comm_t *x) {
  zmq_install_error();
  return 1;
};

/*!
  @brief Create a new socket.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_zmq_address(comm_t *comm) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Initialize a ZeroMQ communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_zmq_comm(comm_t *comm) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t* Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int zmq_comm_nmsg(const comm_t* x) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Send a message to the comm.
  Send a message smaller than YGG_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t* structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int zmq_comm_send(const comm_t* x, const char *data, const size_t len) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than YGG_MSG_MAX bytes from an input comm.
  @param[in] x comm_t* structure that message should be sent to.
  @param[out] data char ** pointer to allocated buffer where the message
  should be saved. This should be a malloc'd buffer if allow_realloc is 1.
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @param[in] allow_realloc const int If 1, the buffer will be realloced if it
  is not large enought. Otherwise an error will be returned.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int zmq_comm_recv(const comm_t* x, char **data, const size_t len,
		  const int allow_realloc) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Add reply socket information to a send comm.
  @param[in] comm comm_t* Comm that confirmation is for.
  @returns char* Reply socket address.
*/
static inline
char *set_reply_send(const comm_t *comm) {
  zmq_install_error();
  return nullptr;
};

/*!
  @brief Add reply socket information to a recv comm.
  @param[in] comm comm_t* Comm that confirmation is for.
  @param[in] address const char* Comm address.
  @returns int Index of the reply socket.
*/
static inline
int set_reply_recv(const comm_t *comm, const char* address) {
  zmq_install_error();
  return -1;
};

#endif /*ZMQINSTALLED*/