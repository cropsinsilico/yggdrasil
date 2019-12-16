/*! @brief Flag for checking if this header has already been included. */
#ifndef YGGIPCCOMM_H_
#define YGGIPCCOMM_H_

#ifdef IPCINSTALLED
#include <fcntl.h>           /* For O_* constants */
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/types.h>
#include <sys/sem.h>
#include <sys/shm.h>
#endif /*IPCINSTALLED*/
#include <CommBase.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

#ifdef IPCINSTALLED

/*! Number of temporary channels created. */
static unsigned _yggChannelsCreated = 0;
/*! @brief Maximum number of channels. */
#define _yggTrackChannels 256
/*! @brief Names of channels in use. */
static int _yggChannelNames[_yggTrackChannels]; 
//static char * _yggChannelNames[_yggTrackChannels];
/*! @brief Number of channels in use. */
static unsigned _yggChannelsUsed = 0;
static unsigned _ipc_rand_seeded = 0;

/*!
  @brief Message buffer structure.
*/
typedef struct msgbuf_t {
  long mtype; //!< Message buffer type
  char data[YGG_MSG_MAX]; //!< Buffer for the message
} msgbuf_t;

/*!
  @brief Check if an IPC channel can be initialized.
  @param[in] comm comm_t* Comm structure with name that should be checked.
  @returns int -1 if the channel can't be initialized.
 */
static inline
int check_channels(comm_t* comm) {
  // Fail if name is empty
  if (strlen(comm->name) == 0) {
    ygglog_error("Cannot create channel with empty name.");
    return -1;
  }
  // Fail if trying to re-use the same channel twice
  unsigned i;
  char *key = comm->address;
  for (i = 0; i < _yggChannelsUsed; i++ ) {
    if (_yggChannelNames[i] == atoi(comm->address)) {
    /* if (0 == strcmp(_yggChannelNames[i], key)) { */
      ygglog_error("Attempt to re-use channel: name=%s, key=%s, i=%d",
		   comm->name, key, i);
      return -1;
    }
  }
  // Fail if > _yggTrackChannels channels used
  if (_yggChannelsUsed >= _yggTrackChannels) {
    ygglog_error("Too many channels in use, max: %d", _yggTrackChannels);
    return -1;
  }
  return 0;
};

/*!
  @brief Add a new channel to the list of existing channels.
  @param[in] name const char * Name of channel to record.
*/
static inline
void add_channel(const comm_t* comm) {
  // printf("add_channel(%s): %d, %s\n", comm->name, _yggChannelsUsed, comm->address);
  _yggChannelNames[_yggChannelsUsed++] = atoi(comm->address);
};

/*!
  @brief Remove a channel.
  @param[in] comm comm_t* Comm with channel that should be removed.
  @param[in] close_comm int If 1, the queue will be closed, otherwise it will
  just be removed from the register and it is assumed that another process
  will close it.
  @returns int -1 if removal not successful.
*/
static inline
int remove_comm(const comm_t* comm, const int close_comm) {
  int ret;
  if (close_comm) {
    ret = msgctl(((int*)(comm->handle))[0], IPC_RMID, NULL);
    /* if (ret < 0) { */
    /*   ygglog_error("remove_comm(%s): Could not close comm.", comm->name); */
    /*   return ret; */
    /* } */
  }
  ret = -1;
  unsigned i;
  int ich = atoi(comm->address);
  for (i = 0; i < _yggChannelsUsed; i++) {
    if (ich == _yggChannelNames[i]) {
      memmove(_yggChannelNames + i, _yggChannelNames + i + 1,
	      (_yggTrackChannels - (i + 1))*sizeof(int));
      _yggChannelsUsed--;
      ret = 0;
      break;
    }
  }
  if (ret < 0) {
    ygglog_error("remove_comm(%s): Could not locate comm in register.", comm->name);
  }
  /* if ((ret != -1) && (ich == (int)(_yggChannelsUsed - 1))) { */
  /*   /\* memmove(_yggChannelNames + ich, _yggChannelNames + ich + 1, *\/ */
  /*   /\* 	    (_yggTrackChannels - (ich + 1))*sizeof(char*)); *\/ */
  /*   _yggChannelsUsed--; */
  /* } */
  return ret;
};

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_ipc_address(comm_t *comm) {
  int ret;
  // TODO: small chance of reusing same number
  int key = 0;
  if (!(_ipc_rand_seeded)) {
    srand(ptr2seed(comm));
    _ipc_rand_seeded = 1;
  }
  while (key == 0) {
    key = rand();
  } // _yggChannelsUsed + 1;
  if (strlen(comm->name) == 0) {
    sprintf(comm->name, "tempnewIPC.%d", key);
  } else {
    ret = check_channels(comm);
    if (ret < 0)
      return ret;
  }
  sprintf(comm->address, "%d", key);
  int *fid = (int*)malloc(sizeof(int));
  if (fid == NULL) {
    ygglog_error("new_ipc_address: Could not malloc queue fid.");
    return -1;
  }
  fid[0] = msgget(key, (IPC_CREAT | 0777));
  if (fid[0] < 0) {
      ygglog_error("new_ipc_address: msgget(%d, %d | 0777) ret(%d), errno(%d): %s",
		   key, IPC_CREAT, fid[0], errno, strerror(errno));
      return -1;
  }
  comm->handle = (void*)fid;
  add_channel(comm);
  _yggChannelsCreated++;
  return 0;
};

