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
  size_t size; //!< Size of incoming message.
  char address[COMMBUFFSIZ]; //!< Address that message will comm in on.
  int multipart; //!< 1 if message is multipart, 0 if it is not.
  size_t bodysiz; //!< Size of body.
  size_t bodybeg; //!< Start of body in header.
  int valid; //!< 1 if the header is valid, 0 otherwise.
  char id[COMMBUFFSIZ]; //!< Unique ID associated with this message.
  char response_address[COMMBUFFSIZ]; //!< Response address.
  char request_id[COMMBUFFSIZ]; //!< Request id.
  int serializer_type; //!< Code indicating the type of serializer.
  char format_str[COMMBUFFSIZ]; //!< Format string for serializer.
  char field_names[COMMBUFFSIZ]; //!< String containing field names.
  char field_units[COMMBUFFSIZ]; //!< String containing field units.
  int as_array; //!< 1 if messages will be serialized arrays.
  char zmq_reply[COMMBUFFSIZ]; //!< Reply address for ZMQ sockets.
  char zmq_reply_worker[COMMBUFFSIZ]; //!< Reply address for worker socket.
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
  out.size = size;
  out.multipart = 0;
  out.bodysiz = 0;
  out.bodybeg = 0;
  out.valid = 1;
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
  out.serializer_type = -1;
  out.format_str[0] = '\0';
  out.as_array = 0;
  out.zmq_reply[0] = '\0';
  out.zmq_reply_worker[0] = '\0';
  /* if (response_address == NULL) */
  /*   out.response_address[0] = '\0'; */
  /* else */
  /*   strcpy(out.response_address, response_address); */
  return out;
};

/*!
  @brief Format single key, value pair into header.
  @param[out] head char * Buffer where key, value pair should be written.
  @param[in] key const char * Key to be written.
  @param[in] value const char * Value to be written.
  @param[in] headsiz size_t Size of head buffer.
  returns: int Number of characters written.
*/
static inline
int format_header_entry(char *head, const char *key, const char *value,
			const size_t headsiz) {
  int ret = snprintf(head, headsiz, "%s%s%s%s",
		     key, HEAD_VAL_SEP, value, HEAD_KEY_SEP);
  if (ret > (int)headsiz) {
    cislog_error("format_header_entry: Formatted header is larger than bufer.\n");
    return -1;
  }
  return ret;
};

/*!
  @brief Extract header value for a given key.
  @param[in] head const char * Header string.
  @param[in] key const char * Key that should be extracted.
  @param[out] value char * buffer where value should be stored.
  @param[in] valsiz size_t Size of value buffer.
  returns: int size of value if it could be found, -1 otherwise.
*/
static inline
int parse_header_entry(const char *head, const char *key, char *value,
		       const size_t valsiz) {
  // Compile
  /*
  if (strlen(HEAD_KEY_SEP) > 1) {
    cislog_error("parse_header_entry: HEAD_KEY_SEP is more than one character. Fix regex.");
    return -1;
    } */
  char regex_text[200];
  regex_text[0] = '\0';
  strcat(regex_text, HEAD_KEY_SEP);
  strcat(regex_text, key);
  strcat(regex_text, HEAD_VAL_SEP);
  strcat(regex_text, "([^(");
  strcat(regex_text, HEAD_KEY_SEP);
  strcat(regex_text, ")]*)");
  strcat(regex_text, HEAD_KEY_SEP);
  // Extract substring
  size_t *sind = NULL;
  size_t *eind = NULL;
  int n_sub_matches = find_matches(regex_text, head, &sind, &eind);
  // Loop until string done
  if (n_sub_matches < 2) {
    cislog_debug("parse_header_entry: Could not find match to %s in %s.",
		 regex_text, head);
    if (sind != NULL) free(sind);
    if (eind != NULL) free(eind);
    return -1;
  }
  // Extract substring
  size_t value_size = eind[1] - sind[1];
  if (value_size > valsiz) {
    cislog_error("parse_header_entry: Value is larger than buffer.\n");
    if (sind != NULL) free(sind);
    if (eind != NULL) free(eind);
    return -1;
  }
  memcpy(value, head + sind[1], value_size);
  value[value_size] = '\0';
  if (sind != NULL) free(sind);
  if (eind != NULL) free(eind);
  return (int)value_size;
};


