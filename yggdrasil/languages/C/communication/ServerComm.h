/*! @brief Flag for checking if this header has already been included. */
#ifndef YGGSERVERCOMM_H_
#define YGGSERVERCOMM_H_

#include <CommBase.h>
#include <DefaultComm.h>
#include "../datatypes/datatypes.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

// Handle is recv address
// Info is response

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_server_address(comm_t *comm) {
  comm->type = _default_comm;
  return new_default_address(comm);
};

/*!
  @brief Initialize a server communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_server_comm(comm_t *comm) {
  int ret = 0;
  // Called to create temp comm for send/recv
  if ((strlen(comm->name) == 0) && (strlen(comm->address) > 0)) {
    comm->type = _default_comm;
    return init_default_comm(comm);
  }
  // Called to initialize/create server comm
  dtype_t *dtype_in = create_dtype_format(comm->direction, 0, false);
  if (dtype_in == NULL) {
    ygglog_error("init_server_comm: Failed to create dtype_in.");
    return -1;
  }
  comm_t *handle;
  if (strlen(comm->name) == 0) {
    handle = new_comm_base(comm->address, "recv", _default_comm, dtype_in);
    sprintf(handle->name, "server_request.%s", comm->address);
  } else {
    handle = init_comm_base(comm->name, "recv", _default_comm, dtype_in);
  }
  ret = init_default_comm(handle);
  strcpy(comm->address, handle->address);
  // printf("init_server_comm: name = %s, type=%d, address = %s\n",
  // 	 handle->name, handle->type, handle->address);
  strcpy(comm->direction, "recv");
  comm->handle = (void*)handle;
  if (_default_comm == ZMQ_COMM) {
    comm->always_send_header = 1;
  } else {
    comm->always_send_header = 1; // Always send header.
  }
  comm_t **info = (comm_t**)malloc(sizeof(comm_t*));
  if (info == NULL) {
    ygglog_error("init_server_comm: Failed to malloc info.");
    return -1;
  }
  info[0] = NULL;
  comm->info = (void*)info;
  return ret;
};

/*!
  @brief Perform deallocation for server communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_server_comm(comm_t *x) {
  if (x->handle != NULL) {
    comm_t *handle = (comm_t*)(x->handle);
    free_default_comm(handle);
    free_comm_base(handle);
    free(x->handle);
    x->handle = NULL;
  }
  if (x->info != NULL) {
    comm_t **info = (comm_t**)(x->info);
    if (*info != NULL) {
      free_default_comm(*info);
      free_comm_base(*info);
      free(*info);
    }
    free(info);
    x->info = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t* Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int server_comm_nmsg(const comm_t* x) {
  comm_t *handle = (comm_t*)(x->handle);
  int ret = default_comm_nmsg(handle);
  return ret;
};

/*!
  @brief Send a message to the comm.
  @param[in] x comm_t* structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int server_comm_send(const comm_t* x, const char *data, const size_t len) {
  ygglog_debug("server_comm_send(%s): %d bytes", x->name, len);
  if (x->info == NULL) {
    ygglog_error("server_comm_send(%s): no response comm registered", x->name);
    return -1;
  }
  comm_t **res_comm = (comm_t**)(x->info);
  if (res_comm[0] == NULL) {
    ygglog_error("server_comm_send(%s): no response comm registered", x->name);
    return -1;
  }
  int ret = default_comm_send(res_comm[0], data, len);
  // Wait for msg to be received?
  free_default_comm(res_comm[0]);
  free_comm_base(res_comm[0]);
  free(res_comm[0]);
  res_comm[0] = NULL;
  return ret;
};

/*!
  @brief Receive a message from an input comm.
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
int server_comm_recv(comm_t* x, char **data, const size_t len, const int allow_realloc) {
  ygglog_debug("server_comm_recv(%s)", x->name);
  if (x->handle == NULL) {
    ygglog_error("server_comm_recv(%s): no request comm registered", x->name);
    return -1;
  }
  comm_t *req_comm = (comm_t*)(x->handle);
  int ret = default_comm_recv(req_comm, data, len, allow_realloc);
  if (ret < 0) {
    return ret;
  }
  // Return EOF
  if (is_eof(*data)) {
    req_comm->recv_eof[0] = 1;
    return ret;
  }
  // Initialize new comm from received address
  comm_head_t head = parse_comm_header(*data, ret);
  if (!(head.valid)) {
    ygglog_error("server_comm_recv(%s): Error parsing header.", x->name);
    return -1;
  }
  // Return EOF
  if (is_eof((*data) + head.bodybeg)) {
    req_comm->recv_eof[0] = 1;
    return ret;
  }
  // If there is not a response address
  if (strlen(head.response_address) == 0) {
    ygglog_error("server_comm_recv(%s): No response address in message.", x->name);
    return -1;
  }
  strcpy(x->address, head.id);
  dtype_t *dtype_copy = copy_dtype(x->datatype);
  if (dtype_copy == NULL) {
    ygglog_error("server_comm_recv(%s): Failed to create dtype_copy.");
    return -1;
  }
  comm_t **res_comm = (comm_t**)(x->info);
  res_comm[0] = new_comm_base(head.response_address, "send", _default_comm,
			      dtype_copy);
  /* sprintf(res_comm[0]->name, "server_response.%s", res_comm[0]->address); */
  int newret;
  newret = init_default_comm(res_comm[0]);
  if (newret < 0) {
    ygglog_error("server_comm_recv(%s): Could not initialize response comm.", x->name);
    return newret;
  }
  res_comm[0]->sent_eof[0] = 1;
  res_comm[0]->recv_eof[0] = 1;
  return ret;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGSERVERCOMM_H_*/