/*!
  @brief Initialize a sysv_ipc communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_ipc_comm(comm_t *comm) {
  if (comm->valid == 0)
    return -1;
  if (strlen(comm->name) == 0) {
    sprintf(comm->name, "tempinitIPC.%s", comm->address);
  } else {
    int ret = check_channels(comm);
    if (ret < 0)
      return ret;
  }
  add_channel(comm);
  int qkey = atoi(comm->address);
  int *fid = (int *)malloc(sizeof(int));
  if (fid == NULL) {
    ygglog_error("init_ipc_comm: Could not malloc queue fid.");
    return -1;
  }
  fid[0] = msgget(qkey, 0600);
  if (fid[0] < 0) {
      ygglog_error("init_ipc_address: msgget(%d, 0600) ret(%d), errno(%d): %s",
       qkey, fid[0], errno, strerror(errno));
      return -1;
  }
  comm->handle = (void*)fid;
  return 0;
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is an error, 0 otherwise.
*/
static inline
int free_ipc_comm(comm_t *x) {
  if (x->handle != NULL) {
    if (strcmp(x->direction, "recv") == 0) {
      remove_comm(x, 1);
    } else {
      remove_comm(x, 0);
    }
    free(x->handle);
    x->handle = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t* Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int ipc_comm_nmsg(const comm_t *x) {
  struct msqid_ds buf;
  if (x->handle == NULL) {
    ygglog_error("ipc_comm_nmsg: Queue handle is NULL.");
    return -1;
  }
  int rc = msgctl(((int*)x->handle)[0], IPC_STAT, &buf);
  if (rc != 0) {
    /* ygglog_error("ipc_comm_nmsg: Could not access queue."); */
    return 0;
  }
  int ret = buf.msg_qnum;
  return ret;
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
int ipc_comm_send(const comm_t *x, const char *data, const size_t len) {
  ygglog_debug("ipc_comm_send(%s): %d bytes", x->name, len);
  if (comm_base_send(x, data, len) == -1)
    return -1;
  msgbuf_t t;
  t.mtype = 1;
  memcpy(t.data, data, len);
  int ret = -1;
  int handle = ((int*)(x->handle))[0];
  while (1) {
    ret = msgsnd(handle, &t, len, IPC_NOWAIT);
    ygglog_debug("ipc_comm_send(%s): msgsnd returned %d", x->name, ret);
    if (ret == 0) break;
    if ((ret == -1) && (errno == EAGAIN)) {
      ygglog_debug("ipc_comm_send(%s): msgsnd, sleep", x->name);
      usleep(YGG_SLEEP_TIME);
    } else {
      ygglog_error("ipc_comm_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s",
		   (int*)(x->handle), &t, len, ret, errno, strerror(errno));
      ret = -1;
      break;
    }
  }
  ygglog_debug("ipc_comm_send(%s): returning %d", x->name, ret);
  return ret;
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
int ipc_comm_recv(const comm_t *x, char **data, const size_t len,
		  const int allow_realloc) {
  ygglog_debug("ipc_comm_recv(%s)", x->name);
  msgbuf_t t;
  t.mtype = 1;
  int ret = -1;
  int len_recv = -1;
  while (1) {
    ret = msgrcv(((int*)(x->handle))[0], &t, YGG_MSG_MAX, 0, IPC_NOWAIT);
    if (ret == -1 && errno == ENOMSG) {
      ygglog_debug("ipc_comm_recv(%s): no input, sleep", x->name);
      usleep(YGG_SLEEP_TIME);
    } else {
      ygglog_debug("ipc_comm_recv(%s): received input: %d bytes, ret=%d",
		   x->name, strlen(t.data), ret);
      break;
    }
  }
  if (ret <= 0) {
    ygglog_debug("ipc_comm_recv: msgrecv(%d, %p, %d, 0, IPC_NOWAIT): %s",
		 (int*)(x->handle), &t, (int)YGG_MSG_MAX, strerror(errno));
    return -1;
  }
  len_recv = ret + 1;
  if (len_recv > (int)len) {
    if (allow_realloc) {
      ygglog_debug("ipc_comm_recv(%s): reallocating buffer from %d to %d bytes.",
		   x->name, (int)len, len_recv);
      (*data) = (char*)realloc(*data, len_recv);
      if (*data == NULL) {
	ygglog_error("ipc_comm_recv(%s): failed to realloc buffer.", x->name);
	return -1;
      }
    } else {
      ygglog_error("ipc_comm_recv(%s): buffer (%d bytes) is not large enough for message (%d bytes)",
		   x->name, len, len_recv);
      return -(len_recv - 1);
    }
  }
  memcpy(*data, t.data, len_recv);
  (*data)[len_recv - 1] = '\0';
  ret = len_recv - 1;
  ygglog_debug("ipc_comm_recv(%s): returns %d bytes", x->name, ret);
  return ret;
};

/*!
  @brief Send a large message to an output comm.
  Send a message larger than YGG_MSG_MAX bytes to an output comm by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  ipc_comm_recv_nolimit for communication to make sense.
  @param[in] x comm_t* structure that message should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int ipc_comm_send_nolimit(const comm_t *x, const char *data, const size_t len){
  ygglog_debug("ipc_comm_send_nolimit(%s): %d bytes", x->name, len);
  int ret = -1;
  size_t msgsiz = 0;
  char msg[YGG_MSG_MAX];
  sprintf(msg, "%ld", (long)(len));
  ret = ipc_comm_send(x, msg, strlen(msg));
  if (ret != 0) {
    ygglog_debug("ipc_comm_send_nolimit(%s): sending size of payload failed.", x->name);
    return ret;
  }
  size_t prev = 0;
  while (prev < len) {
    if ((len - prev) > YGG_MSG_MAX)
      msgsiz = YGG_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = ipc_comm_send(x, data + prev, msgsiz);
    if (ret != 0) {
      ygglog_debug("ipc_comm_send_nolimit(%s): send interupted at %d of %d bytes.",
		   x->name, (int)prev, (int)len);
      break;
    }
    prev += msgsiz;
    ygglog_debug("ipc_comm_send_nolimit(%s): %d of %d bytes sent",
		 x->name, prev, len);
  }
  if (ret == 0)
    ygglog_debug("ipc_comm_send_nolimit(%s): %d bytes completed", x->name, len);
  return ret;
};


// Definitions in the case where IPC libraries not installed
#else /*IPCINSTALLED*/

/*!
  @brief Print error message about IPC library not being installed.
 */
static inline
void ipc_install_error() {
  ygglog_error("Compiler flag 'IPCINSTALLED' not defined so IPC bindings are disabled.");
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is an error, 0 otherwise.
*/
static inline
int free_ipc_comm(comm_t *x) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  x;
#endif
  ipc_install_error();
  return 1;
};

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_ipc_address(comm_t *comm) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  comm;
#endif
  ipc_install_error();
  return -1;
};

/*!
  @brief Initialize a sysv_ipc communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_ipc_comm(comm_t *comm) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  comm;
#endif
  ipc_install_error();
  return -1;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int ipc_comm_nmsg(const comm_t *x) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  x;
#endif
  ipc_install_error();
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
int ipc_comm_send(const comm_t *x, const char *data, const size_t len) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  x;
  data;
  len;
#endif
  ipc_install_error();
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
int ipc_comm_recv(const comm_t *x, char **data, const size_t len,
		  const int allow_realloc) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  x;
  data;
  len;
  allow_realloc;
#endif
  ipc_install_error();
  return -1;
};

#endif /*IPCINSTALLED*/

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGIPCCOMM_H_*/
