#include <fcntl.h>           /* For O_* constants */
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/types.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <CommBase.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISIPCCOMM_H_
#define CISIPCCOMM_H_

/*! Number of temporary channels created. */
static unsigned _cisChannelsCreated = 0;
/*! @brief Maximum number of channels. */
#define _cisTrackChannels 256
/*! @brief Names of channels in use. */
static char * _cisChannelNames[_cisTrackChannels];
/*! @brief Number of channels in use. */
static unsigned _cisChannelsUsed = 0;

/*!
  @brief Message buffer structure.
*/
typedef struct msgbuf_t {
  long mtype; //!< Message buffer type
  char data[CIS_MSG_MAX]; //!< Buffer for the message
} msgbuf_t;

/*!
  @brief Check if an IPC channel can be initialized.
  @param[in] comm comm_t Comm structure with name that should be checked.
  @returns int -1 if the channel can't be initialized.
 */
static inline
int check_channels(comm_t comm) {
  // Fail if name is empty
  if (strlen(comm.name) == 0) {
    cislog_error("Cannot create channel with empty name.");
    return -1;
  }
  // Fail if trying to re-use the same channel twice
  unsigned i;
  for (i = 0; i < _cisChannelsUsed; i++ ){
    if (0 == strcmp(_cisChannelNames[i], comm.name)){
      cislog_error("Attempt to re-use channel: name=%s", comm.name);
      return -1;
    }
  }
  // Fail if > _cisTrackChannels channels used
  if (_cisChannelsUsed >= _cisTrackChannels) {
    cislog_error("Too many channels in use, max: %d\n", _cisTrackChannels);
    return -1;
  }
  return 0;
};

/*!
  @brief Add a new channel to the list of existing channels.
  @param[in] name const char * Name of channel to record.
*/
static inline
void add_channel(char *name) {
  _cisChannelNames[_cisChannelsUsed++] = name;
};

