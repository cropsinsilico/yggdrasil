/*! @brief Flag for checking if this header has already been included. */
#ifndef YGGCOMMBASE_H_
#define YGGCOMMBASE_H_

#include "../tools.h"
#include "../datatypes/datatypes.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif


/*! @brief Bit flags. */
#define COMM_FLAG_VALID   0x00000001  //!< Set if the comm is initialized
#define COMM_FLAG_GLOBAL  0x00000002  //!< Set if the comm is global
#define COMM_FLAG_FILE    0x00000004  //!< Set if the comm connects to a file
#define COMM_FLAG_WORKER  0x00000008  //!< Set if the comm is a work comm
#define COMM_FLAG_CLIENT  0x00000010  //!< Set if the comm is a client
#define COMM_FLAG_SERVER  0x00000020  //!< Set if the comm is a server
#define COMM_FLAG_CLIENT_RESPONSE 0x00000040 //!< Set if the comm is a client response comm
#define COMM_ALWAYS_SEND_HEADER   0x00000080 //!< Set if the comm should always include a header in messages
#define COMM_ALLOW_MULTIPLE_COMMS 0x00000100 //!< Set if the comm should connect in a way that allow multiple connections

/*! @brief Bit flags that can be set for const comm */
#define COMM_FLAGS_USED   0x00000001  //!< Set if the comm has been used
#define COMM_EOF_SENT     0x00000002  //!< Set if EOF has been sent
#define COMM_EOF_RECV     0x00000004  //!< Set if EOF has been received
  
/*! @brief Set if the comm is the receiving comm for a client/server request connection */
#define COMM_FLAG_RPC     COMM_FLAG_SERVER | COMM_FLAG_CLIENT


/*! @brief Communicator types. */
enum comm_enum { NULL_COMM, IPC_COMM, ZMQ_COMM,
		 SERVER_COMM, CLIENT_COMM,
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
  void *other; //!< Pointer to additional information for the comm.
  char name[COMM_NAME_SIZE]; //!< Comm name.
  char address[COMM_ADDRESS_SIZE]; //!< Comm address.
  char direction[COMM_DIR_SIZE]; //!< send or recv for direction messages will go.
  int flags; //!< Flags describing the status of the comm.
  int *const_flags;  //!< Flags describing the status of the comm that can be est for const.
  void *handle; //!< Pointer to handle for comm.
  void *info; //!< Pointer to any extra info comm requires.
  dtype_t *datatype; //!< Data type for comm messages.
  size_t maxMsgSize; //!< The maximum message size.
  size_t msgBufSize; //!< The size that should be reserved in messages.
  int index_in_register; //!< Index of the comm in the comm register.
  time_t *last_send; //!< Clock output at time of last send.
  void *reply; //!< Reply information.
  int thread_id; //!< ID for the thread that created the comm.
} comm_t;


/*!
  @brief Display the comm in the other field for a comm.
  @param[in] x Comm to display other field of.
 */
static inline
void display_other(comm_t *x) {
  if (x->other != NULL) {
    comm_t* other = (comm_t*)(x->other);
    printf("type(%s) = %d\n", other->name, (int)(other->type));
  }
}


/*!
  @brief Perform deallocation for basic communicator.
  @param[in] x comm_t * Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_comm_base(comm_t *x) {
  ygglog_debug("free_comm_base: Started");
  if (x == NULL)
    return 0;
  if (x->last_send != NULL) {
    free(x->last_send);
    x->last_send = NULL;
  }
  if (x->const_flags != NULL) {
    free(x->const_flags);
    x->const_flags = NULL;
  }
  if (x->datatype != NULL) {
    destroy_dtype(&(x->datatype));
    x->datatype = NULL;
  }
  x->flags = 0;
  x->name[0] = '\0';
  x->index_in_register = -1;
  ygglog_debug("free_comm_base: Finished");
  return 0;
};

/*!
  @brief Initialize an empty comm base without malloc.
  @returns comm_t NULL comm object.
 */
static inline
comm_t empty_comm_base() {
  comm_t ret;
  ret.type = NULL_COMM;
  ret.other = NULL;
  ret.name[0] = '\0';
  ret.address[0] = '\0';
  ret.direction[0] = '\0';
  ret.flags = COMM_ALWAYS_SEND_HEADER;
  ret.handle = NULL;
  ret.info = NULL;
  ret.datatype = NULL;
  ret.maxMsgSize = 0;
  ret.msgBufSize = 0;
  ret.index_in_register = -1;
  ret.last_send = NULL;
  ret.reply = NULL;
  ret.thread_id = 0;
  return ret;
};

