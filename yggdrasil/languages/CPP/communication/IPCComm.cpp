#include "IPCComm.hpp"

unsigned IPCComm::_yggChannelsUsed = 0;
bool IPCComm::_ipc_rand_seeded = false;

#ifdef IPCINSTALLED

IPCComm::~IPCComm() {
    if (handle != nullptr) {
        if (direction == RECV) {
            remove_comm(true);
        } else {
            remove_comm(false);
        }
        delete handle;
        handle = nullptr;
    }
}

/*!
  @brief Check if an IPC channel can be initialized.
  @returns int -1 if the channel can't be initialized.
 */
int IPCComm::check_channels() {
    // Fail if name is empty
    if (name.empty()) {
        ygglog_error("Cannot create channel with empty name.");
        return -1;
    }
    // Fail if trying to re-use the same channel twice
    unsigned i;
    int error_code = 0;
#ifdef _OPENMP
    #pragma omp critical (ipc)
  {
#endif
    for (i = 0; i < _yggChannelsUsed; i++ ) {
        if (IPCComm::_yggChannelNames[i] == address->key()) {
            ygglog_error("Attempt to re-use channel: name=%s, key=%s, i=%d",
                         name.c_str(), address->address().c_str(), i);
            error_code = -1;
            break;
        }
    }
    // Fail if > _yggTrackChannels channels used
    if ((!error_code) && (IPCComm::_yggChannelsUsed >= _yggTrackChannels)) {
        ygglog_error("Too many channels in use, max: %d", _yggTrackChannels);
        error_code = -1;
    }
#ifdef _OPENMP
    }
#endif
  return error_code;
}

/*!
  @brief Add a new channel to the list of existing channels.
*/

void IPCComm::add_channel() {
#ifdef _OPENMP
#pragma omp critical (ipc)
  {
#endif
  // printf("add_channel(%s): %d, %s\n", comm->name, _yggChannelsUsed, comm->address);
    IPCComm::_yggChannelNames[IPCComm::_yggChannelsUsed++] = address->key();
#ifdef _OPENMP
  }
#endif
}

/*!
  @brief Remove a channel.
  @param[in] close_comm int If 1, the queue will be closed, otherwise it will
  just be removed from the register and it is assumed that another process
  will close it.
  @returns int -1 if removal not successful.
*/

int IPCComm::remove_comm(bool close_comm) {
    int ret;
    if (close_comm) {
        msgctl(handle[0], IPC_RMID, nullptr);
    }
    ret = -1;
    unsigned i;
    int ich = address->key();
#ifdef _OPENMP
    #pragma omp critical (ipc)
  {
#endif
    for (i = 0; i < IPCComm::_yggChannelsUsed; i++) {
        if (ich == IPCComm::_yggChannelNames[i]) {
            memmove(IPCComm::_yggChannelNames + i, IPCComm::_yggChannelNames + i + 1,
                    (_yggTrackChannels - (i + 1))*sizeof(int));
            IPCComm::_yggChannelsUsed--;
            ret = 0;
            break;
        }
    }
    if (ret < 0) {
        ygglog_error("remove_comm(%s): Could not locate comm in register.", name.c_str());
    }
#ifdef _OPENMP
    }
#endif
    return ret;
}

/*!
  @brief Create a new channel.
  @returns int -1 if the address could not be created.
*/
int IPCComm::new_address() {
    int ret;
    // TODO: small chance of reusing same number
    int key = 0;
#ifdef _OPENMP
    #pragma omp critical (ipc)
  {
#endif
    if (!_ipc_rand_seeded) {
        srand(ptr2seed(this));
        _ipc_rand_seeded = true;
    }
#ifdef _OPENMP
    }
#endif
    while (key == 0) {
        key = std::rand();
    }
    if (name.empty()) {
        name = "tempnewIPC." + std::to_string(key);
    } else {
        ret = check_channels();
        if (ret < 0)
            return ret;
    }
    address->address(std::to_string(key));
    int *fid = new int;
    fid[0] = msgget(key, (IPC_CREAT | 0777));
    if (fid[0] < 0) {
        ygglog_error("new_ipc_address: msgget(%d, %d | 0777) ret(%d), errno(%d): %s",
                     key, IPC_CREAT, fid[0], errno, strerror(errno));
        return -1;
    }
    handle = fid;
    add_channel();
    return 0;
}

/*!
  @brief Get number of messages in the comm.
  @returns int Number of messages. -1 indicates an error.
 */
int IPCComm::comm_nmsg() {
    struct msqid_ds buf;
    if (handle == nullptr) {
        ygglog_error("ipc_comm_nmsg: Queue handle is NULL.");
        return -1;
    }

    int rc = msgctl(handle[0], IPC_STAT, &buf);
    if (rc != 0) {
        /* ygglog_error("ipc_comm_nmsg: Could not access queue."); */
        return 0;
    }
    int ret = static_cast<int>(buf.msg_qnum);
    return ret;
}

