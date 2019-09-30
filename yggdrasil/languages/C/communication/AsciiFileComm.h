/*! @brief Flag for checking if this header has already been included. */
#ifndef YGGASCIIFILECOMM_H_
#define YGGASCIIFILECOMM_H_

#include <../tools.h>
#include <CommBase.h>
#include <../dataio/AsciiFile.h>
#include <../dataio/AsciiTable.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief Number of files creates. */
static unsigned _yggAsciiFilesCreated;

/*!
  @brief Initialize a ASCII file comm.
  @param[in] comm comm_t Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_ascii_file_comm(comm_t *comm) {
  // Don't check base validity since address is name
  comm->is_file = 1;
  comm->type = ASCII_FILE_COMM;
  strcpy(comm->address, comm->name);
  asciiFile_t *handle = (asciiFile_t*)malloc(sizeof(asciiFile_t));
  if (handle == NULL) {
    ygglog_error("init_ascii_file_comm: Failed to malloc asciiFile handle.");
    return -1;
  }
  if (strcmp(comm->direction, "send") == 0)
    handle[0] = asciiFile(comm->address, "w", NULL, NULL);
  else
    handle[0] = asciiFile(comm->address, "r", NULL, NULL);
  comm->handle = (void*)handle;
  int ret = af_open(handle);
  if (ret != 0) {
    ygglog_error("init_ascii_file_comm: Could not open %s", comm->name);
    comm->valid = 0;
  }
  return ret;
};

/*!
  @brief Create a new file comm.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_ascii_file_address(comm_t *comm) {
  sprintf(comm->name, "temp%d", _yggAsciiFilesCreated);
  int ret = init_ascii_file_comm(comm);
  return ret;
};

/*!
  @brief Perform deallocation for ASCII file communicator.
  @param[in] x comm_t* Pointer to ommunicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_ascii_file_comm(comm_t *x) {
  if (x->handle != NULL) {
    asciiFile_t *file = (asciiFile_t*)x->handle;
    af_close(file);
    free(x->handle);
    x->handle = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] x comm_t* Communicator to check.
  @returns int Number of messages.
 */
static inline
int ascii_file_comm_nmsg(const comm_t* x) {
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  x;
#endif
  // TODO: Count lines in file.
  return 0;
};

/*!
  @brief Send a message to the comm.
  Send a message smaller than PSI_MSG_MAX bytes to an output comm. If the
  message is larger, it will not be sent.
  @param[in] x comm_t* structure that comm should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, 1 if send unsuccessful.
 */
static inline
int ascii_file_comm_send(const comm_t* x, const char *data, const size_t len) {
  if (is_eof(data))
    return 0;
  // Prevent C4100 warning on windows by referencing param
#ifdef _WIN32
  len;
#endif
  asciiFile_t *file = (asciiFile_t*)(x->handle);
  return af_writeline_full(file[0], data);
};

/*!
  @brief Receive a message from an input comm.
  Receive a message smaller than PSI_MSG_MAX bytes from an input comm.
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
int ascii_file_comm_recv(const comm_t* x, char **data, size_t len,
			 const int allow_realloc) {
  asciiFile_t *file = (asciiFile_t*)(x->handle);
  if (allow_realloc) {
    return af_readline_full(file[0], data, (size_t*)(&len));
  } else {
    return af_readline_full_norealloc(file[0], data[0], len);
  }
};

/*!
  @brief Send a large message to an output comm.
  Alias for sending short message.
 */
#define ascii_file_comm_send_nolimit ascii_file_comm_send

/*!
  @brief Receive a large message from an input comm.
  Alias for receiving short message.
 */
#define ascii_file_comm_recv_nolimit ascii_file_comm_recv


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGASCIIFILECOMM_H_*/
