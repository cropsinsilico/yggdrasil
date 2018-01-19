/*! @brief Flag for checking if this header has already been included. */
#ifndef CISZMQCOMM_H_
#define CISZMQCOMM_H_

#include <CommBase.h>

#ifdef ZMQINSTALLED

#include <czmq.h>

static unsigned _zmq_rand_seeded = 0;
static unsigned _cisSocketsCreated = 0;
static int _last_port = 49152;

/*!
  @brief Create a new socket.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_zmq_address(comm_t *comm) {
  // TODO: Get protocol/host from input
  char protocol[50] = "tcp";
  char host[50] = "localhost";
  char address[100];
  if (strcmp(host, "localhost") == 0)
    strcpy(host, "127.0.0.1");
  if ((strcmp(protocol, "inproc") == 0) ||
      (strcmp(protocol, "ipc") == 0)) {
    // TODO: small chance of reusing same number
    int key = 0;
    if (!(_zmq_rand_seeded)) {
      srand(ptr2seed(comm));
      _zmq_rand_seeded = 1;
    }
    while (key == 0) key = rand();
    if (strlen(comm->name) == 0)
      sprintf(comm->name, "tempnewZMQ-%d", key);
    sprintf(address, "%s://%s", protocol, comm->name);
  } else {
    sprintf(address, "%s://%s:*[%d-]", protocol, host, _last_port + 1);
    /* strcat(address, ":!"); // For random port */
  }
  // Bind
  zsock_t *s = zsock_new(ZMQ_PAIR);
  zsock_set_linger(s, 100);
  if (s == NULL) {
    cislog_error("new_zmq_address: Could not initialize empty socket.");
    return -1;
  }
  int port = zsock_bind(s, "%s", address);
  if (port == -1) {
    cislog_error("new_zmq_address: Could not bind socket to address = %s",
		 address);
    return -1;
  }
  // Add port to address
  if ((strcmp(protocol, "inproc") != 0) &&
      (strcmp(protocol, "ipc") != 0)) {
    _last_port = port;
    sprintf(address, "%s://%s:%d", protocol, host, port);
  }
  strcpy(comm->address, address);
  if (strlen(comm->name) == 0)
    sprintf(comm->name, "tempnewZMQ-%d", port);
  // Unbind and connect if this is a recv socket
  // int ret;
  /* if (strcmp(comm->direction, "recv") == 0) { */
  /*   ret = zsock_unbind(s, "%s", comm->address); */
  /*   printf("unbound from %s (ret = %d)\n", comm->address, ret); */
  /*   if (ret == -1) { */
  /*     cislog_error("new_zmq_address: Could not unbind socket for connect."); */
  /*     return ret; */
  /*   } */
  /*   ret = zsock_connect(s, "%s", comm->address); */
  /*   if (ret == -1) { */
  /*     cislog_error("new_zmq_address: Could not connect socket to address = %s", */
  /* 		   address); */
  /*     return ret; */
  /*   } */
  /* } */
  comm->handle = (void*)s;
  _cisSocketsCreated++;
  return 0;
};

/*!
  @brief Initialize a ZeroMQ communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_zmq_comm(comm_t *comm) {
  int ret;
  if (comm->valid == 0)
    return -1;
  zsock_t *s = zsock_new(ZMQ_PAIR);
  /* if (s == NULL) { */
  /*   cislog_error("init_zmq_address: Could not initialize empty socket."); */
  /*   return -1; */
  /* } */
  /* zsock_set_linger(s, 100); */
  /* /\* int port = zsock_bind(s, comm->address); *\/ */
  /* /\* if (port == -1) { *\/ */
  /* /\*   cislog_error("init_zmq_address: Could not bind socket to address = %s", *\/ */
  /* /\* 		 comm->address); *\/ */
  /* /\*   return -1; *\/ */
  /* /\* } *\/ */
  /* /\* if (strlen(comm->name) == 0) *\/ */
  /* /\*  sprintf(comm->name, "tempinitZMQ-%d", port); *\/ */
  /* /\* if (0) { *\/ */
  /* /\* if (strcmp(comm->direction, "send") == 0) { *\/ */
  /* /\*   ret = zsock_bind(s, "%s", comm->address); *\/ */
  /* /\*   if (ret == -1) { *\/ */
  /* /\*     cislog_error("new_zmq_address: Could not bind socket to address = %s", *\/ */
  /* /\* 		   comm->address); *\/ */
  /* /\*     return ret; *\/ */
  /* /\*   } *\/ */
  /* /\* } else { *\/ */
  /* ret = zsock_connect(s, "%s", comm->address); */
  /* if (ret == -1) { */
  /*   cislog_error("new_zmq_address: Could not connect socket to address = %s", */
  /* 		 comm->address); */
  /*   return ret; */
  /* } */
  /* /\* } *\/ */
  /* if (strlen(comm->name) == 0) */
  /*   sprintf(comm->name, "tempinitZMQ-%s", comm->address); */
  /* // Asign to void pointer */
  /* comm->handle = (void*)s; */
  return 0;
};

