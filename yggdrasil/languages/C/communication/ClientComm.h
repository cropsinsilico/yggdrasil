/*! @brief Flag for checking if this header has already been included. */
#ifndef YGGCLIENTCOMM_H_
#define YGGCLIENTCOMM_H_

#include <../tools.h>
#include <CommBase.h>
#include <DefaultComm.h>
#include "../datatypes/datatypes.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

// Handle is send address
// Info is response
static unsigned _client_rand_seeded = 0;

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_client_address(comm_t *comm) {
  if (!(_client_rand_seeded)) {
    srand(ptr2seed(comm));
    _client_rand_seeded = 1;
  }
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
  int ret = 0;
  if (!(_client_rand_seeded)) {
    srand(ptr2seed(comm));
    _client_rand_seeded = 1;
  }
  // Called to create temp comm for send/recv
  if ((strlen(comm->name) == 0) && (strlen(comm->address) > 0)) {
    comm->type = _default_comm;
    return init_default_comm(comm);
  }
  // Called to initialize/create client comm
  dtype_t *dtype_out = create_dtype_format(comm->direction, 0, false);
  if (dtype_out == NULL) {
    ygglog_error("init_client_comm: Failed to create output datatype.");
    return -1;
  }
  comm_t *handle;
  if (strlen(comm->name) == 0) {
    handle = new_comm_base(comm->address, "send", _default_comm, dtype_out);
    sprintf(handle->name, "client_request.%s", comm->address);
  } else {
    handle = init_comm_base(comm->name, "send", _default_comm, dtype_out);
  }
  ret = init_default_comm(handle);
  strcpy(comm->address, handle->address);
  comm->handle = (void*)handle;
  // Keep track of response comms
  int *ncomm = (int*)malloc(sizeof(int));
  if (ncomm == NULL) {
    ygglog_error("init_client_comm: Failed to malloc ncomm.");
    return -1;
  }
  ncomm[0] = 0;
  handle->info = (void*)ncomm;
  strcpy(comm->direction, "send");
  comm->always_send_header = 1;
  comm_t ***info = (comm_t***)malloc(sizeof(comm_t**));
  if (info == NULL) {
    ygglog_error("init_client_comm: Failed to malloc info.");
    return -1;
  }
  info[0] = NULL;
  comm->info = (void*)info;
  return ret;
};

static inline
int get_client_response_count(const comm_t* x) {
  comm_t *handle = (comm_t*)(x->handle);
  int out = 0;
  if (handle != NULL) {
    out = ((int*)(handle->info))[0];
  }
  return out;
};

static inline
void set_client_response_count(const comm_t* x, const int new_val) {
  comm_t *handle = (comm_t*)(x->handle);
  if (handle != NULL) {
    int *count = (int*)(handle->info);
    count[0] = new_val;
  }
};

static inline
void inc_client_response_count(const comm_t* x) {
  comm_t *handle = (comm_t*)(x->handle);
  if (handle != NULL) {
    int *count = (int*)(handle->info);
    count[0]++;
  }
};

static inline
void dec_client_response_count(const comm_t* x) {
  comm_t *handle = (comm_t*)(x->handle);
  if (handle != NULL) {
    int *count = (int*)(handle->info);
    count[0]--;
  }
};

static inline
void free_client_response_count(comm_t *x) {
  comm_t *handle = (comm_t*)(x->handle);
  if (handle != NULL) {
    int *count = (int*)(handle->info);
    free(count);
    handle->info = NULL;
  }
};