/*!
  @brief Format header to a string.
  @param[in] head comm_head_t Header to be formatted.
  @param[out] buf char * Buffer where header should be written.
  @param[in] bufsiz size_t Size of buf.
  @returns: int Size of header written.
*/
static inline
int format_comm_header(const comm_head_t head, char *buf, const size_t bufsiz) {
  int ret;
  size_t pos;
  // Header tag
  pos = 0;
  strcpy(buf, CIS_MSG_HEAD);
  pos += strlen(CIS_MSG_HEAD);
  if (pos > bufsiz) {
    cislog_error("First header tag would exceed buffer size\n");
    return -1;
  }
  // Address entry
  if (strlen(head.address) > 0) {
    ret = format_header_entry(buf + pos, "address", head.address, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding address entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // Size entry
  char size_str[100];
  sprintf(size_str, "%d", (int)(head.size));
  ret = format_header_entry(buf + pos, "size", size_str, bufsiz - pos);
  if (ret < 0) {
    cislog_error("Adding size entry would exceed buffer size\n");
    return ret;
  } else {
    pos += ret;
  }
  // ID
  if (strlen(head.id) > 0) {
    ret = format_header_entry(buf + pos, "id", head.id, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding id entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // REQUEST_ID
  if (strlen(head.request_id) > 0) {
    ret = format_header_entry(buf + pos, "request_id",
			      head.request_id, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding request_id entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // RESPONSE_ADDRESS
  if (strlen(head.response_address) > 0) {
    ret = format_header_entry(buf + pos, "response_address",
			      head.response_address, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding response_address entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // Serializer type
  if (head.serializer_type >= 0) {
    char stype_str[100];
    sprintf(stype_str, "%d", head.serializer_type);
    ret = format_header_entry(buf + pos, "stype", stype_str, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding stype entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // Serializer format_str
  if (strlen(head.format_str) > 0) {
    ret = format_header_entry(buf + pos, "format_str",
			      head.format_str, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding format_str entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // Serializer as_array
  if (head.as_array > 0) {
    char as_array_str[100];
    sprintf(as_array_str, "%d", head.as_array);
    ret = format_header_entry(buf + pos, "as_array", as_array_str, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding as_array entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // ZMQ Reply address
  if (strlen(head.zmq_reply) > 0) {
    ret = format_header_entry(buf + pos, "zmq_reply",
			      head.zmq_reply, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding zmq_reply entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // ZMQ Reply address for worker
  if (strlen(head.zmq_reply_worker) > 0) {
    ret = format_header_entry(buf + pos, "zmq_reply_worker",
			      head.zmq_reply_worker, bufsiz - pos);
    if (ret < 0) {
      cislog_error("Adding zmq_reply_worker entry would exceed buffer size\n");
      return ret;
    } else {
      pos += ret;
    }
  }
  // Closing header tag
  pos -= strlen(HEAD_KEY_SEP);
  buf[pos] = '\0';
  pos += strlen(CIS_MSG_HEAD);
  if (pos > bufsiz) {
    cislog_error("Closing header tag would exceed buffer size\n");
    return -1;
  }
  strcat(buf, CIS_MSG_HEAD);
  /* // Body */
  /* if (head.body != NULL) { */
  /*   pos += head.bodysiz; */
  /*   if (pos > bufsiz) { */
  /*     cislog_error("Adding body would exceed buffer size\n"); */
  /*     return -1; */
  /*   } */
  /*   memcpy(buf, head.body, head.bodysiz); */
  /*   buf[pos] = '\0'; */
  /* } */
  return (int)pos;
};

/*!
  @brief Extract header information from a string.
  @param[in] buf const char* Message that header should be extracted from.
  @param[in] bufsiz size_t Size of buf.
  @returns: comm_head_t Header information structure.
 */
static inline
comm_head_t parse_comm_header(const char *buf, const size_t bufsiz) {
  comm_head_t out = init_header(0, NULL, NULL);
  size_t sind, eind;
  int ret;
#ifdef _WIN32
  // Windows regex of newline is buggy
  size_t sind1, eind1, sind2, eind2;
  char re_head_tag[COMMBUFFSIZ];
  sprintf(re_head_tag, "(%s)", CIS_MSG_HEAD);
  ret = find_match(re_head_tag, buf, &sind1, &eind1);
  if (ret > 0) {
    sind = sind1;
    ret = find_match(re_head_tag, buf + eind1, &sind2, &eind2);
    if (ret > 0)
      eind = eind1 + eind2;
  }
#else
  // Extract just header
  char re_head[COMMBUFFSIZ] = CIS_MSG_HEAD;
  strcat(re_head, "(.*)");
  strcat(re_head, CIS_MSG_HEAD);
  // strcat(re_head, ".*");
  ret = find_match(re_head, buf, &sind, &eind);
#endif
  if (ret < 0) {
    cislog_error("parse_comm_header: could not find header in '%.1000s'", buf);
    out.valid = 0;
    return out;
  } else if (ret == 0) {
    cislog_debug("parse_comm_header: No header in '%.1000s...'", buf);
    out.multipart = 0;
    out.size = bufsiz;
  } else {
    out.multipart = 1;
    // Extract just header
    size_t headsiz = (eind-sind);
    out.bodysiz = bufsiz - headsiz;
    out.bodybeg = eind;
    headsiz -= (2*strlen(CIS_MSG_HEAD));
    char *head = (char*)malloc(headsiz + 2*strlen(HEAD_KEY_SEP) + 1);
    strcpy(head, HEAD_KEY_SEP);
    memcpy(head + strlen(HEAD_KEY_SEP), buf + sind + strlen(CIS_MSG_HEAD), headsiz);
    head[headsiz + strlen(HEAD_KEY_SEP)] = '\0';
    strcat(head, HEAD_KEY_SEP);
    // Extract address
    ret = parse_header_entry(head, "address", out.address, COMMBUFFSIZ);
    // Extract size
    char size_str[COMMBUFFSIZ];
    ret = parse_header_entry(head, "size", size_str, COMMBUFFSIZ);
    if (ret < 0) {
      cislog_error("parse_comm_header: could not find size in header");
      out.valid = 0;
      free(head);
      return out;
    }
    out.size = atoi(size_str);
    // Extract id & response address
    ret = parse_header_entry(head, "id", out.id, COMMBUFFSIZ);
    ret = parse_header_entry(head, "response_address", out.response_address, COMMBUFFSIZ);
    ret = parse_header_entry(head, "request_id", out.request_id, COMMBUFFSIZ);
    // Extract serializer type
    char stype_str[COMMBUFFSIZ];
    ret = parse_header_entry(head, "stype", stype_str, COMMBUFFSIZ);
    if (ret >= 0)
      out.serializer_type = atoi(stype_str);
    // Extract as_array serialization parameter
    char array_str[COMMBUFFSIZ];
    ret = parse_header_entry(head, "as_array", array_str, COMMBUFFSIZ);
    if (ret >= 0)
      out.as_array = atoi(array_str);
    // Extract serializer information
    ret = parse_header_entry(head, "format_str", out.format_str, COMMBUFFSIZ);
    ret = parse_header_entry(head, "field_names", out.field_names, COMMBUFFSIZ);
    ret = parse_header_entry(head, "field_units", out.field_units, COMMBUFFSIZ);
    // ZMQ reply addresses
    ret = parse_header_entry(head, "zmq_reply", out.zmq_reply, COMMBUFFSIZ);
    ret = parse_header_entry(head, "zmq_reply_worker", out.zmq_reply_worker, COMMBUFFSIZ);
    // Free header
    free(head);
  }
  return out;
};

#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*CISCOMMHEADER_H_*/
