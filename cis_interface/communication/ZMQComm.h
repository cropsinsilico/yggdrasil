#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <CommBase.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISZMQCOMM_H_
#define CISZMQCOMM_H_

static unsigned _cisSocketsCreated;

/*!
  @brief Create a new socket.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_zmq_address(comm_t *comm) {
  sprintf(comm->name, "temp%d", _cisSocketsCreated);
  int ret = -1;
  // TODO: Actually open comm
  return ret;
};

/*!
  @brief Initialize a ZeroMQ communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_zmq_comm(comm_t *comm) {
  int ret = -1;
  if (comm->valid == 0)
    return -1;
  // TODO: Populate
  return ret;
};

/*!
  @brief Perform deallocation for ZMQ communicator.
  @param[in] x comm_t Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_zmq_comm(comm_t *x) {
  // TODO: Populate
  return 1;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int zmq_comm_nmsg(const comm_t x) {
  // TODO: Populate
  return -1;
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
  // TODO: Populate
  int ret = -1;
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
  // TODO: Populate
  int ret = -1;
  cislog_debug("zmq_comm_recv(%s): returns %d bytes\n", x.name, ret);
  return ret;
};

/*!
  @brief Send a large message to an output comm.
  Send a message larger than PSI_MSG_MAX bytes to an output comm by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  zmq_comm_recv_nolimit for communication to make sense.
  @param[in] x comm_t structure that message should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int zmq_comm_send_nolimit(const comm_t x, const char *data, const int len){
  cislog_debug("zmq_comm_send_nolimit(%s): %d bytes", x.name, len);
  int ret = -1;
  // TODO: Populate
  if (ret == 0)
    cislog_debug("zmq_comm_send_nolimit(%s): %d bytes completed", x.name, len);
  return ret;
};

/*!
  @brief Receive a large message from an input comm.
  Receive a message larger than PSI_MSG_MAX bytes from an input comm by
  receiving it in parts. This expects the first message to be the size of
  the total message.
  @param[in] x comm_t structure that message should be sent to.
  @param[out] data character pointer to pointer for allocated buffer where the
  message should be stored. A pointer to a pointer is used so that the buffer
  may be reallocated as necessary for the incoming message.
  @param[in] len0 int length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int zmq_comm_recv_nolimit(const comm_t x, char **data, const int len0){
  cislog_debug("zmq_comm_recv_nolimit(%s)", x.name);
  // TODO: Populate
  int ret = -1;
  if (ret > 0) {
    cislog_debug("zmq_comm_recv_nolimit(%s): %d bytes completed", x.name, ret);
  }
  return ret;
};


#endif /*CISZMQCOMM_H_*/
