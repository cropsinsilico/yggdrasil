#include <../tools.h>
#include <../serialize/serialize.h>
#include <comm_header.h>
#include <CommBase.h>
#include <IPCComm.h>
#include <ZMQComm.h>
#include <RPCComm.h>
#include <ServerComm.h>
#include <ClientComm.h>
#include <AsciiFileComm.h>
#include <AsciiTableComm.h>
#include <DefaultComm.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMUNICATION_H_
#define CISCOMMUNICATION_H_

/*! @brief Memory to keep track of comms to clean up at exit. */
static void **vcomms2clean;
static size_t ncomms2clean = 0;
static size_t clean_registered = 0;

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
  if ((strcmp(x->direction, "send") == 0) && (t != CLIENT_COMM))
    comm_send_eof(*x);
  int ret = 1;
  if (t == IPC_COMM)
    ret = free_ipc_comm(x);
  else if (t == ZMQ_COMM)
    ret = free_zmq_comm(x);
  else if (t == RPC_COMM)
    ret = free_rpc_comm(x);
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
  int idx = x->index_in_register;
  free_comm_base(x);
  if (idx >= 0) {
    free(vcomms2clean[idx]);
    vcomms2clean[idx] = NULL;
  }
  return ret;
};

/*!
  @brief Free comms created that were not freed.
*/
static inline
void clean_comms(void) {
  size_t i;
  for (i = 0; i < ncomms2clean; i++) {
    if (vcomms2clean[i] != NULL) {
      free_comm((comm_t*)(vcomms2clean[i]));
    }
  }
  free(vcomms2clean);
  ncomms2clean = 0;
#if defined(_WIN32) && defined(ZMQINSTALLED) // && defined(__cplusplus)
  zsys_shutdown();
#endif
};

/*!
  @brief Register a comm so that it can be cleaned up later if not done explicitly.
  @param[in] x comm_t* Address of communicator structure that should be
  registered.
  @returns int -1 if there is an error, 0 otherwise.
 */
