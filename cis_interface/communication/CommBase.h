#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <../tools.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMBASE_H_
#define CISCOMMBASE_H_

/*! @brief Communicator types. */
enum comm_enum { IPC_COMM, ZMQ_COMM, RPC_COMM, SERVER_COMM, CLIENT_COMM,
		 ASCII_FILE_COMM, ASCII_TABLE_COMM, ASCII_TABLE_ARRAY_COMM };
typedef enum comm_enum comm_type;
#define COMM_NAME_SIZE 100
#define COMM_ADDRESS_SIZE 500
#define COMM_DIR_SIZE 100


/*!
  @brief Communication structure.
 */
typedef struct comm_t {
  comm_type type; //!< Comm type.
  char name[COMM_NAME_SIZE]; //!< Comm name.
  char address[COMM_ADDRESS_SIZE]; //!< Comm address.
  char direction[COMM_DIR_SIZE]; //!< send or recv for direction messages will go.
  char suffix[COMM_DIR_SIZE]; //!< Suffix to be added to the name.
  int valid; //!< 1 if communicator initialized, 0 otherwise.
  void *handle; //!< Pointer to handle for comm.
  void *info; //!< Pointer to any extra info comm requires.
  seri_t serializer; //!< Serializer for comm messages.
  int maxMsgSize; //!< The maximum message size.
  int always_send_header; //!< 1 if comm should always send a header.
} comm_t;

/*!
  @brief Initialize a basic communicator with address info.
  @param[in] address char * Address for new comm.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] t comm_type Type of comm that should be created.
  @param[in] seri_info Pointer to info for the serializer (e.g. format string).
  @returns comm_t Comm structure.
*/
static inline
comm_t new_comm_base(char *address, const char *direction, const comm_type t,
		     void *seri_info) {
  comm_t ret;
  ret.type = t;
  ret.valid = 1;
  ret.name[0] = '\0';
  if (address == NULL)
    ret.address[0] = '\0';
  else
    strcpy(ret.address, address);
  if (direction == NULL) {
    ret.direction[0] = '\0';
    ret.valid = 0;
    ret.suffix[0] = '\0';
  } else {
    strcpy(ret.direction, direction);
    if (strcmp(direction, "send") == 0)
      strcpy(ret.suffix, "_OUT");
    else
      strcpy(ret.suffix, "_IN");
  }
  ret.handle = NULL;
  ret.info = NULL;
  if (seri_info == NULL) {
    ret.serializer.type = DIRECT_SERI;
    ret.serializer.info = seri_info;
  } else {
    ret.serializer.type = FORMAT_SERI;
    ret.serializer.info = seri_info;
  }
  ret.maxMsgSize = CIS_MSG_MAX;
  ret.always_send_header = 0;
  return ret;
};

/*!
  @brief Initialize a basic communicator.
  The name is used to locate the comm address stored in the associated
  environment variable.
  @param[in] name Name of environment variable that the queue address is
  stored in.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] t comm_type Type of comm that should be created.
  @param[in] seri_info Format for formatting/parsing messages.
  @returns comm_t Comm structure.
 */
static inline
comm_t init_comm_base(const char *name, const char *direction,
		      const comm_type t, void *seri_info) {
  char full_name[COMM_NAME_SIZE];
  char *address = NULL;
  if (name != NULL) {
    strcpy(full_name, name);
    if (strcmp(direction, "send") == 0)
      strcat(full_name, "_OUT");
    else
      strcat(full_name, "_IN");
    address = getenv(full_name);
  }
  comm_t ret = new_comm_base(address, direction, t, seri_info);
  if (name == NULL) {
    ret.name[0] = '\0';
    ret.valid = 0;
  } else
    strcpy(ret.name, full_name);
  if (strlen(ret.address) == 0) {
    cislog_error("init_comm_base: %s not registered as environment variable.\n",
		 full_name);
    ret.valid = 0;
  }
  return ret;
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] x comm_t * Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_comm_base(comm_t *x) {
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
