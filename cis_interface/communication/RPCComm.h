/*! @brief Flag for checking if this header has already been included. */
#ifndef CISRPCCOMM_H_
#define CISRPCCOMM_H_

#include <CommBase.h>
#include <DefaultComm.h>
#include <comm_header.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

// Handle is output comm
// Info is input comm

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_rpc_address(comm_t *comm) {
  comm->type = _default_comm;
  return new_default_address(comm);
};

/*!
  @brief Initialize a rpc communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_rpc_comm(comm_t *comm) {
  int ret;
  // Input comm
  comm_t *info = init_comm_base(comm->name, "recv", _default_comm,
				comm->serializer->info);
  ret = init_default_comm(info);
  if (ret < 0) {
    cislog_error("init_rpc_comm(%s): Failed to initialize input comm", comm->name);
    return -1;
  }
  comm->info = (void*)info;
  // Output comm
  char *seri_out = (char*)malloc(strlen(comm->direction) + 1);
  if (seri_out == NULL) {
    cislog_error("init_rpc_comm(%s): Failed to malloc seri_out.");
    return -1;
  }
  strcpy(seri_out, comm->direction);
  comm_t *handle = init_comm_base(comm->name, "send", _default_comm,
				  (void*)seri_out);
  ret = init_default_comm(handle);
  if (ret < 0) {
    cislog_error("init_rpc_comm(%s): Failed to initialize output comm", comm->name);
    return -1;
  }
  comm->handle = (void*)handle;
  // Clean up
  strcpy(comm->direction, "send");
  free(seri_out);
  return ret;
};

/*!
  @brief Perform deallocation for rpc communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_rpc_comm(comm_t *x) {
  if (x->handle != NULL) {
    comm_t *handle = (comm_t*)(x->handle);
    free_default_comm(handle);
    free(x->handle);
    x->handle = NULL;
  }
  if (x->info != NULL) {
    comm_t *info = (comm_t*)(x->info);
    free_default_comm(info);
    free(x->info);
    x->info = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int rpc_comm_nmsg(const comm_t x) {
  comm_t *info = (comm_t*)(x.info);
  int ret = default_comm_nmsg(*info);
  return ret;
};

/*!
  @brief Send a message to the comm.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int rpc_comm_send(const comm_t x, const char *data, const size_t len) {
  cislog_debug("rpc_comm_send(%s): %d bytes", x.name, len);
  if (x.handle == NULL) {
    cislog_error("rpc_comm_send(%s): no output comm registered", x.name);
    return -1;
  }
  comm_t *res_comm = (comm_t*)(x.handle);
  return default_comm_send(*res_comm, data, len);
};

/*!
  @brief Receive a message from an input comm.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data char ** pointer to allocated buffer where the message
  should be saved. This should be a malloc'd buffer if allow_realloc is 1.
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @param[in] allow_realloc const int If 1, the buffer will be realloced if it
  is not large enought. Otherwise an error will be returned.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int rpc_comm_recv(const comm_t x, char **data, const size_t len,
		  const int allow_realloc) {
  cislog_debug("rpc_comm_recv(%s)", x.name);
  if (x.info == NULL) {
    cislog_error("rpc_comm_recv(%s): no input comm registered", x.name);
    return -1;
  }
  comm_t *req_comm = (comm_t*)(x.info);
  return default_comm_recv(*req_comm, data, len, allow_realloc);
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*CISRPCCOMM_H_*/
