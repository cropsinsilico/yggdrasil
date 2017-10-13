#include <../tools.h>
#include <../serialize/serialize.h>
#include <CommBase.h>
#include <IPCComm.h>
#include <ZMQComm.h>
#include <AsciiFileComm.h>
#include <AsciiTableComm.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMUNICATION_H_
#define CISCOMMUNICATION_H_

comm_type _default_comm = IPC_COMM;

/*!
  @brief Initialize a generic communicator.
  The name is used to locate the comm address stored in the associated
  environment variable.
  @param[in] name Name of environment variable that the queue address is
  stored in.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] t comm_type Type of comm that should be created.
  @param[in] seri_info Pointer to info for the serializer (e.g. format string).
  @returns comm_t Comm structure.
 */
static inline
comm_t init_comm(const char *name, const char *direction, const comm_type t,
		 void *seri_info) {
  comm_t ret;
  if (t == IPC_COMM)
    ret = init_ipc_comm(name, direction, seri_info);
  else if (t == ZMQ_COMM)
    ret = init_zmq_comm(name, direction, seri_info);
  else if (t == ASCII_FILE_COMM)
    ret = init_ascii_file_comm(name, direction, seri_info);
  else if (t == ASCII_TABLE_COMM)
    ret = init_ascii_table_comm(name, direction, seri_info);
  else if (t == ASCII_TABLE_ARRAY_COMM)
    ret = init_ascii_table_array_comm(name, direction, seri_info);
  else {
    cislog_error("init_comm: Unsupported comm_type %d", t);
    ret.valid = 0;
  }
  return ret;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages.
 */
static inline
int comm_nmsg(const comm_t x) {
  comm_type t = x.type;
  int ret = -1;
  if (t == IPC_COMM)
    ret = ipc_comm_nmsg(x);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_nmsg(x);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_nmsg(x);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_nmsg(x);
  else {
    cislog_error("comm_nmsg: Unsupported comm_type %d", t);
  }
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
int comm_send(const comm_t x, const char *data, const int len) {
  int ret = -1;
  if (len > CIS_MSG_MAX) {
    cislog_error("comm_send(%s): message too large for single packet (CIS_MSG_MAX=%d, len=%d)",
		 x.name, CIS_MSG_MAX, len);
    return ret;
  }
  comm_type t = x.type;
  if (t == IPC_COMM)
    ret = ipc_comm_send(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_send(x, data, len);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_send(x, data, len);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_send(x, data, len);
  else {
    cislog_error("comm_send: Unsupported comm_type %d", t);
  }
  return ret;
};

/*!
  @brief Send EOF message to the comm.
  @param[in] x comm_t structure that message should be sent to.
  @returns int 0 if send successfull, -1 otherwise.
*/
static inline
int comm_send_eof(const comm_t x) {
  char buf[CIS_MSG_MAX] = CIS_MSG_EOF;
  int ret = comm_send(x, buf, strlen(buf));
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than CIS_MSG_MAX bytes from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv(const comm_t x, char *data, const int len) {
  comm_type t = x.type;
  int ret = -1;
  if (t == IPC_COMM)
    ret = ipc_comm_recv(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_recv(x, data, len);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_recv(x, data, len);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_recv(x, data, len);
  else {
    cislog_error("comm_recv: Unsupported comm_type %d", t);
  }
  if ((ret > 0) && (is_eof(data))) {
    debug("comm_recv(%s): EOF received.\n", x.name);
    ret = -2;
  }
  return ret;
};

/*!
  @brief Send a large message to an output comm.
  Send a message larger than CIS_MSG_MAX bytes to an output comm by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  comm_recv_nolimit for communication to make sense.
  @param[in] x comm_t structure that message should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int comm_send_nolimit(const comm_t x, const char *data, const int len) {
  int ret = -1;
  comm_type t = x.type;
  if (t == IPC_COMM)
    ret = ipc_comm_send_nolimit(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_send_nolimit(x, data, len);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_send_nolimit(x, data, len);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_send_nolimit(x, data, len);
  else {
    cislog_error("comm_send_nolimit: Unsupported comm_type %d", t);
  }
  return ret;
};

/*!
  @brief Send EOF message to the comm.
  @param[in] x comm_t structure that message should be sent to.
  @returns int 0 if send successfull, -1 otherwise.
*/
static inline
int comm_send_nolimit_eof(const comm_t x) {
  char buf[CIS_MSG_MAX] = CIS_MSG_EOF;
  int ret = comm_send_nolimit(x, buf, strlen(buf));
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
  @param[in] len int length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv_nolimit(const comm_t x, char **data, const int len) {
  comm_type t = x.type;
  int ret = -1;
  if (t == IPC_COMM)
    ret = ipc_comm_recv_nolimit(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_recv_nolimit(x, data, len);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_recv_nolimit(x, data, len);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_recv_nolimit(x, data, len);
  else {
    cislog_error("comm_recv_nolimit: Unsupported comm_type %d", t);
  }
  if ((ret > 0) && (is_eof(data))) {
    debug("comm_recv_nolimit(%s): EOF received.\n", x.name);
    ret = -2;
  }
  return ret;
};

/*!
  @brief Send arguments as a small formatted message to an output comm.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output comm. If the message is larger than
  CIS_MSG_MAX or cannot be encoded, it will not be sent.  
  @param[in] x comm_t structure for comm that message should be sent to.
  @param[in] ap va_list arguments to be formatted into a message using sprintf.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int vcommSend(const comm_t x, va_list ap) {
  char buf[CIS_MSG_MAX];
  int ret = serialize(x.serializer, CIS_MSG_MAX, 0, ap);
  if (ret < 0) {
    cislog_error("vcommSend(%s): serialization error", x.name);
    return -1;
  }
  ret = comm_send(x, buf, ret);
  debug("vcommSend(%s): comm_send returns %d", x.name, ret);
  return ret;
};

/*!
  @brief Assign arguments by receiving and parsing a message from an input comm.
  Receive a message smaller than CIS_MSG_MAX bytes from an input comm and parse
  it using the associated format string.
  @param[in] x comm_t structure for comm that message should be sent to.
  @param[out] ap va_list arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed. -2 is
  returned if EOF is received.
 */
static inline
int vcommRecv(const comm_t x, va_list ap) {
  // Receive message
  char buf[CIS_MSG_MAX];
  int ret = comm_recv(x, buf, CIS_MSG_MAX);
  if (ret < 0) {
    /* cislog_error("vcommRecv(%s): Error receiving.", x.name); */
    return ret;
  }
  debug("vcommRecv(%s): comm_recv returns %d: %s", x.name, ret, buf);
  // Deserialize message
  ret = deserialize(x.serializer, buf, CIS_MSG_MAX, ap);
  if (ret < 0) {
    cislog_error("vcommRecv(%s): error deserializing message (ret=%d)",
		 x.name, ret);
    return -1;
  }
  debug("vcommRecv(%s): deserialize_format returns %d", x.name, ret);
  return ret;
};

/*!
  @brief Send arguments as a large formatted message to an output comm.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output comm. The message can be larger than
  CIS_MSG_MAX. If it cannot be encoded, it will not be sent.  
  @param[in] cisQ cisOutput_t structure that comm should be sent to.
  @param[in] ap va_list arguments to be formatted into a message using sprintf.
  @returns int 0 if formatting and send succesfull, -1 if formatting or send
  unsuccessful.
 */
static inline
int vcommSend_nolimit(const comm_t x, va_list ap) {
  char *buf = (char*)malloc(CIS_MSG_MAX);
  int ret = serialize(x.serializer, buf, CIS_MSG_MAX, 1, ap);
  if (ret < 0) {
    cislog_error("vcommSend_nolimit(%s): serialization error", x.name);
    return -1;
  }
  ret = comm_send_nolimit(x, buf, ret);
  debug("vcommSend_nolimit(%s): comm_send_nolimit returns %d", x.name, ret);
  free(buf);
  return ret;
};

/*!
  @brief Assign arguments by receiving and parsing a message from an input comm.
  Receive a message larger than CIS_MSG_MAX bytes in chunks from an input comm
  and parse it using the associated format string.
  @param[in] cisQ cisOutput_t structure that message should be sent to.
  @param[out] ap va_list arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed. -2 is
  returned if EOF is received.
 */
static inline
int vcommRecv_nolimit(const comm_t x, va_list ap) {
  // Receive message
  char *buf = (char*)malloc(CIS_MSG_MAX);
  int ret = comm_recv_nolimit(x, &buf, CIS_MSG_MAX);
  if (ret < 0) {
    /* cislog_error("vcommRecv_nolimit(%s): Error receiving.", x.name); */
    return ret;
  }
  debug("vcommRecv_nolimit(%s): comm_recv returns %d: %s", x.name, ret, buf);
  // Deserialize message
  ret = deserialize(x.serializezr, buf, CIS_MSG_MAX, ap);
  if (ret < 0) {
    cislog_error("vcommRecv_nolimit(%s): error deserializing message (ret=%d)",
		 x.name, ret);
    return -1;
  }
  debug("vcommRecv_nolimit(%s): deserialize_format returns %d", x.name, ret);
  return ret;
};

/*!
  @brief Perform deallocation for generic communicator.
  @param[in] comm_t Communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_comm(comm_t x) {
  comm_type t = x.type;
  if (strcmp(x.direction, "send") == 0)
    comm_send_eof(x);
  int ret = 1;
  if (t == IPC_COMM)
    ret = free_ipc_comm(x);
  else if (t == ZMQ_COMM)
    ret = free_zmq_comm(x);
  else if (t == ASCII_FILE_COMM)
    ret = free_ascii_file_comm(x);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = free_ascii_table_comm(x);
  else {
    cislog_error("free_comm: Unsupported comm_type %d", t);
  }
  return ret;
};


#endif /*CISCOMMUNICATION_H_*/