/*!
  @brief Initialize a basic communicator with address info.
  @param[in] address char * Address for new comm.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] t comm_type Type of comm that should be created.
  @param[in] datatype dtype_t* Pointer to datatype structure.
  @returns comm_t* Address of comm structure.
*/
static inline
comm_t* new_comm_base(char *address, const char *direction,
		      const comm_type t, dtype_t* datatype) {
  comm_t* ret = (comm_t*)malloc(sizeof(comm_t));
  if (ret == NULL) {
    ygglog_error("new_comm_base: Failed to malloc comm.");
    return ret;
  }
  ret[0] = empty_comm_base();
  ret->type = t;
  ret->flags = ret->flags | COMM_FLAG_VALID;
  if (address != NULL)
    strncpy(ret->address, address, COMM_ADDRESS_SIZE);
  if (direction == NULL) {
    ret->flags = ret->flags & ~COMM_FLAG_VALID;
  } else {
    strncpy(ret->direction, direction, COMM_DIR_SIZE);
  }
  ret->datatype = complete_dtype(datatype, false);
  if (ret->datatype == NULL) {
    ygglog_error("new_comm_base: Could not initialize data type.");
    free_comm_base(ret);
    return NULL;
  }
  ret->maxMsgSize = YGG_MSG_MAX;
  ret->last_send = (time_t*)malloc(sizeof(time_t));
  if (ret->last_send == NULL) {
    ygglog_error("new_comm_base: Error mallocing last_send.");
    free_comm_base(ret);
    return NULL;
  }
  ret->const_flags = (int*)malloc(sizeof(int));
  if (ret->const_flags == NULL) {
    ygglog_error("new_comm_base: Error mallocing const_flags.");
    free_comm_base(ret);
    return NULL;
  }
  ret->last_send[0] = 0;
  ret->const_flags[0] = 0;
  ret->thread_id = get_thread_id();
  char *allow_threading = getenv("YGG_THREADING");
  if (allow_threading != NULL) {
    ret->flags = ret->flags | COMM_ALLOW_MULTIPLE_COMMS;
  }
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
  @param[in] datatype dtype_t* Pointer to data type structure.
  @returns comm_t* Address of comm structure.
 */
static inline
comm_t* init_comm_base(const char *name, const char *direction,
		       const comm_type t, dtype_t* datatype) {
  char full_name[COMM_NAME_SIZE];
  char *model_name = NULL;
  char *address = NULL;
  if (name != NULL) {
    strncpy(full_name, name, COMM_NAME_SIZE);
    if ((direction != NULL) && (strlen(direction) > 0)) {
      if (is_send(direction))
	strcat(full_name, "_OUT");
      else if (is_recv(direction))
	strcat(full_name, "_IN");
    }
    model_name = getenv("YGG_MODEL_NAME");
    address = getenv(full_name);
    if ((address == NULL) && (model_name != NULL)) {
      char prefix[COMM_NAME_SIZE];
      snprintf(prefix, COMM_NAME_SIZE, "%s:", model_name);
      if (strncmp(prefix, full_name, strlen(prefix)) != 0) {
	strcat(prefix, full_name);
	strcpy(full_name, prefix);
	address = getenv(full_name);
      }
    }
    if (address == NULL) {
      char temp_name[COMM_NAME_SIZE] = "";
      size_t i;
      for (i = 0; i < strlen(full_name); i++) {
	if (full_name[i] == ':') {
	  strcat(temp_name, "__COLON__");
	} else {
	  strncat(temp_name, full_name + i, 1);
	}
      }
      address = getenv(temp_name);
    }
    ygglog_debug("init_comm_base: model_name = %s, full_name = %s, address = %s",
		 model_name, full_name, address);
  }
  comm_t *ret = new_comm_base(address, direction, t, datatype);
  if (ret == NULL) {
    ygglog_error("init_comm_base: Error in new_comm_base");
    return ret;
  }
  if (name == NULL) {
    ret->flags = ret->flags & ~COMM_FLAG_VALID;
  } else {
    strncpy(ret->name, full_name, COMM_NAME_SIZE);
  }
  if ((strlen(ret->address) == 0) && (t != SERVER_COMM) && (t != CLIENT_COMM)) {
    ygglog_error("init_comm_base: %s not registered as environment variable.\n",
		 full_name);
    ret->flags = ret->flags & ~COMM_FLAG_VALID;
  }
  ygglog_debug("init_comm_base(%s): Done", ret->name);
  return ret;
};

/*!
  @brief Send a message to the comm.
  Send a message smaller than YGG_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int comm_base_send(const comm_t *x, const char *data, const size_t len) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(data);
#endif
  // Make sure you arn't sending a message that is too big
  if (len > YGG_MSG_MAX) {
    ygglog_error("comm_base_send(%s): message too large for single packet (YGG_MSG_MAX=%d, len=%d)",
		 x->name, YGG_MSG_MAX, len);
    return -1;
  }
  return 0;
};


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif
  
#endif /*YGGCOMMBASE_H_*/