static inline
int register_comm(comm_t *x) {
  if (clean_registered == 0) {
    atexit(clean_comms);
    clean_registered = 1;
  }
  vcomms2clean = (void**)realloc(vcomms2clean, sizeof(void*)*(ncomms2clean + 1));
  if (vcomms2clean == NULL) {
    cislog_error("register_comm(%s): Failed to realloc the comm list.", x->name);
    return -1;
  }
  x->index_in_register = (int)ncomms2clean;
  vcomms2clean[ncomms2clean++] = (void*)x;
  return 0;
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
  else if (t == RPC_COMM)
    flag = new_rpc_address(x);
  else if (t == SERVER_COMM)
    flag = new_server_address(x);
  else if (t == CLIENT_COMM)
    flag = new_client_address(x);
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
  else if (t == RPC_COMM)
    flag = init_rpc_comm(x);
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
  cislog_debug("init_comm_type(%s): Done, flag = %d", x->name, flag);
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
  comm_t *ret = new_comm_base(address, direction, t, seri_info);
  int flag;
  if (address == NULL) {
    flag = new_comm_type(ret);
  } else {
    flag = init_comm_type(ret);
  }
  if (flag < 0) {
    cislog_error("new_comm: Failed to initialize new comm address.");
    ret->valid = 0;
  } else {
    if (strlen(ret->name) == 0) {
      sprintf(ret->name, "temp.%s", ret->address);
    }
    flag = register_comm(ret);
    if (flag < 0) {
      cislog_error("new_comm: Failed to register new comm.");
      ret->valid = 0;
    }
  }
  return ret[0];
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
		 const void *seri_info) {
  cislog_debug("init_comm: Initializing comm.");
#ifdef _WIN32
  SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
  _set_abort_behavior(0,_WRITE_ABORT_MSG);
#endif
  comm_t *ret = init_comm_base(name, direction, t, seri_info);
  int flag = init_comm_type(ret);
  if (flag < 0) {
    cislog_error("init_comm(%s): Could not initialize comm.", name);
    ret->valid = 0;
  } else {
    flag = register_comm(ret);
    if (flag < 0) {
      cislog_error("init_comm(%s): Failed to register new comm.", name);
      ret->valid = 0;
    }
  }
  cislog_debug("init_comm(%s): Initialized comm.", ret->name);
  return ret[0];
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
  else if (t == RPC_COMM)
    ret = rpc_comm_nmsg(x);
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
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int comm_send_single(const comm_t x, const char *data, const size_t len) {
  int ret = -1;
  comm_type t = x.type;
  if (t == IPC_COMM)
    ret = ipc_comm_send(x, data, len);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_send(x, data, len);
  else if (t == RPC_COMM)
    ret = rpc_comm_send(x, data, len);
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
  @brief Create header for multipart message.
  @param[in] x comm_t structure that header will be sent to.
  @param[in] len size_t Size of message body.
  @param[out] comm_head_t Header info that should be sent before the message
  body.
*/
static inline
comm_head_t comm_send_multipart_header(const comm_t x, const size_t len) {
  comm_head_t head = init_header(len, NULL, NULL);
  sprintf(head.id, "%d", rand());
  head.multipart = 1;
  head.valid = 1;
  // Why was this necessary?
  if (x.type == SERVER_COMM)
    strcpy(head.id, x.address);
  else if (x.type == CLIENT_COMM)
    head = client_response_header(x, head);
  return head;
};

/*!
  @brief Send a large message in multiple parts via a new comm.
  @param[in] x comm_t Structure that message should be sent to.
  @param[in] data const char * Message that should be sent.
  @param[in] len size_t Size of data.
  @returns: int 0 if send successfull, -1 if send unsuccessful.
*/
static inline
int comm_send_multipart(const comm_t x, const char *data, const size_t len) {
  //char headbuf[CIS_MSG_BUF];
  int headbuf_len = CIS_MSG_BUF;
  int headlen = 0, ret = -1;
  comm_t xmulti = empty_comm_base();
  // Get header
  comm_head_t head = comm_send_multipart_header(x, len);
  if (head.valid == 0) {
    cislog_error("comm_send_multipart: Invalid header generated.");
    return -1;
  }
  char *headbuf = (char*)malloc(headbuf_len);
  if (headbuf == NULL) {
    cislog_error("comm_send_multipart: Failed to malloc headbuf.");
    return -1;
  }
  // Try to send body in header
  if (len < x.maxMsgSize) {
    headlen = format_comm_header(head, headbuf, headbuf_len);
    if (headlen < 0) {
      cislog_error("comm_send_multipart: Failed to format header.");
      free(headbuf);
      return -1;
    }
    if (((size_t)headlen + len) < x.maxMsgSize) {
      if (((size_t)headlen + len + 1) > (size_t)headbuf_len) {
        headbuf = (char*)realloc(headbuf, (size_t)headlen + len + 1);
        if (headbuf == NULL) {
          cislog_error("comm_send_multipart: Failed to realloc headbuf.");
          return -1;          
        }
        headbuf_len = headlen + (int)len + 1;
      }
      head.multipart = 0;
      memcpy(headbuf + headlen, data, len);
      headlen += (int)len;
      headbuf[headlen] = '\0';
    }
  }
  // Get head string
  if (head.multipart == 1) {
    // Get address for new comm and add to header
    xmulti = new_comm(NULL, "send", x.type, NULL);
    if (!(xmulti.valid)) {
      cislog_error("comm_send_multipart: Failed to initialize a new comm.");
      return -1;
    }
    strcpy(head.address, xmulti.address);
    headlen = format_comm_header(head, headbuf, headbuf_len);
    if (headlen < 0) {
      cislog_error("comm_send_multipart: Failed to format header.");
      free_comm(&xmulti);
      return -1;
    }
  }
  // Send header
  ret = comm_send_single(x, headbuf, headlen);
  if (ret < 0) {
    cislog_error("comm_send_multipart: Failed to send header.");
    if (head.multipart == 1)
      free_comm(&xmulti);
    return -1;
  }
  if (head.multipart == 0) {
    cislog_debug("comm_send_multipart(%s): %d bytes completed", x.name, head.size);
    return ret;
  }
  // Send multipart
  size_t msgsiz;
  size_t prev = 0;
  while (prev < head.size) {
    if ((head.size - prev) > xmulti.maxMsgSize)
      msgsiz = xmulti.maxMsgSize;
    else
      msgsiz = head.size - prev;
    ret = comm_send_single(xmulti, data + prev, msgsiz);
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
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int comm_send(const comm_t x, const char *data, const size_t len) {
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
  char buf[2048] = CIS_MSG_EOF;
  int ret = comm_send(x, buf, strlen(buf));
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than CIS_MSG_MAX bytes from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data char ** pointer to allocated buffer where the message
  should be saved. This should be a malloc'd buffer if allow_realloc is 1.
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @param[in] allow_realloc const int If 1, the buffer will be realloced if it
  is not large enought. Otherwise an error will be returned.
  @returns int -1 if message could not be received, otherwise the length of
  the received message.
 */
static inline
int comm_recv_single(const comm_t x, char **data, const size_t len,
		     const int allow_realloc) {
  comm_type t = x.type;
  int ret = -1;
  if (t == IPC_COMM)
    ret = ipc_comm_recv(x, data, len, allow_realloc);
  else if (t == ZMQ_COMM)
    ret = zmq_comm_recv(x, data, len, allow_realloc);
  else if (t == RPC_COMM)
    ret = rpc_comm_recv(x, data, len, allow_realloc);
  else if (t == SERVER_COMM)
    ret = server_comm_recv(x, data, len, allow_realloc);
  else if (t == CLIENT_COMM)
    ret = client_comm_recv(x, data, len, allow_realloc);
  else if (t == ASCII_FILE_COMM)
    ret = ascii_file_comm_recv(x, data, len, allow_realloc);
  else if ((t == ASCII_TABLE_COMM) || (t == ASCII_TABLE_ARRAY_COMM))
    ret = ascii_table_comm_recv(x, data, len, allow_realloc);
  else {
    cislog_error("comm_recv: Unsupported comm_type %d", t);
  }
  return ret;
};

/*!
  @brief Receive a message in multiple parts.
  @param[in] x comm_t Comm that message should be recieved from.
  @param[in] data char ** Pointer to buffer where message should be stored.
  @param[in] len size_t Size of data buffer.
  @param[in] headlen size_t Size of header in data buffer.
  @param[in] allow_realloc int If 1, data will be realloced if the incoming
  message is larger than the buffer. Otherwise, an error will be returned.
  @returns int -1 if unsucessful, size of message received otherwise.
*/
static inline
int comm_recv_multipart(const comm_t x, char **data, const size_t len,
			const size_t headlen, const int allow_realloc) {
  int ret;
  comm_head_t head = parse_comm_header(*data, headlen);
  if (!(head.valid)) {
    cislog_error("comm_recv(%s): Error parsing header.", x.name);
    ret = -1;
  } else {
    if (head.multipart) {
      // Move part of message after header to front of data
      memmove(*data, *data + head.bodybeg, head.bodysiz);
      (*data)[head.bodysiz] = '\0';
      // Return early if header contained entire message
      if (head.size == head.bodysiz) {
	return (int)(head.bodysiz);
      }
      // Get address for new comm
      comm_t xmulti = new_comm(head.address, "recv", x.type, NULL);
      if (!(xmulti.valid)) {
	cislog_error("comm_recv_multipart: Failed to initialize a new comm.");
	return -1;
      }
      // Receive parts of message
      size_t prev = head.bodysiz;
      size_t msgsiz = 0;
      // Reallocate data if necessary
      if ((head.size + 1) > len) {
	if (allow_realloc) {
	  *data = (char*)realloc(*data, head.size + 1);
	  if (*data == NULL) {
	    cislog_error("comm_recv_multipart(%s): Failed to realloc buffer",
			 x.name);
	    free_comm(&xmulti);
	    return -1;
	  }
 	} else {
	  cislog_error("comm_recv_multipart(%s): buffer is not large enough",
		       x.name);
	  free_comm(&xmulti);
	  return -1;
	}
      }
      ret = -1;
      char *pos = (*data) + prev;
      while (prev < head.size) {
	if ((head.size - prev) > xmulti.maxMsgSize)
	  msgsiz = xmulti.maxMsgSize;
	else
	  msgsiz = head.size - prev + 1;
	ret = comm_recv_single(xmulti, &pos, msgsiz, 0);
	if (ret < 0) {
	  cislog_debug("comm_recv_multipart(%s): recv interupted at %d of %d bytes.",
		       x.name, prev, head.size);
	  break;
	}
	prev += ret;
	pos += ret;
	cislog_debug("comm_recv_multipart(%s): %d of %d bytes received",
		     x.name, prev, head.size);
      }
      if (ret > 0) {
	cislog_debug("comm_recv_multipart(%s): %d bytes completed", x.name, prev);
	ret = (int)prev;
      }
      free_comm(&xmulti);
    } else {
      ret = (int)headlen;
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
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv(const comm_t x, char *data, const size_t len) {
  int ret = comm_recv_single(x, &data, len, 0);
  if (ret > 0) {
    if (is_eof(data)) {
      cislog_debug("comm_recv(%s): EOF received.", x.name);
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
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv_realloc(const comm_t x, char **data, const size_t len) {
  int ret = comm_recv_single(x, data, len, 1);
  if (ret > 0) {
    if (is_eof(*data)) {
      cislog_debug("comm_recv_realloc(%s): EOF received.", x.name);
      ret = -2;
    } else {
      ret = comm_recv_multipart(x, data, len, ret, 1);
    }
  }
  return ret;
};


/*! @brief alias for comm_send. */
static inline
int comm_send_nolimit(const comm_t x, const char *data, const size_t len) {
  return comm_send(x, data, len);
};

/*!
  @brief Send EOF message to the comm.
  @param[in] x comm_t structure that message should be sent to.
  @returns int 0 if send successfull, -1 otherwise.
*/
static inline
int comm_send_nolimit_eof(const comm_t x) {
  char buf[2048] = CIS_MSG_EOF;
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
  @param[in] len size_t length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received and -2 if EOF is received.
  Length of the received message otherwise.
 */
static inline
int comm_recv_nolimit(const comm_t x, char **data, const size_t len) {
  return comm_recv_realloc(x, data, len);
};

/*!
  @brief Send arguments as a small formatted message to an output comm.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output comm. If the message is larger than
  CIS_MSG_MAX or cannot be encoded, it will not be sent.  
  @param[in] x comm_t structure for comm that message should be sent to.
  @param[in] ap va_list arguments to be formatted into a message using sprintf.
  @returns int Number of arguments formatted if send succesfull, -1 if send
  unsuccessful.
 */
static inline
int vcommSend(const comm_t x, va_list ap) {
  size_t buf_siz = CIS_MSG_BUF;
  // char *buf = NULL;
  char *buf = (char*)malloc(buf_siz);
  if (buf == NULL) {
    cislog_error("vcommSend(%s): Failed to alloc buffer", x.name);
    return -1;
  }
  seri_t serializer = x.serializer;
  if (x.type == CLIENT_COMM) {
    comm_t *handle = (comm_t*)(x.handle);
    serializer = handle->serializer;
  }
  int args_used = 0;
  int ret = serialize(serializer, &buf, buf_siz, 1, &args_used, ap);
  if (ret < 0) {
    cislog_error("vcommSend(%s): serialization error", x.name);
    free(buf);
    return -1;
  }
  ret = comm_send(x, buf, ret);
  cislog_debug("vcommSend(%s): comm_send returns %d", x.name, ret);
  free(buf);
  if (ret < 0) {
    return ret;
  } else {
    return args_used;
  }
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
  size_t buf_siz = CIS_MSG_BUF;
  /* char *buf = NULL; */
  char *buf = (char*)malloc(buf_siz);
  if (buf == NULL) {
    cislog_error("vcommSend(%s): Failed to alloc buffer", x.name);
    return -1;
  }
  int ret = comm_recv_nolimit(x, &buf, buf_siz);
  if (ret < 0) {
    // cislog_error("vcommRecv(%s): Error receiving.", x.name);
    free(buf);
    return ret;
  }
  cislog_debug("vcommRecv(%s): comm_recv returns %d: %.10s...", x.name, ret, buf);
  // Deserialize message
  seri_t serializer = x.serializer;
  if (x.type == SERVER_COMM) {
    comm_t *handle = (comm_t*)(x.handle);
    serializer = handle->serializer;
  }
  ret = deserialize(serializer, buf, ret, ap);
  if (ret < 0) {
    cislog_error("vcommRecv(%s): error deserializing message (ret=%d)",
		 x.name, ret);
    free(buf);
    return -1;
  }
  cislog_debug("vcommRecv(%s): deserialize_format returns %d", x.name, ret);
  free(buf);
  return ret;
};

#define vcommSend_nolimit vcommSend
#define vcommRecv_nolimit vcommRecv


#endif /*CISCOMMUNICATION_H_*/
