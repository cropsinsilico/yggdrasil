#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <../tools.h>
#include <CommBase.h>
#include <../dataio/AsciiTable.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISASCIITABLECOMM_H_
#define CISASCIITABLECOMM_H_

/*! @brief Number of tables creates. */
static unsigned _cisAsciiTablesCreated;

/*!
  @brief Initialize a ASCII table comm.
  @param[in] comm comm_t Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_ascii_table_comm(comm_t *comm) {
  // Don't check base validity since address is name
  comm->type = ASCII_TABLE_COMM;
  strcpy(comm->address, comm->name);
  // Initialize table as handle
  char *fmt = (char*)(comm->serializer.info);
  asciiTable_t *handle = (asciiTable_t*)malloc(sizeof(asciiTable_t));
  if (strcmp(comm->direction, "send") == 0)
    handle[0] = asciiTable(comm->address, "w", fmt,
			   NULL, NULL, NULL);
  else
    handle[0] = asciiTable(comm->address, "r", NULL,
			   NULL, NULL, NULL);
  comm->handle = (void*)handle;
  // Open the table
  int flag = at_open(handle);
  if (flag != 0) {
    cislog_error("init_ascii_table_comm: Could not open %s", comm->name);
    comm->valid = 0;
    return -1;;
  }
  // Write format to file if "send"
  if (strcmp(comm->direction, "send") == 0)
    at_writeformat(handle[0]);
  // Set AsciiTable serializer
  comm->serializer.type = ASCII_TABLE_SERI;
  comm->serializer.info = (void*)handle;
  return 0;
};

// TODO: Don't create a new file, just send to original
/*!
  @brief Create a new ASCII table.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_ascii_table_address(comm_t *comm) {
  sprintf(comm->name, "tempASCIITable.%d", _cisAsciiTablesCreated);
  int ret = init_ascii_table_comm(comm);
  _cisAsciiTablesCreated++;
  return ret;
};

/*!
  @brief Initialize a ASCII table comm that will send/recv table as arrays.
  @param[in] comm comm_t Comm structure initialized with init_comm_base.
  @returns int -1 if the comm could not be initialized.
 */
static inline
int init_ascii_table_array_comm(comm_t *comm) {
  int ret = init_ascii_table_comm(comm);
  comm->serializer.type = ASCII_TABLE_ARRAY_SERI;
  return ret;
};

/*!
  @brief Create a new ASCII table that will send/recv table as arrays.
  @param[in] comm comm_t * Comm structure initialized with new_comm_base.
  @returns int -1 if the address could not be created.
*/
static inline
int new_ascii_table_array_address(comm_t *comm) {
  sprintf(comm->name, "tempASCIITableArray.%d", _cisAsciiTablesCreated);
  int ret = init_ascii_table_array_comm(comm);
  _cisAsciiTablesCreated++;
  return ret;
};

/*!
  @brief Perform deallocation for ASCII table communicator.
  @param[in] x comm_t* Pointer to communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_ascii_table_comm(comm_t *x) {
  if (x->handle != NULL) {
    asciiTable_t *table = (asciiTable_t*)x->handle;
    at_close(table);
    at_cleanup(table);
    free(x->handle);
    x->handle = NULL;
  }
  return 0;
};

/*!
  @brief Get number of messages in the comm.
  @param[in] comm_t Communicator to check.
  @returns int Number of messages.
 */
static inline
int ascii_table_comm_nmsg(const comm_t x) {
  // TODO: Count lines in table.
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
int ascii_table_comm_send(const comm_t x, const char *data, const int len) {
  if (is_eof(data))
    return 0;
  asciiTable_t *table = (asciiTable_t*)x.handle;
  return at_writeline_full(table[0], data);
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
int ascii_table_comm_recv(const comm_t x, char *data, const int len) {
  asciiTable_t *table = (asciiTable_t*)x.handle;
  return at_readline_full(table[0], data, len);
};

/*!
  @brief Send a large message to an output comm.
  Alias for sending short message.
 */
#define ascii_table_comm_send_nolimit ascii_table_comm_send

/*!
  @brief Receive a large message from an input comm.
  Alias for receiving short message.
 */
#define ascii_table_comm_recv_nolimit ascii_table_comm_recv


#endif /*CISASCIITABLECOMM_H_*/
