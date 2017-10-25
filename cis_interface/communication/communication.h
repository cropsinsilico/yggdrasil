#include <../tools.h>
#include <../serialize/serialize.h>
#include <comm_header.h>
#include <CommBase.h>
#include <IPCComm.h>
#include <ZMQComm.h>
#include <AsciiFileComm.h>
#include <AsciiTableComm.h>
#include <DefaultComm.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMUNICATION_H_
#define CISCOMMUNICATION_H_

// Forward declaration of eof
static inline
int comm_send_eof(const comm_t x);

/*!
  @brief Perform deallocation for generic communicator.
  @param[in] x comm_t * Pointer to communicator to deallocate.
  @returns int 1 if there is an error, 0 otherwise.
*/
static inline
int free_comm(comm_t *x) {
  comm_type t = x->type;
  if (strcmp(x->direction, "send") == 0)
    comm_send_eof(*x);
  int ret = 1;
  if (t == IPC_COMM)
    ret = free_ipc_comm(x);
  else if (t == ZMQ_COMM)
    ret = free_zmq_comm(x);
  else if (t == SERVER_COMM)
    ret = free_server_comm(x);
  else if (t == CLIENT_COMM)
    ret = free_client_comm(x);
  else if (t == ASCII_FILE_COMM)
    ret = free_ascii_file_comm(x);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = free_ascii_table_comm(x);
  else {
    cislog_error("free_comm: Unsupported comm_type %d", t);
  }
  free_comm_base(x);
  return ret;
};

/*!
  @brief Initialize a new communicator based on its type.
  @param[in] x comm_t * Pointer to communicator structure initialized with
  new_base_comm;
  @returns int -1 if the comm could not be initialized.
 */
static inline
int new_comm_type(comm_t *x) {
  comm_type t = x->type;
  int flag;
  if (t == IPC_COMM)
    flag = new_ipc_address(x);
  else if (t == ZMQ_COMM)
    flag = new_zmq_address(x);
  /* else if (t == SERVER_COMM) */
  /*   flag = new_server_address(x); */
  /* else if (t == CLIENT_COMM) */
  /*   flag = new_client_address(x); */
  else if (t == ASCII_FILE_COMM)
    flag = new_ascii_file_address(x);
  else if (t == ASCII_TABLE_COMM)
    flag = new_ascii_table_address(x);
  else if (t == ASCII_TABLE_ARRAY_COMM)
    flag = new_ascii_table_array_address(x);
  else {
    cislog_error("new_comm_type: Unsupported comm_type %d", t);
    flag = -1;
  }
  return flag;
};

/*!
  @brief Initialize the communicator based on its type.
  @param[in] x comm_t * Pointer to communicator structure initialized with
  init_base_comm;
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_comm_type(comm_t *x) {
  comm_type t = x->type;
  int flag;
  if (t == IPC_COMM)
    flag = init_ipc_comm(x);
  else if (t == ZMQ_COMM)
    flag = init_zmq_comm(x);
  else if (t == SERVER_COMM)
    flag = init_server_comm(x);
  else if (t == CLIENT_COMM)
    flag = init_client_comm(x);
  else if (t == ASCII_FILE_COMM)
    flag = init_ascii_file_comm(x);
  else if (t == ASCII_TABLE_COMM)
    flag = init_ascii_table_comm(x);
  else if (t == ASCII_TABLE_ARRAY_COMM)
    flag = init_ascii_table_array_comm(x);
  else {
    cislog_error("init_comm_type: Unsupported comm_type %d", t);
    flag = -1;
  }
  return flag;
};

/*!
  @brief Initialize comm from the address.
  @param[in] address char * Address for new comm. If NULL, a new address is
  generated.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] t comm_type Type of comm that should be created.
  @param[in] seri_info Pointer to info for the serializer (e.g. format string).
  @returns comm_t Comm structure.
 */