/*!
  @brief Remove a channel.
  @param[in] comm comm_t Comm with channel that should be removed.
  @returns int -1 if removal not successful.
*/
static inline
int remove_comm(const comm_t comm) {
  int ich = atoi(comm.address);
  int ret = msgctl(((int*)comm.handle)[0], IPC_RMID, NULL);
  if ((ret != -1) && (ich == (int)(_cisChannelsUsed - 1))) {
    /* memmove(_cisChannelNames + ich, _cisChannelNames + ich + 1, */
    /* 	    (_cisTrackChannels - (ich + 1))*sizeof(char*)); */
    _cisChannelsUsed--;
  }
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
  int key = _cisChannelsCreated + 1;
  if (strlen(comm->name) == 0)
    sprintf(comm->name, "tempIPC.%d", key);
  ret = check_channels(*comm);
  if (ret < 0)
    return ret;
  sprintf(comm->address, "%d", key);
  int *fid = (int*)malloc(sizeof(int));
  fid[0] = msgget(key, (IPC_CREAT | 0777));
  if (fid[0] < 0) {
      cislog_error("new_ipc_address: msgget(%d, %d) ret(%d), errno(%d): %s",
		   IPC_PRIVATE, IPC_CREAT, fid[0], errno, strerror(errno));
      return -1;
  }
  comm->handle = (void*)fid;
  add_channel(comm->name);
  _cisChannelsCreated++;
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
  if (strlen(comm->name) == 0)
    sprintf(comm->name, "tempIPC.%s", comm->address);
  int ret = check_channels(*comm);
  if (ret < 0)
    return ret;
  add_channel(comm->address);
  int qkey = atoi(comm->address);
  int *fid = (int *)malloc(sizeof(int));
  fid[0] = msgget(qkey, 0600);
  comm->handle = (void*)fid;
  return 0;
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_ipc_comm(comm_t *x) {
  if (x->handle != NULL) {
    if (strcmp(x->direction, "recv") == 0) {
      remove_comm(*x);
    }
    free(x->handle);
    x->handle = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int ipc_comm_nmsg(const comm_t x) {
  struct msqid_ds buf;
  int rc = msgctl(((int*)x.handle)[0], IPC_STAT, &buf);
  if (rc != 0) {
    cislog_error("ipc_comm_nmsg: Could not access queue.");
    return -1;
  }
  int ret = buf.msg_qnum;
  return ret;
};

/*!
  @brief Send a message to the comm.
  Send a message smaller than CIS_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int ipc_comm_send(const comm_t x, const char *data, const int len) {
  cislog_debug("ipc_comm_send(%s): %d bytes", x.name, len);
  if (comm_base_send(x, data, len) == -1)
    return -1;
  msgbuf_t t;
  t.mtype = 1;
  memcpy(t.data, data, len);
  int ret = -1;
  int handle = ((int*)(x.handle))[0];
  while (1) {
    ret = msgsnd(handle, &t, len, IPC_NOWAIT);
    cislog_debug("ipc_comm_send(%s): msgsnd returned %d", x.name, ret);
    if (ret == 0) break;
    if (ret == EAGAIN) {
      cislog_debug("ipc_comm_send(%s): msgsnd, sleep", x.name);
      usleep(250*1000);
    } else {
      cislog_error("ipc_comm_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s",
		   (int*)x.handle, &t, len, ret, errno, strerror(errno));
      ret = -1;
      break;
    }
  }
  cislog_debug("ipc_comm_send(%s): returning %d", x.name, ret);
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than CIS_MSG_MAX bytes from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int ipc_comm_recv(const comm_t x, char *data, const int len) {
  cislog_debug("ipc_comm_recv(%s)", x.name);
  msgbuf_t t;
  t.mtype = 1;
  int ret = -1;
  while (1) {
    ret = msgrcv(((int*)x.handle)[0], &t, len, 0, IPC_NOWAIT);
    if (ret == -1 && errno == ENOMSG) {
      cislog_debug("ipc_comm_recv(%s): no input, sleep", x.name);
      usleep(250*1000);
    } else {
      cislog_debug("ipc_comm_recv(%s): received input: %d bytes, ret=%d",
		   x.name, strlen(t.data), ret);
      break;
    }
  }
  if (ret > 0){
    memcpy(data, t.data, ret);
    data[ret] = '\0';
  } else {
    cislog_debug("ipc_comm_recv: msgrecv(%d, %p, %d, 0, IPC_NOWAIT: %s",
		 (int*)x.handle, &t, len, strerror(errno));
    ret = -1;
  }
  cislog_debug("ipc_comm_recv(%s): returns %d bytes\n", x.name, ret);
  return ret;
};

/*!
  @brief Send a large message to an output comm.
  Send a message larger than CIS_MSG_MAX bytes to an output comm by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  ipc_comm_recv_nolimit for communication to make sense.
  @param[in] x comm_t structure that message should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int ipc_comm_send_nolimit(const comm_t x, const char *data, const int len){
  cislog_debug("ipc_comm_send_nolimit(%s): %d bytes", x.name, len);
  int ret = -1;
  int msgsiz = 0;
  char msg[CIS_MSG_MAX];
  sprintf(msg, "%ld", (long)(len));
  ret = ipc_comm_send(x, msg, strlen(msg));
  if (ret != 0) {
    cislog_debug("ipc_comm_send_nolimit(%s): sending size of payload failed.", x.name);
    return ret;
  }
  int prev = 0;
  while (prev < len) {
    if ((len - prev) > CIS_MSG_MAX)
      msgsiz = CIS_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = ipc_comm_send(x, data + prev, msgsiz);
    if (ret != 0) {
      cislog_debug("ipc_comm_send_nolimit(%s): send interupted at %d of %d bytes.",
		   x.name, prev, len);
      break;
    }
    prev += msgsiz;
    cislog_debug("ipc_comm_send_nolimit(%s): %d of %d bytes sent",
		 x.name, prev, len);
  }
  if (ret == 0)
    cislog_debug("ipc_comm_send_nolimit(%s): %d bytes completed", x.name, len);
  return ret;
};

/*!
  @brief Receive a large message from an input comm.
  Receive a message larger than CIS_MSG_MAX bytes from an input comm by
  receiving it in parts. This expects the first message to be the size of
  the total message.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to pointer for allocated buffer where the
  message should be stored. A pointer to a pointer is used so that the buffer
  may be reallocated as necessary for the incoming message.
  @param[in] len0 int length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int ipc_comm_recv_nolimit(const comm_t x, char **data, const int len0){
  cislog_debug("ipc_comm_recv_nolimit(%s)", x.name);
  long len = 0;
  int ret = -1;
  int msgsiz = 0;
  char msg[CIS_MSG_MAX];
  int prev = 0;
  ret = ipc_comm_recv(x, msg, CIS_MSG_MAX);
  if (ret < 0) {
    cislog_debug("ipc_comm_recv_nolimit(%s): failed to receive payload size.", x.name);
    return -1;
  }
  ret = sscanf(msg, "%ld", &len);
  if (ret != 1) {
    cislog_debug("ipc_comm_recv_nolimit(%s): failed to parse payload size (%s)",
		 x.name, msg);
    return -1;
  }
  // Reallocate data if necessary
  if (len > len0) {
    *data = (char*)realloc(*data, len);
  }
  ret = -1;
  while (prev < len) {
    if ((len - prev) > CIS_MSG_MAX)
      msgsiz = CIS_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = ipc_comm_recv(x, (*data) + prev, msgsiz);
    if (ret < 0) {
      cislog_debug("ipc_comm_recv_nolimit(%s): recv interupted at %d of %d bytes.",
		   x.name, prev, len);
      break;
    }
    prev += ret;
    cislog_debug("ipc_comm_recv_nolimit(%s): %d of %d bytes received",
		 x.name, prev, len);
  }
  if (ret > 0) {
    cislog_debug("ipc_comm_recv_nolimit(%s): %d bytes completed", x.name, prev);
    return prev;
  } else {
    return -1;
  }
};


#endif /*CISIPCCOMM_H_*/
