/*! @brief Flag for checking if this header has already been included. */
#ifndef YGGMPICOMM_H_
#define YGGMPICOMM_H_

#ifdef MPIINSTALLED
#include <mpi.h>
#endif /*MPIINSTALLED*/
#include <CommBase.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

#if defined(MPIINSTALLED) && defined(MPI_COMM_WORLD)

typedef struct mpi_registry_t {
  MPI_Comm comm; //!< MPI communicator.
  size_t nproc; //!< Number of processes in procs.
  size_t* procs; //!< IDs for partner processes.
  size_t tag; //!< Tag for next message.
} mpi_registry_t;


/*!
  @brief Initialize an MPI communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_mpi_comm(comm_t *comm) {
  if (!(comm->flags & COMM_FLAG_VALID))
    return -1;
  if (strlen(comm->name) == 0) {
    sprintf(comm->name, "tempinitMPI.%s", comm->address);
  }
  mpi_registry_t* reg = (mpi_registry_t*)malloc(sizeof(mpi_registry_t));
  if (reg == NULL) {
    ygglog_error("init_mpi_comm: Could not alloc MPI registry.");
    return -1;
  }
  reg->comm = MPI_COMM_WORLD;
  reg->nproc = 0;
  reg->procs = NULL;
  reg->tag = 0;
  reg->nproc = 1;
  for (size_t i = 0; i < strlen(comm->address); i++) {
    if (comm->address[i] == ',') reg->nproc++;
  }
  reg->procs = (size_t*)malloc(reg->nproc * sizeof(size_t));
  if (reg->procs == NULL) {
    ygglog_error("init_mpi_comm: Could not alloc MPI registry procs.");
    free(reg);
    return -1;
  }
  for (size_t i = 0; i < reg->nprocs; i++)
    reg->procs[i] = 0;
  size_t ibeg = 0, iend = 0;
  char iaddress[5] = "";
  while (iend <= strlen(comm->address)) {
    if ((iend == strlen(comm->address))
	|| (comm->address[iend] == ',')
	|| (comm->address[iend] == ']')) {
      strncpy(iaddress, comm->address + ibeg, iend - ibeg);
      iaddress[iend - ibeg] = '\0';
      reg->procs[i] = atoi(iaddress);
      if (comm->address[iend] == ']')
	iend++;
      else if (comm->address[iend] == ',')
	ibeg = iend + 1;
    } else if (comm->address[iend] == '[') ibeg++;
    iend++;
  }
  comm->handle = (void*)reg;
  return 0;
};

/*!
  @brief Perform deallocation for MPI communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is an error, 0 otherwise.
*/
static inline
int free_mpi_comm(comm_t *x) {
  if (x->handle != NULL) {
    reg = (mpi_registry_t*)(x->handle);
    if (reg->procs != NULL) free(reg->procs);
    free(x->handle);
    x->handle = NULL;
  }
  return 0;
};

/*!
  @brief Get the ID for the source process of the next incoming message.
  @param[in] comm_t* Communicator to check.
  @returns int ID of source comm, 0 if no messages, -1 for an error.
*/
static inline
int mpi_comm_source_id(const comm_t *x) {
  if (is_send(x->direction)) return 0;
  if (x->handle == NULL) {
    ygglog_error("mpi_comm_source_id(%s): Queue handle is NULL.", x->name);
    return -1;
  }
  mpi_registry_t* reg = (mpi_registry_t*)(x->handle);
  MPI_Status status;
  int address = MPI_ANY_SOURCE;
  if (MPI_Probe(address, reg->tag, reg->comm, &status) != MPI_SUCCESS) {
    ygglog_error("mpi_comm_source_id(%s): Error in probe for tag = %d",
		 x->name, reg->tag);
    return -1;
  }
  if (status.MPI_ERROR) {
    ygglog_error("mpi_comm_source_id(%s): Error in status for tag = %d: %d",
		 x->name, reg->tag, status.MPI_ERROR);
    return -1;
  }
  if (status.cancelled) {
    ygglog_error("mpi_comm_source_id(%s): Request canceled for tag = %d",
		 x->name, reg->tag);
    return -1;
  }
  if (status.count > 0) {
    for (size_t i = 0; i < reg->nproc; i++) {
      if (reg->procs[i] == status.MPI_SOURCE) {
	return status.MPI_SOURCE;
      }
    }
  }
  return 0;
};
  
  
/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t* Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int mpi_comm_nmsg(const comm_t *x) {
  int src = mpi_comm_source_id(x);
  int nmsg = 0;
  if (src < 0) {
    ygglog_error("mpi_comm_nmsg(%s): Error checking messages.", x->name);
    return -1;
  } else if (src > 0) {
    nmsg = 1;
  }
  return nmsg;
};

