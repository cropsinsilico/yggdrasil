#ifndef YGGINTERFACEP_IPCCOMM_HPP
#define YGGINTERFACEP_IPCCOMM_HPP

#define IPCINSTALLED

#ifdef USE_OSR_YGG
#undef IPCINSTALLED
#endif

#ifdef IPCINSTALLED
#include <fcntl.h>           /* For O_* constants */
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/types.h>
#include <sys/sem.h>
#include <sys/shm.h>
#endif /*IPCINSTALLED*/
#include "CommBase.hpp"

/*! @brief Maximum number of channels. */
#define _yggTrackChannels 256
/*!
  @brief Message buffer structure.
*/
typedef struct msgbuf_t {
    long mtype; //!< Message buffer type
    char data[YGG_MSG_MAX]; //!< Buffer for the message
} msgbuf_t;


class IPCComm : public CommBase {
public:
    IPCComm(const std::string &name = "", const std::string &address = "", const std::string & direction = "",
            DataType* datatype = nullptr);
    ~IPCComm();
    int check_channels();
    void add_channel();
    int remove_comm(const int close_comm);
    int new_ipc_address();
    int ipc_comm_nmsg();
    int send(const std::string &data) override;
    int recv(std::string &data) override;
    int send_nolimit(const std::string &data) override;
private:
    /*! @brief Names of channels in use. */
    static int _yggChannelNames[_yggTrackChannels];
    /*! @brief Number of channels in use. */
    static unsigned _yggChannelsUsed;
    static unsigned _ipc_rand_seeded;
};

#endif //YGGINTERFACEP_IPCCOMM_HPP
