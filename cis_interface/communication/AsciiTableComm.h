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

/*!
  @brief Initialize a ASCII table comm.
  @param[in] name Full path to table that should be read from or written to.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] seri_info Format for formatting/parsing messages.
  @returns comm_t Comm structure.
 */
static inline
comm_t init_ascii_table_comm(const char *name, const char *direction,
			     const void *seri_info) {
  // Don't check base validity since address is name
  comm_t ret = init_base_comm(name, direction, NULL);
  ret.type = ASCII_TABLE_COMM;
  ret.address = name;
  // Initialize table as handle
  char *fmt = (char*)seri_info;
  asciiTable_t *handle = (asciiTable_t*)malloc(sizeof(asciiTable_t));
  if (strcmp(ret.direction, "send") == 0)
    handle[0] = asciiTable(ret.address, "w", fmt,
			   NULL, NULL, NULL);
  else
    handle[0] = asciiTable(ret.address, "r", NULL,
			   NULL, NULL, NULL);
  ret.handle = (void*)handle;
  // Open the table
  int flag = at_open(handle);
  if (flag != 0) {
    cislog_error("init_ascii_table_comm: Could not open %s", name);
    ret.valid = 0;
    return ret;
  }
  // Write format to file if "send"
  if (strcmp(ret.direction, "send") == 0)
    at_writeformat(handle[0]);
  // Set AsciiTable serializer
  ret.serializer.type = ASCII_TABLE_SERI;
  ret.serializer.info = (void*)handle;
  return ret;
};

/*!
  @brief Initialize a ASCII table comm that will send/recv table as arrays.
  @param[in] name Full path to table that should be read from or written to.
  @param[in] direction Direction that messages will go through the comm.
  Values include "recv" and "send".
  @param[in] seri_info Format for formatting/parsing messages.
  @returns comm_t Comm structure.
 */
static inline
comm_t init_ascii_table_array_comm(const char *name, const char *direction,
				   const void *seri_info) {
  comm_t ret = init_ascii_table_comm(name, direction, seri_info);
  ret.serializer.type = ASCII_TABLE_ARRAY_SERI;
  return ret;
};

/*!
  @brief Perform deallocation for ASCII table communicator.
  @param[in] comm_t Communicator to deallocate.
  @returns int 1 if there is and error, 0 otherwise.
*/
static inline
int free_ascii_table_comm(comm_t x) {
  if (ret.handle != NULL) {
    asciiTable_t *table = (asciiTable_t*)x.handle;
    at_close(table);
    at_cleanup(table);
    free(x.handle);
    x.handle = NULL;
  }
  return free_base_comm(x);
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
  asciiTable_t table = (asciiTable_t*)x.handle;
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
  asciiTable_t table = (asciiTable_t*)x.handle;
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
