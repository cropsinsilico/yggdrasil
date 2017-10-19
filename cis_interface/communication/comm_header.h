#include <../dataio/AsciiTable.h>

/*! @brief Flag for checking if this header has already been included. */
#ifndef CISCOMMHEADER_H_
#define CISCOMMHEADER_H_

#define CIS_MSG_HEAD "CIS_MSG_HEAD"
#define HEAD_VAL_SEP ":CIS:"
#define HEAD_KEY_SEP ","
#define BUFSIZ 2000


/*! @brief Header information passed by comms for multipart messages. */
typedef struct comm_head_t {
  int size; //!< Size of incoming message.
  char address[BUFSIZ]; //!< Address that message will comm in on.
  int multipart; //!< 1 if message is multipart, 0 if it is not.
  int bodysiz; //!< Size of body.
  char *body; //!< Remaining message body following header.
  int valid; //!< 1 if the header is valid, 0 otherwise.
} comm_head_t;

/*!
  @brief Format single key, value pair into header.
  @param[out] head char * Buffer where key, value pair should be written.
  @param[in] key const char * Key to be written.
  @param[in] value const char * Value to be written.
  @param[in] headsiz int Size of head buffer.
  returns: int Number of characters written.
*/
static inline
int format_header_entry(char *head, const char *key, const char *value,
			const int headsiz) {
  int ret = snprintf(head, headsiz, "%s%s%s%s",
		     key, HEAD_VAL_SEP, value, HEAD_KEY_SEP);
  if (ret > headsiz) {
    psilog_error("format_header_entry: Formatted header is larger than bufer.\n");
    return -1;
  }
  return ret;
};

/*!
  @brief Extract header value for a given key.
  @param[in] head const char * Header string.
  @param[in] key const char * Key that should be extracted.
  @param[out] value char * buffer where value should be stored.
  @param[in] valsiz int Size of value buffer.
  returns: int size of value if it could be found, -1 otherwise.
*/
static inline
int parse_header_entry(const char *head, const char *key, char *value,
		       const int valsiz) {
  int ret;
  int n_match = 0;
  regex_t r;
  // Compile
  char regex_text[200] = '\0';
  strcat(regex_text, key);
  strcat(regex_text, HEAD_VAL_SEP);
  strcat(regex_text, "(.*)");
  strcat(regex_text, HEAD_KEY_SEP);
  ret = compile_regex(&r, regex_text);
  if (ret)
    return -1;
  // Loop until string done
  const int n_sub_matches = 10;
  regmatch_t m[n_sub_matches];
  int nomatch = regexec(&r, head, n_sub_matches, m, 0);
  if (nomatch)
    return -1;
  // Extract substring
  int value_size = m[1].rm_eo - m[1].rm_so;
  if (value_size > valsiz) {
    cislog_error("parse_header_entry: Value is larger than buffer.\n");
    return -1;
  }
  memcpy(value, head + m[1].rm_so, value_size);
  value[value_size] = '\0';
  return value_size;
};


/*!
  @brief Format header to a string.
  @param[in] head comm_head_t Header to be formatted.
  @param[out] buf char * Buffer where header should be written.
  @param[in] bufsiz int Size of buf.
  @returns: int Size of header written.
*/
static inline
int format_comm_header(const comm_head_t head, char *buf, const int bufsiz) {
  int ret, pos;
  pos += strlen(CIS_MSG_HEAD);
  if (pos > bufsiz) {
    cislog_error("First header tag would exceed buffer size\n");
    return -1;
  }
  // Header tag
  strcpy(buf, CIS_MSG_HEAD);
  // Address entry
  ret = format_header_entry(head + pos, "address", out.address, bufsiz - pos);
  if (ret < 0) {
    cislog_error("Adding address entry would exceed buffer size\n");
    return ret;
  } else {
    pos += ret;
  }
  // Size entry
  char size_str[100];
  sprintf(size_str, "%d", out.size);
  ret = format_header_entry(head + pos, "size", size_str, bufsiz - pos);
  if (ret < 0) {
    cislog_error("Adding size entry would exceed buffer size\n");
    return ret;
  } else {
    pos += ret;
  }
  // Closing header tag
  buf[pos - strlen(HEAD_KEY_SEP)] = '\0'
  strcat(buf, CIS_MSG_HEAD);
  // Body
  if (out.body != NULL) {
    pos += out.bodysiz;
    if (pos > bufsiz) {
      cislog_error("Adding body would exceed buffer size\n");
      return -1;
    }
    memcpy(buf, out.body, out.bodysiz);
    buf[pos] = '\0';
  }
  return pos;
};

/*!
  @brief Extract header information from a string.
  @param[in] buf const char* Message that header should be extracted from.
  @param[in] bufsiz int Size of buf.
  @returns: comm_head_t Header information structure.
 */
static inline
comm_head_t parse_comm_header(const char *buf, const int bufsiz) {
  comm_head_t out;
  out.size = 0;
  out.address = '\0'
  out.multipart = 0;
  out.bodysiz = 0;
  out.body = NULL;
  out.valid = 1;
  // Extract just header
  char re_head[BUFSIZ] = CIS_MSG_HEAD;
  strcat(re_head, "(.*)");
  strcat(re_head, CIS_MSG_HEAD);
  strcat(re_head, "(.*)");
  int sind, eind;
  int ret = find_match(re_head, buf, &sind, &eind);
  if (ret < 0) {
    out.valid = 0;
    return out;
  } else if (ret == 0) {
    out.multipart = 0;
    out.size = bufsiz;
    out.body = (char*)malloc(bufsiz);
    memcpy(out.body, buf, bufsiz);
  } else {
    out.multipart = 1;
    // Extract just header
    int sind, eind;
    int ret = find_match(re_head, buf, &sind, &eind);
    int headsiz = (eind-sind);
    char *head = (char*)malloc(headsiz + strlen(HEAD_KEY_SEP));
    out.bodysiz = bufsiz - headsiz;
    out.body = (char*)malloc(out.bodysiz);
    memcpy(head, buf + sind, headsiz);
    head[headsiz] = '\0';
    memcpy(out.body, buf + eind, out.bodysiz);
    out.body[out.bodysiz] = '\0';
    strcat(out.body, HEAD_KEY_SEP);
    // Extract address
    ret = parse_header_entry(head, "address", out.address, BUFSIZ);
    if (ret < 0) {
      out.valid = 0;
      return out;
    }
    // Extract size
    char size_str[BUFSIZ];
    ret = parse_header_entry(head, "size", size_str, BUFSIZ);
    if (ret < 0) {
      out.valid = 0;
      return out;
    }
    out.size = atoi(size_str);
  }
  return out;
};



#endif CISCOMMHEADER_H_
