#include "IPCComm.hpp"

unsigned IPCComm::_yggChannelsUsed = 0;
unsigned IPCComm::_ipc_rand_seeded = 0;

#ifdef IPCINSTALLED

IPCComm::~IPCComm() {

}
int IPCComm::check_channels() {

}
void IPCComm::add_channel() {

}
int IPCComm::remove_comm(const int close_comm) {

}
int IPCComm::new_ipc_address() {

}
int IPCComm::ipc_comm_nmsg() {

}
int IPCComm::send(const std::string &data) {

}
int IPCComm::recv(std::string &data) {

}
int IPCComm::send_nolimit(const std::string &data) {

}

IPCComm::IPCComm(const std::string &name, const std::string &address, const std::string &direction,
                 DataType *datatype) : CommBase(name, address, direction, IPC_COMM, datatype) {
    if (name.empty()) {
        this->name = "tempinitIPC." + this->address;
    } else {
        int ret = check_channels();
        if (ret < 0)
            EXCEPTION;
    }
    add_channel();
    int qkey = stoi(address);

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
int IPCComm::remove_comm(const int close_comm) {
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