static inline
comm_t new_comm(char *address, const char *direction, const comm_type t,
		void *seri_info) {
  comm_t ret = new_comm_base(address, direction, t, seri_info);
  int flag;
  if (address == NULL) {
    flag = new_comm_type(&ret);
  } else {
    flag = init_comm_type(&ret);
  }
  if (flag < 0) {
    cislog_error("new_comm: Failed to initialized new comm address.");
    ret.valid = 0;
  }
  return ret;
};

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
  comm_t ret = init_comm_base(name, direction, t, seri_info);
  int flag = init_comm_type(&ret);
  if (flag < 0) {
    cislog_error("init_comm: Could not initialize comm.");
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
  else if (t == SERVER_COMM)
    ret = server_comm_nmsg(x);
  else if (t == CLIENT_COMM)
    ret = client_comm_nmsg(x);
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
  @brief Send a single message to the comm.
  Send a message smaller than CIS_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int comm_send_single(const comm_t x, const char *data, const int len) {
  int ret = -1;
  comm_type t = x.type;
  if (t == IPC_COMM)
    ret = ipc_comm_send(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_send(x, data, len);
  else if (t == SERVER_COMM)
    ret = server_comm_send(x, data, len);
  else if (t == CLIENT_COMM)
    ret = client_comm_send(x, data, len);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_send(x, data, len);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_send(x, data, len);
  else {
    cislog_error("comm_send_single: Unsupported comm_type %d", t);
  }
  return ret;
};

/*!
  @brief Send a large message in multiple parts via a new comm.
  @param[in] x comm_t Structure that message should be sent to.
  @param[in] data const char * Message that should be sent.
  @param[in] len int Size of data.
  @returns: int 0 if send successfull, -1 if send unsuccessful.
*/
static inline
int comm_send_multipart(const comm_t x, const char *data, const int len) {
  // Get address for new comm
  comm_t xmulti = new_comm(NULL, "send", x.type, NULL);
  if (!(xmulti.valid)) {
    cislog_error("comm_send_multipart: Failed to initialize a new comm.");
    return -1;
  }
  // Create header
  comm_head_t head;
  head.size = len;
  strcpy(head.address, xmulti.address);
  if (x.type == SERVER_COMM)
    strcpy(head.id, x.address);
  char headbuf[BUFSIZ];
  int ret = format_comm_header(head, headbuf, BUFSIZ);
  if (ret < 0) {
    cislog_error("comm_send_multipart: Failed to format header.");
    return -1;
  }
  // Send header
  ret = comm_send_single(x, headbuf, ret);
  if (ret < 0) {
    cislog_error("comm_send_multipart: Failed to send header.");
    return -1;
  }
  // Send multipart
  int msgsiz;
  int prev = 0;
  while (prev < head.size) {
    if ((head.size - prev) > xmulti.maxMsgSize)
      msgsiz = xmulti.maxMsgSize;
    else
      msgsiz = head.size - prev;
    ret = comm_send_single(x, data + prev, msgsiz);
    if (ret < 0) {
      cislog_debug("comm_send_multipart(%s): send interupted at %d of %d bytes.",
		   x.name, prev, head.size);
      break;
    }
    prev += msgsiz;
    cislog_debug("comm_send_multipart(%s): %d of %d bytes sent",
		 x.name, prev, head.size);
  }
  if (ret == 0)
    cislog_debug("comm_send_multipart(%s): %d bytes completed", x.name, head.size);
  // Free multipart
  free_comm(&xmulti);
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
  if (((len > x.maxMsgSize) && (x.maxMsgSize > 0)) ||
      ((x.always_send_header) && (!(is_eof(data))))) {
    return comm_send_multipart(x, data, len);
  }
  ret = comm_send_single(x, data, len);
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
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than CIS_MSG_MAX bytes from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  mshould be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received, otherwise the length of
  the received message.
 */
static inline
int comm_recv_single(const comm_t x, char *data, const int len) {
  comm_type t = x.type;
  int ret = -1;
  if (t == IPC_COMM)
    ret = ipc_comm_recv(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_recv(x, data, len);
  else if (t == SERVER_COMM)
    ret = server_comm_recv(x, data, len);
  else if (t == CLIENT_COMM)
    ret = client_comm_recv(x, data, len);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_recv(x, data, len);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_recv(x, data, len);
  else {
    cislog_error("comm_recv: Unsupported comm_type %d", t);
  }
  return ret;
};

/*!
  @brief Receive a message in multiple parts.
  @param[in] x comm_t Comm that message should be recieved from.
  @param[in] data char ** Pointer to buffer where message should be stored.
  @param[in] len int Size of data buffer.
  @param[in] allow_realloc int If 1, data will be realloced if the incoming
  message is larger than the buffer. Otherwise, an error will be returned.
  @returns int -1 if unsucessful, size of message received otherwise.
*/
static inline
int comm_recv_multipart(const comm_t x, char **data, const int len,
			const int headlen, const int allow_realloc) {
  int ret;
  comm_head_t head = parse_comm_header(*data, headlen);
  if (!(head.valid)) {
    cislog_error("comm_recv(%s): Error parsing header.", x.name);
    ret = -1;
  } else {
    if (head.multipart) {
      // Get address for new comm
      comm_t xmulti = new_comm(head.address, "recv", x.type, NULL);
      if (!(xmulti.valid)) {
	cislog_error("comm_recv_multipart: Failed to initialize a new comm.");
	return -1;
      }
      // Receive parts of message
      int prev = 0;
      int msgsiz = 0;
      // Reallocate data if necessary
      if (head.size > len) {
	if (allow_realloc) {
	  *data = (char*)realloc(*data, head.size);
	} else {
	  cislog_error("comm_recv_multipart(%s): buffer is not large enough",
		       x.name);
	  return -1;
	}
      }
      ret = -1;
      while (prev < head.size) {
	if ((head.size - prev) > xmulti.maxMsgSize)
	  msgsiz = xmulti.maxMsgSize;
	else
	  msgsiz = head.size - prev;
	ret = comm_recv_single(xmulti, (*data) + prev, msgsiz);
	if (ret < 0) {
	  cislog_debug("comm_recv_multipart(%s): recv interupted at %d of %d bytes.",
		       x.name, prev, head.size);
	  break;
	}
	prev += ret;
	cislog_debug("comm_recv_multipart(%s): %d of %d bytes received",
		     x.name, prev, head.size);
      }
      if (ret > 0) {
	cislog_debug("comm_recv_multipart(%s): %d bytes completed", x.name, prev);
	ret = prev;
      }
    } else {
      ret = headlen;
    }
  }
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  An error will be returned if the buffer is not large enough.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the
  message should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv(const comm_t x, char *data, const int len) {
  int ret = comm_recv_single(x, data, len);
  if (ret > 0) {
    if (is_eof(data)) {
      cislog_debug("comm_recv(%s): EOF received.\n", x.name);
      ret = -2;
    } else {
      ret = comm_recv_multipart(x, &data, len, ret, 0);
    }
  }
  return ret;
};

/*!
  @brief Receive a message from an input comm, reallocating as necessary.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to pointer to allocated buffer where the
  message should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv_realloc(const comm_t x, char **data, const int len) {
  int ret = comm_recv_single(x, *data, len);
  if (ret > 0) {
    if (is_eof(*data)) {
      cislog_debug("comm_recv(%s): EOF received.\n", x.name);
      ret = -2;
    } else {
      ret = comm_recv_multipart(x, data, len, ret, 1);
    }
  }
  return ret;
};


/*! @brief alias for comm_send. */
static inline
int comm_send_nolimit(const comm_t x, const char *data, const int len) {
  return comm_send(x, data, len);
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
  @param[in] len int length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv_nolimit(const comm_t x, char **data, const int len) {
  return comm_recv_realloc(x, data, len);
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
  char *buf = (char*)malloc(CIS_MSG_MAX);
  int ret = serialize(x.serializer, &buf, CIS_MSG_MAX, 0, ap);
  if (ret < 0) {
    cislog_error("vcommSend(%s): serialization error", x.name);
    free(buf);
    return -1;
  }
  ret = comm_send(x, buf, ret);
  cislog_debug("vcommSend(%s): comm_send returns %d", x.name, ret);
  free(buf);
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
  cislog_debug("vcommRecv(%s): comm_recv returns %d: %s", x.name, ret, buf);
  // Deserialize message
  ret = deserialize(x.serializer, buf, ret, ap);
  if (ret < 0) {
    cislog_error("vcommRecv(%s): error deserializing message (ret=%d)",
		 x.name, ret);
    return -1;
  }
  cislog_debug("vcommRecv(%s): deserialize_format returns %d", x.name, ret);
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
  int ret = serialize(x.serializer, &buf, CIS_MSG_MAX, 1, ap);
  if (ret < 0) {
    cislog_error("vcommSend_nolimit(%s): serialization error", x.name);
    free(buf);
    return -1;
  }
  ret = comm_send_nolimit(x, buf, ret);
  cislog_debug("vcommSend_nolimit(%s): comm_send_nolimit returns %d", x.name, ret);
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
  cislog_debug("vcommRecv_nolimit(%s): comm_recv returns %d: %s", x.name, ret, buf);
  // Deserialize message
  ret = deserialize(x.serializer, buf, CIS_MSG_MAX, ap);
  if (ret < 0) {
    cislog_error("vcommRecv_nolimit(%s): error deserializing message (ret=%d)",
		 x.name, ret);
    return -1;
  }
  cislog_debug("vcommRecv_nolimit(%s): deserialize_format returns %d", x.name, ret);
  return ret;
};


#endif /*CISCOMMUNICATION_H_*/