/*!
  @brief Send a message to the comm.
  Send a message smaller than YGG_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] data character pointer to message that should be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
int IPCComm::send(const std::string &data) {
    ygglog_debug("ipc_comm_send(%s): %d bytes", name.c_str(), data.size());
   if (check(data) == -1)
        return -1;
    msgbuf_t t;
    t.mtype = 1;
    memcpy(t.data, data.c_str(), data.size());
    int ret;
    while (true) {
        ret = msgsnd(handle[0], &t, data.size(), IPC_NOWAIT);
        ygglog_debug("ipc_comm_send(%s): msgsnd returned %d", name.c_str(), ret);
        if (ret == 0)
            break;
        if ((ret == -1) && (errno == EAGAIN)) {
            ygglog_debug("ipc_comm_send(%s): msgsnd, sleep", name.c_str());
            usleep(YGG_SLEEP_TIME);
        } else {
            struct msqid_ds buf;
            int rtrn = msgctl(handle[0], IPC_STAT, &buf);
            if ((rtrn == 0) && ((buf.msg_qnum + data.size()) > buf.msg_qbytes)) {
                ygglog_debug("ipc_comm_send(%s): msgsnd, queue full, sleep", name.c_str());
                usleep(YGG_SLEEP_TIME);
            } else {
                ygglog_error("ipc_comm_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s",
                             handle[0], &t, data.size(), ret, errno, strerror(errno));
                ret = -1;
                break;
            }
        }
    }
    ygglog_debug("ipc_comm_send(%s): returning %d", name.c_str(), ret);
    return ret;
}

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than YGG_MSG_MAX bytes from an input comm.
  @param[out] data char ** pointer to allocated buffer where the message
  should be saved.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
int IPCComm::recv(std::string &data) {
    ygglog_debug("ipc_comm_recv(%s)", name.c_str());
    msgbuf_t t;
    t.mtype = 1;
    long ret;
    while (true) {
        ret = msgrcv(handle[0], &t, YGG_MSG_MAX, 0, IPC_NOWAIT);
        if (ret == -1 && errno == ENOMSG) {
            ygglog_debug("ipc_comm_recv(%s): no input, sleep", name.c_str());
            usleep(YGG_SLEEP_TIME);
        } else {
            ygglog_debug("ipc_comm_recv(%s): received input: %d bytes, ret=%d",
                         name.c_str(), strlen(t.data), ret);
            break;
        }
    }
    if (ret <= 0) {
        ygglog_debug("ipc_comm_recv: msgrecv(%d, %p, %d, 0, IPC_NOWAIT): %s",
                     handle, &t, (int)YGG_MSG_MAX, strerror(errno));
        return -1;
    }

    data.assign(t.data);
    ygglog_debug("ipc_comm_recv(%s): returns %d bytes", name.c_str(), ret);
    return static_cast<int>(ret);
}

/*!
  @brief Send a large message to an output comm.
  Send a message larger than YGG_MSG_MAX bytes to an output comm by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  ipc_comm_recv_nolimit for communication to make sense.
  @param[in] data character pointer to message that should be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
int IPCComm::send_nolimit(const std::string &data) {
    ygglog_debug("ipc_comm_send_nolimit(%s): %d bytes", name.c_str(), data.size());
    int ret = -1;
    size_t msgsiz;
    size_t len = data.size();
    size_t pos = 0;
    while (pos < len) {
        if ((ret = send(data.substr(pos, YGG_MSG_MAX))) != 0) {
            ygglog_debug("ipc_comm_send_nolimit(%s): send interupted at %d of %d bytes.",
                         name.c_str(), pos, len);
            break;
        }
        if ((len - pos) > YGG_MSG_MAX)
            msgsiz = YGG_MSG_MAX;
        else
            msgsiz = len - pos;
        pos += msgsiz;
        ygglog_debug("ipc_comm_send_nolimit(%s): %d of %d bytes sent",
                     name.c_str(), pos, len);
    }

    if (ret == 0)
        ygglog_debug("ipc_comm_send_nolimit(%s): %d bytes completed", name.c_str(), len);
    return ret;
}

IPCComm::IPCComm(const std::string &name, Address *address, const Direction direction,
                 DataType *datatype) : CommBase(address, direction, IPC_COMM, datatype) {
    if (name.empty()) {
        this->name = "tempinitIPC." + this->address->address();
    } else {
        this->name = name;
        if (check_channels() < 0)
            throw std::runtime_error("Check channels failed");
    }
    add_channel();
    int qkey = this->address->key();
    int *fid = new int;
    fid[0] = msgget(qkey, 0600);
    handle = fid;
}

#else /*IPCINSTALLED*/

/*!
  @brief Print error message about IPC library not being installed.
 */
static inline
void ipc_install_error() {
  ygglog_error("Compiler flag 'IPCINSTALLED' not defined so IPC bindings are disabled.");
};

IPCComm::IPCComm() {
ipc_install_error();
}
IPCComm::~IPCComm() {
ipc_install_error();
}
int IPCComm::check_channels() {
ipc_install_error();
return -1;
}
void IPCComm::add_channel() {
ipc_install_error();
}
int IPCComm::remove_comm(bool close_comm) {
      // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(close_comm);
#endif
  ipc_install_error();
  return -1;
}
int IPCComm::new_ipc_address() {
ipc_install_error();
return -1;
}
int IPCComm::ipc_comm_nmsg() {
ipc_install_error();
return -1;
}
int IPCComm::send(const std::string &data) {
      // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(data);
#endif
  ipc_install_error();
  return -1;
}
int IPCComm::recv(std::string &data) {
      // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(data);
#endif
  ipc_install_error();
  return -1;
}
int IPCComm::send_nolimit(const std::string &data) {
      // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(data);
#endif
  ipc_install_error();
  return -1;
}

#endif /*IPCINSTALLED*/
