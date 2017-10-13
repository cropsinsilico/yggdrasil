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
  char data[PSI_MSG_MAX]; //!< Buffer for the message
} msgbuf_t;

/*!
  @brief Initialize a sysv_ipc communicator.
  The name is used to locate the IPC queue handle stored in the associated
  environment variable.
  @param[in] name Name of environment variable that the queue address is
  stored in.
  @param[in] seri_info Format for formatting/parsing messages.
  @returns comm_t Comm structure.
 */
static inline
comm_t init_ipc_comm(const char *name, const char *direction, const void *seri_info) {
  comm_t ret = init_comm_base(name, direction, seri_info);
  ret.type = IPC_COMM;
  if (ret.valid == 0)
    return ret;
  // Fail if trying to re-use the same channel twice
  unsigned i;
  for (i = 0; i < _psiChannelsUsed; i++ ){
    if (0 == strcmp(_psiChannelNames[i], name)){
      psilog_error("Attempt to re-use channel %s", name);
      ret.valid = 0;
      return ret;
    }
  }
  // Fail if > _psiTrackChannels channels used
  if (_psiChannelsUsed >= _psiTrackChannels) {
    psilog_error("Too many channels in use, max: %d\n", _psiTrackChannels);
    ret.valid = 0;
    return ret;
  }
  _psiChannelNames[_psiChannelsUsed++] = ret.address;
  int qkey = atoi(qid);
  int *fid = (int *)malloc(sizeof(int));
  fid[0] = msgget(qkey, 0600);
  ret.handle = (void*)fid;
  return ret;
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] comm_t Communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_ipc_comm(comm_t x) {
  if (free_comm_base(x))
    return 1;
  if (x.handle != NULL) {
    free(x.handle);
    x.handle = NULL;
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
  Send a message smaller than PSI_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int ipc_comm_send(const comm_t x, const char *data, const int len) {
  debug("ipc_comm_send(%s): %d bytes", x.name, len);
  if (comm_base_send(x, data, len) == -1)
    return -1;
  msgbuf_t t;
  t.mtype = 1;
  memcpy(t.data, data, len);
  int ret = -1;
  while (1) {
    ret = msgsnd(((int*)x.handle)[0], &t, len, IPC_NOWAIT);
    debug("ipc_comm_send(%s): msgsnd returned %d", x.name, ret);
    if (ret == 0) break;
    if (ret == EAGAIN) {
      debug("ipc_comm_send(%s): msgsnd, sleep", x.name);
      usleep(250*1000);
    } else {
      cislog_error("ipc_comm_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s",
		   (int*)x.handle, &t, len, ret, errno, strerror(errno));
      ret = -1;
      break;
    }
  }
  debug("ipc_comm_send(%s): returning %d", x.name, ret);
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than PSI_MSG_MAX bytes from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int ipc_comm_recv(const comm_t x, char *data, const int len) {
  debug("ipc_comm_recv(%s)", x.name);
  msgbuf_t t;
  t.mtype = 1;
  int ret = -1;
  while (1) {
    ret = msgrcv(((int*)x.handle)[0], &t, len, 0, IPC_NOWAIT);
    if (ret == -1 && errno == ENOMSG) {
      debug("ipc_comm_recv(%s): no input, sleep", x.name);
      usleep(250*1000);
    } else {
      debug("ipc_comm_recv(%s): received input: %d bytes, ret=%d",
	    x.name, strlen(t.data), ret);
      break;
    }
  }
  if (ret > 0){
    memcpy(data, t.data, ret);
    data[ret] = '\0';
  } else {
    debug("ipc_comm_recv: msgrecv(%d, %p, %d, 0, IPC_NOWAIT: %s",
	  (int*)x.handle, &t, len, strerror(errno));
    ret = -1;
  }
  debug("ipc_comm_recv(%s): returns %d bytes\n", x.name, ret);
  return ret;
};

/*!
  @brief Send a large message to an output comm.
  Send a message larger than PSI_MSG_MAX bytes to an output comm by breaking
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
  debug("ipc_comm_send_nolimit(%s): %d bytes", x.name, len);
  int ret = -1;
  int msgsiz = 0;
  char msg[PSI_MSG_MAX];
  sprintf(msg, "%ld", (long)(len));
  ret = ipc_comm_send(x, msg, strlen(msg));
  if (ret != 0) {
    debug("ipc_comm_send_nolimit(%s): sending size of payload failed.", x.name);
    return ret;
  }
  int prev = 0;
  while (prev < len) {
    if ((len - prev) > PSI_MSG_MAX)
      msgsiz = PSI_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = ipc_comm_send(x, data + prev, msgsiz);
    if (ret != 0) {
      debug("ipc_comm_send_nolimit(%s): send interupted at %d of %d bytes.",
	    x.name, prev, len);
      break;
    }
    prev += msgsiz;
    debug("ipc_comm_send_nolimit(%s): %d of %d bytes sent",
	  x.name, prev, len);
  }
  if (ret == 0)
    debug("ipc_comm_send_nolimit(%s): %d bytes completed", x.name, len);
  return ret;
};

/*!
  @brief Receive a large message from an input comm.
  Receive a message larger than PSI_MSG_MAX bytes from an input comm by
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
  debug("ipc_comm_recv_nolimit(%s)", x.name);
  long len = 0;
  int ret = -1;
  int msgsiz = 0;
  char msg[PSI_MSG_MAX];
  int prev = 0;
  ret = ipc_comm_recv(x, msg, PSI_MSG_MAX);
  if (ret < 0) {
    debug("ipc_comm_recv_nolimit(%s): failed to receive payload size.", x.name);
    return -1;
  }
  ret = sscanf(msg, "%ld", &len);
  if (ret != 1) {
    debug("ipc_comm_recv_nolimit(%s): failed to parse payload size (%s)",
	  x.name, msg);
    return -1;
  }
  // Reallocate data if necessary
  if (len > len0) {
    *data = (char*)realloc(*data, len);
  }
  ret = -1;
  while (prev < len) {
    if ((len - prev) > PSI_MSG_MAX)
      msgsiz = PSI_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = ipc_comm_recv(x, (*data) + prev, msgsiz);
    if (ret < 0) {
      debug("ipc_comm_recv_nolimit(%s): recv interupted at %d of %d bytes.",
	    x.name, prev, len);
      break;
    }
    prev += ret;
    debug("ipc_comm_recv_nolimit(%s): %d of %d bytes received",
	  x.name, prev, len);
  }
  if (ret > 0) {
    debug("ipc_comm_recv_nolimit(%s): %d bytes completed", x.name, prev);
    return prev;
  } else {
    return -1;
  }
};


#endif /*CISIPCCOMM_H_*/
