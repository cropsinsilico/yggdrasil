#include <../tools.h>
#include <CommBase.h>
#include <DefaultComm.h>
#include <comm_header.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCLIENTCOMM_H_
#define CISCLIENTCOMM_H_

// Handle is send address
// Info is response

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_client_address(comm_t *comm) {
  comm->type = _default_comm;
  return new_default_address(comm);
};

/*!
  @brief Initialize a client communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_client_comm(comm_t *comm) {
  int ret;
  char *seri_out = (char*)malloc(strlen(comm->direction) + 1);
  strcpy(seri_out, comm->direction);
  comm_t *handle = (comm_t*)malloc(sizeof(comm_t));
  handle[0] = init_comm_base(comm->name, "send", _default_comm, (void*)seri_out);
  ret = init_default_comm(handle);
  strcpy(comm->direction, "send");
  comm->handle = (void*)handle;
  comm->always_send_header = 1;
  comm->maxMsgSize = 0; // Used by this comm to be the number of response comms
  free(seri_out);
  return ret;
};

/*!
  @brief Perform deallocation for client communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_client_comm(comm_t *x) {
  if (x->handle != NULL) {
    comm_t *handle = (comm_t*)(x->handle);
    free_default_comm(handle);
    free(x->handle);
    x->handle = NULL;
  }
  if (x->info != NULL) {
    int i;
    comm_t *info;
    for (i = 0; i < x->maxMsgSize; i++) {
      info = (comm_t*)(x->info) + i;
      free_default_comm(info);
    }
    free(x->info);
    x->info = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int client_comm_nmsg(const comm_t x) {
  comm_t *handle = (comm_t*)(x->handle);
  int ret = default_comm_nmsg(*handle);
  return ret;
};

/*!
  @brief Send a message to the comm.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int client_comm_send(comm_t x, const char *data, const int len) {
  int ret;
  cislog_debug("client_comm_send(%s): %d bytes", x.name, len);
  if (x.handle == NULL) {
    cislog_error("client_comm_send(%s): no request comm registered", x.name);
    return -1;
  }
  if (is_eof(data)) {
    // Send EOF message without header
    comm_t *req_comm = (comm_t*)(x.handle);
    ret = default_comm_send(*req_comm, data, len);
    return ret;
  }
  // Initialize new comm
  comm_t *res_comm = (comm_t*)(x.info);
  res_comm = (comm_t*)realloc(res_comm, sizeof(comm_t)*(x.maxMsgSize + 1));
  res_comm[x.maxMsgSize] = new_comm_base(NULL, "recv", _default_comm,
					 x->serializer.info);
  ret = new_default_address(res_comm + x.maxMsgSize);
  if (ret < 0) {
    cislog_error("client_comm_send(%s): could not create response comm", x.name);
    return -1;
  }
  x.maxMsgSize++;
  x->info = (void*)res_comm;
  // Add address to header
  comm_head_t head = parse_comm_header(data, len);
  if (!(head.valid)) {
    cislog_error("client_comm_send(%s): Error parsing header.", x.name);
    return -1;
  }
  strcpy(head.response_address, res_comm[x.maxMsgSize - 1].address);
  ret = format_comm_header(head, data, BUFSIZ);
  if (ret < 0) {
    cislog_error("client_comm_send(%s): Error formatting.", x.name);
    return -1;
  }    
  // Send message with header
  comm_t *req_comm = (comm_t*)(x.handle);
  ret = default_comm_send(*req_comm, data, len);
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int client_comm_recv(comm_t x, char *data, const int len) {
  cislog_debug("client_comm_recv(%s)", x.name);
  if (x.info == NULL) {
    cislog_error("client_comm_recv(%s): no response comm registered", x.name);
    return -1;
  }
  comm_t *res_comm = (comm_t*)(x.info);
  int ret = default_comm_recv(res_comm[0], data, len);
  if (ret < 0)
    return ret;
  // Close response comm and decrement count of response comms
  free_default_comm(res_comm);
  x.maxMsgSize -= 1;
  if (x.maxMsgSize == 0) {
    free(x.info);
    x.info = NULL;
  } else {
    memmove(res_comm, res_comm + 1, x.maxMsgSize*sizeof(comm_t));
  }
  return ret;
};

#endif /*CISCLIENTCOMM_H_*/
