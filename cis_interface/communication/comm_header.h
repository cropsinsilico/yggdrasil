/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMHEADER_H_
#define CISCOMMHEADER_H_

#include <../tools.h>
#include <../dataio/AsciiTable.h>

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

#define CIS_MSG_HEAD "CIS_MSG_HEAD"
#define HEAD_VAL_SEP ":CIS:"
#define HEAD_KEY_SEP ",CIS,"
#define COMMBUFFSIZ 2000


/*! @brief Header information passed by comms for multipart messages. */
typedef struct comm_head_t {
  int multipart; //!< 1 if message is multipart, 0 if it is not.
  size_t bodysiz; //!< Size of body.
  size_t bodybeg; //!< Start of body in header.
  int valid; //!< 1 if the header is valid, 0 otherwise.
  int nargs_populated; //!< Number of arguments populated during deserialization.
  //
  size_t size; //!< Size of incoming message.
  char address[COMMBUFFSIZ]; //!< Address that message will comm in on.
  char id[COMMBUFFSIZ]; //!< Unique ID associated with this message.
  char response_address[COMMBUFFSIZ]; //!< Response address.
  char request_id[COMMBUFFSIZ]; //!< Request id.
  char zmq_reply[COMMBUFFSIZ]; //!< Reply address for ZMQ sockets.
  char zmq_reply_worker[COMMBUFFSIZ]; //!< Reply address for worker socket.
  //
  int serializer_type; //!< Code indicating the type of serializer.
  char format_str[COMMBUFFSIZ]; //!< Format string for serializer.
  char field_names[COMMBUFFSIZ]; //!< String containing field names.
  char field_units[COMMBUFFSIZ]; //!< String containing field units.
  int as_array; //!< 1 if messages will be serialized arrays.
  //
  char type[COMMBUFFSIZ]; //!< Type name
  void *serializer_info; //!< JSON type
} comm_head_t;

/*!
  @brief Initialize a header struct.
  @param[in] size size_t Size of message to be sent.
  @param[in] address char* Address that should be used for remainder of 
  message following this header if it is a multipart message.
  @param[in] id char* Message ID.
  @returns comm_head_t Structure with provided information, char arrays
  correctly initialized to empty strings if NULLs provided.
 */
static inline
comm_head_t init_header(const size_t size, const char *address, const char *id) {
  comm_head_t out;
  // Parameters set during read
  out.multipart = 0;
  out.bodysiz = 0;
  out.bodybeg = 0;
  out.valid = 1;
  out.nargs_populated = 0;
  // Parameters sent in header
  out.size = size;
  if (address == NULL)
    out.address[0] = '\0';
  else
    strcpy(out.address, address);
  if (id == NULL)
    out.id[0] = '\0';
  else
    strcpy(out.id, id);
  out.response_address[0] = '\0';
  out.request_id[0] = '\0';
  out.zmq_reply[0] = '\0';
  out.zmq_reply_worker[0] = '\0';
  /* if (response_address == NULL) */
  /*   out.response_address[0] = '\0'; */
  /* else */
  /*   strcpy(out.response_address, response_address); */
  // Parameters that will be removed
  out.serializer_type = -1;
  out.format_str[0] = '\0';
  out.as_array = 0;
  // Parameters used for type
  out.type[0] = '\0';
  out.serializer_info = NULL;
  return out;
};


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*CISCOMMHEADER_H_*/
