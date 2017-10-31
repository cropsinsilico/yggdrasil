#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <czmq.h>
#include <CommBase.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISZMQCOMM_H_
#define CISZMQCOMM_H_

static unsigned _zmq_rand_seeded = 0;
static unsigned _cisSocketsCreated;

/*!
  @brief Create a new socket.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_zmq_address(comm_t *comm) {
  // TODO: Get protocol/host from input
  char protocol[50] = "inproc";
  char host[50] = "localhost";
  char address[100];
  if (stcmp(host, "localhost") == 0)
    host = "127.0.0.1";
  int ret;
  if (strcmp(protocol, "inproc") == 0) {
    // TODO: small chance of reusing same number
    int key = 0;
    if (!(_zmq_rand_seeded)) {
      srand((unsigned long)comm); //time(NULL));
      _zmq_rand_seeded = 1;
    }
    while (key == 0) key = rand();
    if (strlen(comm->name) == 0)
      sprintf(comm->name, "tempnewZMQ-%d", key);
    sprintf(address, "inproc://%s", comm->name);
  } else {
    sprintf(address, "%s://%s", protocol, host);
    strcat(address, ":!"); // For random port
  }
  // Bind
  zsock_t *s = zsock_new(ZMQ_PAIR);
  if (s == NULL) {
    cislog_error("new_zmq_address: Could not initialize empty socket.");
    return -1;
  }
  int port = zsock_bind(s, address);
  if (port == -1) {
    cislog_error("new_zmq_address: Could not bind socket to address = %s",
		 address);
    return -1;
  }
  if (strlen(comm->name) == 0)
    sprintf(comm->name, "tempnewZMQ-%d", port);
  strcpy(comm->address, zsock_endpoint(s));
  // Unbind and connect if this is a recv socket
  if (strcmp(comm->direction, "recv") == 0) {
    ret = zsock_unbind(s, comm->address);
    if (ret == -1) {
      cislog_error("new_zmq_address: Could not unbind socket for connect.");
      return ret;
    }
    ret = zsock_connect(z, comm->address);
    if (ret == -1) {
      cislog_error("new_zmq_address: Could not connect socket to address = %s",
		   address);
      return ret;
    }
  }
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
  if (comm->valid == 0)
    return -1;
  zsock_t *s = zsock_new(ZMQ_PAIR);
  if (s == NULL) {
    cislog_error("init_zmq_address: Could not initialize empty socket.");
    return -1;
  }
  /* int port = zsock_bind(s, comm->address); */
  /* if (port == -1) { */
  /*   cislog_error("init_zmq_address: Could not bind socket to address = %s", */
  /* 		 comm->address); */
  /*   return -1; */
  /* } */
  /* if (strlen(comm->name) == 0) */
  /*  sprintf(comm->name, "tempinitZMQ-%d", port); */
  if (strcmp(comm->direction, "recv") == 0) {
    ret = zsock_connect(z, comm->address);
    if (ret == -1) {
      cislog_error("new_zmq_address: Could not connect socket to address = %s",
		   address);
      return ret;
    }
  } else {
    ret = zsock_bind(z, comm->address);
    if (ret == -1) {
      cislog_error("new_zmq_address: Could not bind socket to address = %s",
		   address);
      return ret;
    }
  }
  if (strlen(comm->name) == 0)
    sprintf(comm->name, "tempinitZMQ-%s", comm->address);
  
  zsock_t *s = zsock_new_pair(comm->address);
  comm->handle = (void*)s;
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
  if (x->handle != NULL) {
    zsock_t *s = (zsock_t*)(x->handle);
    zpoller_t *poller = zpoller_new(s);
    if (poller == NULL) {
      cislog_error("zmq_comm_nmsg: Could not create poller");
      return -1;
    }
    zsock_t *p = zpoller_wait(s, 1);
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
  Send a message smaller than PSI_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int zmq_comm_send(const comm_t x, const char *data, const int len) {
  cislog_debug("zmq_comm_send(%s): %d bytes", x.name, len);
  if (comm_base_send(x, data, len) == -1)
    return -1;
  zsock_t *s = (zsock_t*)(x->handle);
  int ret = zstr_send(s, data);
  cislog_debug("zmq_comm_send(%s): returning %d", x.name, ret);
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
int zmq_comm_recv(const comm_t x, char *data, const int len) {
  cislog_debug("zmq_comm_recv(%s)", x.name);
  char *out = zstr_recv(s);
  if (out == NULL) {
    cislog_debug("zmq_comm_recv(%s): did not receive", x.name);
    return -1;
  }
  strcpy(data, out);
  zstr_free(&s);
  return strlen(data);
};


#endif /*CISZMQCOMM_H_*/
