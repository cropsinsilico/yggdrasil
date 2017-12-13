#include <stdlib.h>
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
  // Called to create temp comm for send/recv
  if ((strlen(comm->name) == 0) && (strlen(comm->address) > 0)) {
    comm->type = _default_comm;
    return init_default_comm(comm);
  }
  // Called to initialize/create client comm
  char *seri_out = (char*)malloc(strlen(comm->direction) + 1);
  strcpy(seri_out, comm->direction);
  /* printf("init_client_comm(%s): seri: %s\n", comm->name, seri_out); */
  comm_t *handle = (comm_t*)malloc(sizeof(comm_t));
  if (strlen(comm->name) == 0) {
    handle[0] = new_comm_base(comm->address, "send", _default_comm, (void*)seri_out);
    sprintf(handle->name, "client_request.%s", comm->address);
  } else {
    handle[0] = init_comm_base(comm->name, "send", _default_comm, (void*)seri_out);
  }
  ret = init_default_comm(handle);
  strcpy(comm->address, handle->address);
  /* printf("init_client_comm: name = %s, type=%d, address = %s\n", */
  /* 	 handle->name, handle->type, handle->address); */
  int *ncomm = (int*)malloc(sizeof(int));
  ncomm[0] = 0;
  handle->info = (void*)ncomm;
  strcpy(comm->direction, "send");
  comm->handle = (void*)handle;
  comm->always_send_header = 1;
  comm_t **info = (comm_t**)malloc(sizeof(comm_t*));
  info[0] = NULL;
  comm->info = (void*)info;
  return ret;
};

static inline
int get_client_response_count(const comm_t x) {
  comm_t *handle = (comm_t*)(x.handle);
  int out = 0;
  if (handle != NULL) {
    out = ((int*)(handle->info))[0];
  }
  return out;
};

static inline
void set_client_response_count(const comm_t x, const int new_val) {
  comm_t *handle = (comm_t*)(x.handle);
  if (handle != NULL) {
    int *count = (int*)(handle->info);
    count[0] = new_val;
  }
};

static inline
void inc_client_response_count(const comm_t x) {
  comm_t *handle = (comm_t*)(x.handle);
  if (handle != NULL) {
    int *count = (int*)(handle->info);
    count[0]++;
  }
};

static inline
void dec_client_response_count(const comm_t x) {
  comm_t *handle = (comm_t*)(x.handle);
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
    comm_t **info = (comm_t**)(x->info);
    if (*info != NULL) {
      int ncomm = get_client_response_count(*x);
      int i;
      for (i = 0; i < ncomm; i++) {
	free((char*)(info[0][i].serializer.info));
	free_default_comm(info[0] + i);
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
    char buf[CIS_MSG_MAX] = CIS_MSG_EOF;
    default_comm_send(*handle, buf, strlen(buf));
    free((char*)(handle->serializer.info));
    free_default_comm(handle);
    free(x->handle);
    x->handle = NULL;
  }
  // TODO: Why is the pointer invalid?
  /* printf("serializer: %s\n", (char*)(x->serializer.info)); */
  /* free((char*)(x->serializer.info)); */
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int client_comm_nmsg(const comm_t x) {
  comm_t *handle = (comm_t*)(x.handle);
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
  int ncomm = get_client_response_count(x);
  comm_t **res_comm = (comm_t**)(x.info);
  res_comm[0] = (comm_t*)realloc(res_comm[0], sizeof(comm_t)*(ncomm + 1));
  char *seri_copy = (char*)malloc(strlen((char*)(x.serializer.info)) + 1);
  strcpy(seri_copy, (char*)(x.serializer.info));
  (*res_comm)[ncomm] = new_comm_base(NULL, "recv", _default_comm, seri_copy);
  /* sprintf((*res_comm)[ncomm].name, "client_response.%s", (*res_comm)[ncomm].address); */
  ret = new_default_address(*res_comm + ncomm);
  if (ret < 0) {
    cislog_error("client_comm_send(%s): could not create response comm", x.name);
    return -1;
  }
  inc_client_response_count(x);
  ncomm = get_client_response_count(x);
  // Add address to header
  comm_head_t head = parse_comm_header(data, len);
  if (!(head.valid)) {
    cislog_error("client_comm_send(%s): Error parsing header.", x.name);
    return -1;
  }
  strcpy(head.response_address, (*res_comm)[ncomm - 1].address);
  sprintf(head.request_id, "%d", rand());
  char *new_data = (char*)malloc(BUFSIZ);
  ret = format_comm_header(head, new_data, BUFSIZ);
  if (ret < 0) {
    cislog_error("client_comm_send(%s): Error formatting.", x.name);
    free(new_data);
    return -1;
  }    
  // Send message with header
  comm_t *req_comm = (comm_t*)(x.handle);
  ret = default_comm_send(*req_comm, new_data, ret);
  free(new_data);
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
  if ((x.info == NULL) || (get_client_response_count(x) == 0)) {
    cislog_error("client_comm_recv(%s): no response comm registered", x.name);
    return -1;
  }
  comm_t **res_comm = (comm_t**)(x.info);
  int ret = default_comm_recv((*res_comm)[0], data, len);
  if (ret < 0)
    return ret;
  // Close response comm and decrement count of response comms
  free((char*)((*res_comm)[0].serializer.info));
  free_default_comm(&((*res_comm)[0]));
  dec_client_response_count(x);
  int nresp = get_client_response_count(x);
  memmove(*res_comm, *res_comm + 1, nresp*sizeof(comm_t));
  return ret;
};

#endif /*CISCLIENTCOMM_H_*/