/*!
  @brief Perform deallocation for ZMQ communicator.
  @param[in] x comm_t Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_zmq_comm(comm_t *x) {
  if (x->handle != NULL) {
    zsock_t *s = (zsock_t*)(x->handle);
    zsock_destroy(&s);
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
int zmq_comm_nmsg(const comm_t x) {
  int out = 0;
  if (x.handle != NULL) {
    zsock_t *s = (zsock_t*)(x.handle);
    zpoller_t *poller = zpoller_new(s);
    if (poller == NULL) {
      cislog_error("zmq_comm_nmsg: Could not create poller");
      return -1;
    }
    void *p = zpoller_wait(poller, 1);
    if (p == NULL)
      out = 0;
    else
      out = 1;
    zpoller_destroy(&poller);
  }
  return out;
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
int zmq_comm_send(const comm_t x, const char *data, const size_t len) {
  cislog_debug("zmq_comm_send(%s): %d bytes", x.name, len);
  if (comm_base_send(x, data, len) == -1)
    return -1;
  /* printf("(C) sending %d bytes to %s\n", len, x.address); */
  zsock_t *s = (zsock_t*)(x.handle);
  zframe_t *f = zframe_new(data, len);
  int ret = zframe_send(&f, s, 0);
  zframe_destroy(&f);
  cislog_debug("zmq_comm_send(%s): returning %d", x.name, ret);
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
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int zmq_comm_recv(const comm_t x, char **data, const size_t len,
		  const int allow_realloc) {
  cislog_debug("zmq_comm_recv(%s)", x.name);
  zsock_t *s = (zsock_t*)(x.handle);
  zframe_t *out = zframe_recv(s);
  if (out == NULL) {
    cislog_debug("zmq_comm_recv(%s): did not receive", x.name);
    return -1;
  }
  size_t len_recv = zframe_size(out);
  /* printf("(C) received %d bytes from %s\n", len_recv, x.address); */
  if ((len_recv + 1) > len) {
    if (allow_realloc) {
      cislog_debug("zmq_comm_recv(%s): reallocating buffer from %d to %d bytes.\n",
		   x.name, len, len_recv + 1);
      (*data) = (char*)realloc(*data, len_recv + 1);
    } else {
      cislog_error("zmq_comm_recv(%s): buffer (%d bytes) is not large enough for message (%d bytes)",
		   x.name, len, len_recv);
      return -((int)len_recv + 1);
    }
  }
  memcpy(*data, zframe_data(out), len_recv + 1);
  (*data)[len_recv] = '\0';
  zframe_destroy(&out);
  cislog_debug("zmq_comm_recv(%s): returning %d", x.name, len_recv);
  return (int)len_recv;
};


// Definitions in the case where ZMQ libraries not installed
#else /*ZMQINSTALLED*/

/*!
  @brief Print error message about ZMQ library not being installed.
 */
static inline
void zmq_install_error() {
  cislog_error("Compiler flag 'ZMQINSTALLED' not defined so ZMQ bindings are disabled.");
};

/*!
  @brief Perform deallocation for ZMQ communicator.
  @param[in] x comm_t Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_zmq_comm(comm_t *x) {
  zmq_install_error();
  return 1;
};

/*!
  @brief Create a new socket.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_zmq_address(comm_t *comm) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Initialize a ZeroMQ communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_zmq_comm(comm_t *comm) {
  zmq_install_error();
  return -1;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int zmq_comm_nmsg(const comm_t x) {
  zmq_install_error();
  return -1;
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
int zmq_comm_send(const comm_t x, const char *data, const size_t len) {
  zmq_install_error();
  return -1;
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
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int zmq_comm_recv(const comm_t x, char **data, const size_t len,
		  const int allow_realloc) {
  zmq_install_error();
  return -1;
};

#endif /*ZMQINSTALLED*/
#endif /*CISZMQCOMM_H_*/
