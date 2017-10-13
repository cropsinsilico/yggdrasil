#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMBASE_H_
#define CISCOMMBASE_H_

/*! @brief Communicator types. */
enum comm_type { IPC_COMM, ZMQ_COMM, ASCII_FILE_COMM,
		 ASCII_TABLE_COMM, ASCII_TABLE_ARRAY_COMM };

/*!
  @brief Communication structure.
 */
typedef struct comm_t {
  const comm_type type; //!< Comm type.
  const char *name; //!< Comm name.
  const char *address; //!< Comm address.
  const char *direction; //!< send or recv for direction messages will go.
  int valid; //!< 1 if communicator initialized, 0 otherwise.
  void *handle; //!< Pointer to handle for comm.
  void *info; //!< Pointer to any extra info comm requires.
  seri_t serializer; //!< Serializer for comm messages.
  int nolimit; //!< If 1, all messages are sent nolimit.
} comm_t;

/*!
  @brief Initialize a basic communicator.
  The name is used to locate the comm address stored in the associated
  environment variable.
  @param[in] name Name of environment variable that the queue address is
  stored in.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] seri_info Format for formatting/parsing messages.
  @returns comm_t Comm structure.
 */
static inline
comm_t init_comm_base(const char *name, const char *direction, const void *seri_info) {
  comm_t ret;
  ret.name = name;
  ret.direction = direction;
  if (seri_info == NULL) {
    ret.serializer.type = DIRECT_SERI;
    ret.serializer.info = seri_info;
  } else {
    ret.serializer.type = FORMAT_SERI;
    ret.serializer.info = seri_info;
  }
  ret.info = NULL;
  ret.handle = NULL;
  ret.nolimit = 1;
  ret.address = getenv(name);
  if (ret.address == NULL) {
    cislog_error("init_comm_base: %s not registered as environment variable.\n",
		 name);
    ret.valid = 0;
  } else {
    ret.valid = 1;
  }
  return ret;
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] comm_t Communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_comm_base(comm_t x) {
  return 0;
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
int comm_base_send(const comm_t x, const char *data, const int len) {
  if (len > PSI_MSG_MAX) {
    cislog_error("comm_base_send(%s): message too large for single packet (PSI_MSG_MAX=%d, len=%d)",
		 x.name, PSI_MSG_MAX, len);
    return -1;
  }
  return 0;
};

  
#endif /*CISCOMMBASE_H_*/