/*!
  @brief Perform deallocation for client communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_client_comm(comm_t *x) {
  if (x->info != NULL) {
    comm_t ***info = (comm_t***)(x->info);
    if (info[0] != NULL) {
      int ncomm = get_client_response_count(x);
      int i;
      for (i = 0; i < ncomm; i++) {
        if (info[0][i] != NULL) {
          free_default_comm(info[0][i]);
	  free_comm_base(info[0][i]);
          free(info[0][i]);
        }
      }
      free(*info);
      info[0] = NULL;
    }
    free(info);
    x->info = NULL;
  }
  free_client_response_count(x);
  if (x->handle != NULL) {
    comm_t *handle = (comm_t*)(x->handle);
    free_default_comm(handle);
    free_comm_base(handle);
    free(x->handle);
    x->handle = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t* Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int client_comm_nmsg(const comm_t* x) {
  comm_t *handle = (comm_t*)(x->handle);
  int ret = default_comm_nmsg(handle);
  return ret;
};

/*!
  @brief Create response comm and add info to header.
  @param[in] x comm_t* structure that header will be sent to.
  @param[in] head comm_head_t Prexisting header structure.
  @returns comm_head_t Header structure that includes the additional
  information about the response comm.
*/
static inline
comm_head_t client_response_header(const comm_t* x, comm_head_t head) {
  // Initialize new comm
  int ncomm = get_client_response_count(x);
  comm_t ***res_comm = (comm_t***)(x->info);
  res_comm[0] = (comm_t**)realloc(res_comm[0], sizeof(comm_t*)*(ncomm + 1));
  if (res_comm[0] == NULL) {
    ygglog_error("client_response_header: Failed to realloc response comm.");
    head.valid = 0;
    return head;
  }
  dtype_t * dtype_copy = copy_dtype(x->datatype);
  res_comm[0][ncomm] = new_comm_base(NULL, "recv", _default_comm, dtype_copy);
  int ret = new_default_address(res_comm[0][ncomm]);
  if (ret < 0) {
    ygglog_error("client_response_header(%s): could not create response comm", x->name);
    head.valid = 0;
    return head;
  }
  res_comm[0][ncomm]->sent_eof[0] = 1;
  res_comm[0][ncomm]->recv_eof[0] = 1;
  inc_client_response_count(x);
  ncomm = get_client_response_count(x);
  ygglog_debug("client_response_header(%s): Created response comm number %d",
	       x->name, ncomm);
  // Add address & request ID to header
  strcpy(head.response_address, res_comm[0][ncomm - 1]->address);
  sprintf(head.request_id, "%d", rand());
  ygglog_debug("client_response_header(%s): response_address = %s, request_id = %s",
	       x->name, head.response_address, head.request_id);
  return head;
};

/*!
  @brief Send a message to the comm.
  @param[in] x comm_t* structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int client_comm_send(const comm_t* x, const char *data, const size_t len) {
  int ret;
  ygglog_debug("client_comm_send(%s): %d bytes", x->name, len);
  if (x->handle == NULL) {
    ygglog_error("client_comm_send(%s): no request comm registered", x->name);
    return -1;
  }
  comm_t *req_comm = (comm_t*)(x->handle);
  ret = default_comm_send(req_comm, data, len);
  if (is_eof(data)) {
    req_comm->sent_eof[0] = 1;
  }
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
int client_comm_recv(const comm_t* x, char **data, const size_t len, const int allow_realloc) {
  ygglog_debug("client_comm_recv(%s)", x->name);
  if ((x->info == NULL) || (get_client_response_count(x) == 0)) {
    ygglog_error("client_comm_recv(%s): no response comm registered", x->name);
    return -1;
  }
  comm_t ***res_comm = (comm_t***)(x->info);
  int ret = default_comm_recv(res_comm[0][0], data, len, allow_realloc);
  if (ret < 0) {
    ygglog_error("client_comm_recv(%s): default_comm_recv returned %d",
		 x->name, ret);
    return ret;
  }
  // Close response comm and decrement count of response comms
  ygglog_debug("client_comm_recv(%s): default_comm_recv returned %d",
	       x->name, ret);
  free_default_comm(res_comm[0][0]);
  free_comm_base(res_comm[0][0]);
  free(res_comm[0][0]);
  dec_client_response_count(x);
  int nresp = get_client_response_count(x);
  memmove(*res_comm, *res_comm + 1, nresp*sizeof(comm_t*));
  return ret;
};


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGCLIENTCOMM_H_*/