/*!
  @brief Send a message to the comm.
  Send a message smaller than YGG_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t* structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int mpi_comm_send(const comm_t *x, const char *data, const size_t len) {
  int ret = -1;
  ygglog_debug("mpi_comm_send(%s): %d bytes", x->name, len);
  if (comm_base_send(x, data, len) == -1)
    return -1;
  if (x->handle == NULL) {
    ygglog_error("mpi_comm_send(%s): Queue handle is NULL.", x->name);
    return -1;
  }
  mpi_registry_t* reg = (mpi_registry_t*)(x->handle);
  int len_int = (int)(len);
  int address = reg->procs[tag % reg->nproc];
  if (MPI_Send(&len_int, 1, MPI_INT, address, reg->tag, reg->comm)) {
    ygglog_error("mpi_comm_send(%s): Error sending message size for tag = %d.",
		 x->name, reg->tag);
    return -1;
  }
  if (MPI_Send(data, len_int, MPI_CHAR, address, reg->tag, reg->comm)) {
    ygglog_error("mpi_comm_send(%s): Error sending message for tag = %d.",
		 x->name, reg->tag);
    return -1;
  }
  ygglog_debug("mpi_comm_send(%s): returning %d", x->name, ret);
  reg->tag++;
  return ret;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than YGG_MSG_MAX bytes from an input comm.
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
int mpi_comm_recv(const comm_t *x, char **data, const size_t len,
		  const int allow_realloc) {
  ygglog_debug("mpi_comm_recv(%s)", x->name);
  if (MPI_Probe(address, reg->tag, reg->comm, &status) != MPI_SUCCESS) {
    ygglog_error("mpi_comm_nmsg(%s): Error in probe for tag = %d",
		 x->name, reg->tag);
    return -1;
  }
  int address = mpi_comm_source_id(x);
  int len_recv = 0;
  if (MPI_Recv(&len_recv, 1, MPI_INT, address, reg->tag, reg->comm, MPI_STATUS_IGNORE)) {
    // TODO: Check status?
    ygglog_error("mpi_comm_recv(%s): Error receiving message size for tag = %d.",
		 x->name, reg->tag);
    return -1;
  }
  if (len_recv > len) {
    if (allow_realloc) {
      ygglog_debug("mpi_comm_recv(%s): reallocating buffer from %d to %d bytes.",
		   x->name, len, len_recv);
      (*data) = (char*)realloc(*data, len_recv);
      if (*data == NULL) {
	ygglog_error("mpi_comm_recv(%s): failed to realloc buffer.", x->name);
	return -1;
      }
    } else {
      ygglog_error("mpi_comm_recv(%s): buffer (%d bytes) is not large enough for message (%d bytes)",
		   x->name, len, len_recv);
      return -len_recv;
    }
  }
  if (MPI_Recv(*data, len_recv, MPI_CHAR, address, reg->tag, reg->comm, MPI_STATUS_IGNORE)) {
    // TODO: Check status?
    ygglog_error("mpi_comm_recv(%s): Error receiving message for tag = %d.",
		 x->name, reg->tag);
    return -1;
  }
  ygglog_debug("mpi_comm_recv(%s): returns %d bytes", x->name, len_recv);
  reg->tag++;
  return len_recv;
};

// Definitions in the case where MPI libraries not installed
#else /*MPIINSTALLED*/

/*!
  @brief Print error message about MPI library not being installed.
 */
static inline
void mpi_install_error() {
  ygglog_error("Compiler flag 'MPIINSTALLED' not defined so MPI bindings are disabled.");
};

/*!
  @brief Perform deallocation for basic communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is an error, 0 otherwise.
*/
static inline
int free_mpi_comm(comm_t *x) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(x);
#endif
  mpi_install_error();
  return 1;
};

/*!
  @brief Create a new channel.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_mpi_address(comm_t *comm) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(comm);
#endif
  mpi_install_error();
  return -1;
};

/*!
  @brief Initialize a sysv_mpi communicator.
  @param[in] comm comm_t * Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_mpi_comm(comm_t *comm) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(comm);
#endif
  mpi_install_error();
  return -1;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t Communicator to check.
  @returns int Number of messages. -1 indicates an error.
 */
static inline
int mpi_comm_nmsg(const comm_t *x) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(x);
#endif
  mpi_install_error();
  return -1;
};

/*!
  @brief Send a message to the comm.
  Send a message smaller than YGG_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t* structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int mpi_comm_send(const comm_t *x, const char *data, const size_t len) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(x);
  UNUSED(data);
  UNUSED(len);
#endif
  mpi_install_error();
  return -1;
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than YGG_MSG_MAX bytes from an input comm.
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
int mpi_comm_recv(const comm_t *x, char **data, const size_t len,
		  const int allow_realloc) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  UNUSED(x);
  UNUSED(data);
  UNUSED(len);
  UNUSED(allow_realloc);
#endif
  mpi_install_error();
  return -1;
};

#endif /*MPIINSTALLED*/

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGMPICOMM_H_*/
