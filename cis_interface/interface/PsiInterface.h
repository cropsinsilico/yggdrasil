#include <fcntl.h>           /* For O_* constants */
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/types.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
#include <regex.h>
#include <../dataio/AsciiFile.h>
#include <../dataio/AsciiTable.h>

/*! @brief Flag for checking if PsiInterface.h has already been included.*/
#ifndef PSIINTERFACE_H_
#define PSIINTERFACE_H_

/*! @brief Maximum message size. */
#define PSI_MSG_MAX LINE_SIZE_MAX
/*! @brief End of file message. */
#define PSI_MSG_EOF "EOF!!!"
/*! @brief Maximum number of channels. */
#define _psiTrackChannels 256
/*! @brief Names of channels in use. */
static char * _psiChannelNames[_psiTrackChannels];
/*! @brief Number of channels in use. */
static unsigned _psiChannelsUsed = 0;


//==============================================================================
/*!
  Logging

  Alliases are set at compile-time based on the value of PSI_CLIENT_DEBUG. If 
  set to INFO, only messages logged with info or error alias are printed. If
  set to DEBUG, messages logged with error, info or debug aliases are printed.
  Otherwise, only error messages are printed. If the PSI_CLIENT_DEBUG is
  changed, any code including this header must be recompiled for the change to
  take effect.

*/
//==============================================================================

/*!
  @brief Print a log message.
  Prints a formatted message, prepending it with the process id and appending
  it with a newline.
  @param[in] prefix a constant character pointer to the prefix that should
  preceed the message and process id.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ap va_list of arguments to be formatted in the format string.
 */
static inline
void psiLog(const char* prefix, const char* fmt, va_list ap) {
  fprintf(stdout, "%s: %d: ", prefix, getpid());
  vfprintf(stdout, fmt, ap);
  fprintf(stdout, "\n");
};

/*!
  @brief Print an info log message.
  Prints a formatted message, prepending it with INFO and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void psiInfo(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  psiLog("INFO", fmt, ap);
  va_end(ap);
};
  
/*!
  @brief Print an debug log message.
  Prints a formatted message, prepending it with DEBUG and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void psiDebug(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  psiLog("DEBUG", fmt, ap);
  va_end(ap);
};
  
/*!
  @brief Print an error log message.
  Prints a formatted message, prepending it with ERROR and the process id. A
  newline character is added to the end of the message.
  @param[in] fmt a constant character pointer to a format string.
  @param[in] ... arguments to be formatted in the format string.
 */
static inline
void psiError(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  psiLog("ERROR", fmt, ap);
  va_end(ap);
};
  
#define psilog_error psiError
#ifdef PSI_DEBUG
  #if PSI_DEBUG == INFO
    #define info psiInfo
    #define debug while (0) psiDebug
  #elif PSI_DEBUG == DEBUG
    #define debug psiInfo
    #define info psiDebug
  #else
    #define debug while (0) psiDebug
    #define info while (0) psiInfo
  #endif
#else
  #define debug while (0) psiDebug
  #define info while (0) psiInfo
#endif

//==============================================================================
/*!
  Basic IO 

  Output Usage:
      1. One-time: Create output channel (store in named variables)
            psiOutput_t output_channel = psiOutput("out_name");
      2. Prepare: Format data to a character array buffer.
            char buffer[PSI_MSG_MAX]; 
	    sprintf(buffer, "a=%d, b=%d", 1, 2);
      3. Send:
	    ret = psi_send(output_channel, buffer, strlen(buffer));

  Input Usage:
      1. One-time: Create output channel (store in named variables)
            psiInput_t input_channel = psiInput("in_name");
      2. Prepare: Allocate a character array buffer.
            char buffer[PSI_MSG_MAX];
      3. Receive:
            int ret = psi_recv(input_channel, buffer, PSI_MSG_MAX);
*/
//==============================================================================

/*!
  @brief Get a sysv_ipc queue identifier based on its name.
  The queue name is used to locate the queue key stored in the associated
  environment variable. That key is then used to get the queue ID.
  @param[in] name character pointer to name of environment variable that the
  queue key should be shored in.
  @param[in] yamlName constant character pointer to the original name of the
  queue, absent any suffix. This is used to check if there is an existing
  queue with that name, but a different suffix.
  @returns int queue identifier.
 */
static inline
int psi_mq(const char *name, const char *yamlName){
  // Look up registered name
  char *qid = getenv(name);
  // Fail if the driver did not declare the channel
  if (qid == NULL) {
    psilog_error("psi_mq: Channel %s not registered, model/YAML mismatch (yaml=%s)\n",
		 name, yamlName);
    // Check if opposite channel exists
    char nm_opp[512];
    strcpy(nm_opp, yamlName);
    if (strcmp(name+strlen(yamlName), "_IN") == 0)
      strcat(nm_opp, "_OUT");
    else
      strcat(nm_opp, "_IN");
    qid = getenv(nm_opp);
    if (qid != NULL) {
      psilog_error("psi_mq: Directed channel %s exists, but requested channel %s does not\n",
		   nm_opp, name);
    }
    return -1;
  }
  // Fail if trying to re-use the same channel twice
  unsigned i;
  for (i =0; i < _psiChannelsUsed; i++ ){
    if (0 == strcmp(_psiChannelNames[i], name)){
      psilog_error("Attempt to re-use channel %s", name);
      return -1;
    }
  }
  // Fail if > _psiTrackChannels channels used
  if (_psiChannelsUsed >= _psiTrackChannels) {
    psilog_error("Too many channels in use, max: %d\n", _psiTrackChannels);
    return -1;
  }
  _psiChannelNames[_psiChannelsUsed++] = qid;
  int qkey = atoi(qid);
  int fid = msgget(qkey, 0600);
  return fid;
};

/*!
  @brief Check if a character array matches the internal EOF message.
  @param[in] buf constant character pointer to string that should be checked.
  @returns int 1 if buf is the EOF message, 0 otherwise.
 */
static inline
int is_eof(const char *buf) {
  if (strcmp(buf, PSI_MSG_EOF) == 0)
    return 1;
  else
    return 0;
};

/*!
  @brief Message buffer structure.
*/
typedef struct msgbuf_t {
  long mtype; //!< Message buffer type
  char data[PSI_MSG_MAX]; //!< Buffer for the message
} msgbuf_t;

/*!
  @brief Input queue structure.
  Contains information on an input queue.
 */
typedef struct psiInput_t {
  int _handle; //!< Queue handle.
  const char *_name; //!< Queue name.
  char _fmt[PSI_MSG_MAX]; //!< Format for interpreting queue messages.
  int _nfmt; //!< Number of fields expected from format string
} psiInput_t;

/*!
  @brief Output queue structure.
  Contains information on an output queue.
 */
typedef struct psiOutput_t {
  int _handle; //!< Queue handle. 
  const char *_name; //!< Queue name.
  char _fmt[PSI_MSG_MAX]; //!< Format for formatting queue messages.
  int _nfmt; //!< Number of fields expected from format string
} psiOutput_t;

/*!
  @brief Constructor for psiOutput_t structure.
  Create a psiOutput_t structure based on a provided name that is used to
  locate a particular sysv_ipc queue key stored in the environment variable
  name + "_OUT".
  @param[in] name constant character pointer to name of queue.
  @returns psiOutput_t output queue structure.
 */
static inline
psiOutput_t psiOutput(const char *name){
  char nm[512];
  strcpy(nm, name);
  strcat(nm, "_OUT");
  psiOutput_t ret;
  ret._name = name;
  strcpy(ret._fmt, "\0");
  ret._nfmt = 0;
  ret._handle = psi_mq(nm, name);
  return ret;
};

/*!
  @brief Constructor for psiInput_t structure.
  Create a psiInput_t structure based on a provided name that is used to
  locate a particular sysv_ipc queue key stored in the environment variable
  name + "_IN".
  @param[in] name constant character pointer to name of queue.
  @returns psiInput_t input queue structure.
 */
static inline
psiInput_t psiInput(const char *name){
  char nm[512];
  strcpy(nm, name);
  strcat(nm, "_IN");
  psiInput_t ret;
  ret._handle =  psi_mq(nm, name);
  ret._name = name;
  strcpy(ret._fmt, "\0");
  ret._nfmt = 0;
  return ret;
};

/*! @brief Alias for psiOutput */
static inline
psiOutput_t psi_output(const char *name){
  return psiOutput(name);
};

/*! @brief Alias for psiInput */
static inline
psiInput_t psi_input(const char *name){
  return psiInput(name);
};

/*!
  @brief Constructor for psiOutput_t structure with format.
  Create a psiOutput_t structure based on a provided name that is used to
  locate a particular sysv_ipc queue key stored in the environment variable
  name + "_OUT" and a format string that can be used to format arguments into
  outgoing messages for the queue.
  @param[in] name constant character pointer to name of queue.
  @param[in] fmtString character pointer to format string.
  @returns psiOutput_t output queue structure.
 */
static inline
psiOutput_t psiOutputFmt(const char *name, const char *fmtString){
  psiOutput_t ret = psiOutput(name);
  strcpy(ret._fmt, fmtString);
  ret._nfmt = count_formats(fmtString);
  return ret;
};

/*!
  @brief Constructor for psiInput_t structure with format.
  Create a psiInput_t structure based on a provided name that is used to
  locate a particular sysv_ipc queue key stored in the environment variable
  name + "_IN" and a format stirng that can be used to extract arguments from
  messages received from the queue.
  @param[in] name constant character pointer to name of queue.
  @param[in] fmtString character pointer to format string.
  @returns psiInput_t input queue structure.
 */
static inline
psiInput_t psiInputFmt(const char *name, const char *fmtString){
  psiInput_t ret = psiInput(name);
  strcpy(ret._fmt, fmtString);
  ret._nfmt = count_formats(fmtString);
  return ret;
};

/*!
  @brief Get the number of messages in an output queue.
  Check how many messages are waiting in the associated queue for an output
  queue structure.
  @param[in] psiQ psiOutput_t output queue structure.
  @returns int number of messages in the queue. -1 if the queue cannot be
  accessed.
*/
static inline
int psi_output_nmsg(const psiOutput_t psiQ) {
  int rc;
  struct msqid_ds buf;
  int num_messages;
  rc = msgctl(psiQ._handle, IPC_STAT, &buf);
  if (rc != 0) {
    psilog_error("psi_output_nmsg: Could not access queue.");
    return -1;
  }
  num_messages = buf.msg_qnum;
  return num_messages;
};

/*!
  @brief Get the number of messages in an input queue.
  Check how many messages are waiting in the associated queue for an input
  queue structure.
  @param[in] psiQ psiInput_t input queue structure.
  @returns int number of messages in the queue. -1 if the queue cannot be
  accessed.
*/
static inline
int psi_input_nmsg(const psiInput_t psiQ) {
  int rc;
  struct msqid_ds buf;
  int num_messages;
  rc = msgctl(psiQ._handle, IPC_STAT, &buf);
  if (rc != 0) {
    psilog_error("psi_input_nmsg: Could not access queue.");
    return -1;
  }
  num_messages = buf.msg_qnum;
  return num_messages;
};

/*!
  @brief Send a message to an output queue.
  Send a message smaller than PSI_MSG_MAX bytes to an output queue. If the
  message is larger, it will not be sent.
  @param[in] psiQ psiOutput_t structure that queue should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int psi_send(const psiOutput_t psiQ, const char *data, const int len){
  debug("psi_send(%s): %d bytes", psiQ._name, len);
  if (len > PSI_MSG_MAX) {
    psilog_error("psi_send(%s): message too large for single packet (PSI_MSG_MAX=%d, len=%d)",
		 psiQ._name, PSI_MSG_MAX, len);
    return -1;
  }
  msgbuf_t t;
  t.mtype = 1;
  memcpy(t.data, data, len);
  int ret = -1;
  while (1) {
    ret = msgsnd(psiQ._handle, &t, len, IPC_NOWAIT);
    debug("psi_send(%s): msgsnd returned %d", psiQ._name, ret);
    if (ret == 0) break;
    if (ret == EAGAIN) {
      debug("psi_send(%s): msgsnd, sleep", psiQ._name);
      usleep(250*1000);
    } else {
      psilog_error("psi_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s",
		   psiQ._handle, &t, len, ret, errno, strerror(errno));
      ret = -1;
      break;
    }
  }
  debug("psi_send(%s): returning %d", psiQ._name, ret);   
  return ret;
};

/*!
  @brief Receive a message from an input queue.
  Receive a message smaller than PSI_MSG_MAX bytes from an input queue.
  @param[in] psiQ psiOutput_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int psi_recv(const psiInput_t psiQ, char *data, const int len){
  debug("psi_recv(%s)", psiQ._name);
  msgbuf_t t;
  t.mtype=1;
  int ret = -1;
  while (1) {
    ret = msgrcv(psiQ._handle, &t, len, 0, IPC_NOWAIT);
    if (ret == -1 && errno == ENOMSG) {
      debug("psi_recv(%s): no input, sleep", psiQ._name);
      usleep(250*1000);
    } else {
      debug("psi_recv(%s): received input: %d bytes, ret=%d",
	    psiQ._name, strlen(t.data), ret);
      break;
    }
  }
  if (ret > 0){
    memcpy(data, t.data, ret);
    data[ret] = '\0';
  } else {
    debug("psi_recv:  msgrecv(%d, %p, %d, 0, IPC_NOWAIT: %s", psiQ._handle, &t, len, strerror(errno));
    ret = -1;
  }
  
  debug("psi_recv(%s): returns %d bytes\n", psiQ._name, ret);
  return ret;
};

/*!
  @brief Send a large message to an output queue.
  Send a message larger than PSI_MSG_MAX bytes to an output queue by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  psi_recv_nolimit for communication to make sense.
  @param[in] psiQ psiOutput_t structure that message should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int psi_send_nolimit(const psiOutput_t psiQ, const char *data, const int len){
  debug("psi_send_nolimit(%s): %d bytes", psiQ._name, len);
  int ret = -1;
  int msgsiz = 0;
  char msg[PSI_MSG_MAX];
  sprintf(msg, "%ld", (long)(len));
  ret = psi_send(psiQ, msg, strlen(msg));
  if (ret != 0) {
    debug("psi_send_nolimit(%s): sending size of payload failed.", psiQ._name);
    return ret;
  }
  int prev = 0;
  while (prev < len) {
    if ((len - prev) > PSI_MSG_MAX)
      msgsiz = PSI_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = psi_send(psiQ, data + prev, msgsiz);
    if (ret != 0) {
      debug("psi_send_nolimit(%s): send interupted at %d of %d bytes.",
	    psiQ._name, prev, len);
      break;
    }
    prev += msgsiz;
    debug("psi_send_nolimit(%s): %d of %d bytes sent",
	  psiQ._name, prev, len);
  }
  if (ret == 0)
    debug("psi_send_nolimit(%s): %d bytes completed", psiQ._name, len);
  return ret;
};

/*!
  @brief Receive a large message from an input queue.
  Receive a message larger than PSI_MSG_MAX bytes from an input queue by
  receiving it in parts. This expects the first message to be the size of
  the total message.
  @param[in] psiQ psiOutput_t structure that message should be sent to.
  @param[out] data character pointer to pointer for allocated buffer where the
  message should be stored. A pointer to a pointer is used so that the buffer
  may be reallocated as necessary for the incoming message.
  @param[in] len0 int length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int psi_recv_nolimit(const psiInput_t psiQ, char **data, const int len0){
  debug("psi_recv_nolimit(%s)", psiQ._name);
  long len = 0;
  int ret = -1;
  int msgsiz = 0;
  char msg[PSI_MSG_MAX];
  int prev = 0;
  ret = psi_recv(psiQ, msg, PSI_MSG_MAX);
  if (ret < 0) {
    debug("psi_recv_nolimit(%s): failed to receive payload size.", psiQ._name);
    return -1;
  }
  ret = sscanf(msg, "%ld", &len);
  if (ret != 1) {
    debug("psi_recv_nolimit(%s): failed to parse payload size (%s)",
	  psiQ._name, msg);
    return -1;
  }
  // Reallocate data if necessary
  if (len > len0) {
    *data = (char*)realloc(*data, len);
  }
  ret = -1;
  while (prev < len) {
    if ((len - prev) > PSI_MSG_MAX)
      msgsiz = PSI_MSG_MAX;
    else
      msgsiz = len - prev;
    ret = psi_recv(psiQ, (*data) + prev, msgsiz);
    if (ret < 0) {
      debug("psi_recv_nolimit(%s): recv interupted at %d of %d bytes.",
	    psiQ._name, prev, len);
      break;
    }
    prev += ret;
    debug("psi_recv_nolimit(%s): %d of %d bytes received",
	  psiQ._name, prev, len);
  }
  if (ret > 0) {
    debug("psi_recv_nolimit(%s): %d bytes completed", psiQ._name, prev);
    return prev;
  } else {
    return -1;
  }
};


//==============================================================================
/*!
  Formatted IO 

  Output Usage:
      1. One-time: Create output channel with format specifier.
            psiOutput_t output_channel = psiOutputFmt("out_name", "a=%d, b=%d");
      2. Send:
	    ret = psiSend(output_channel, 1, 2);

  Input Usage:
      1. One-time: Create output channel with format specifier.
            psiInput_t input_channel = psiInput("in_name", "a=%d, b=%d");
      2. Prepare: Allocate space for recovered variables.
            int a, b;
      3. Receive:
            int ret = psiRecv(input_channel, &a, &b);
*/
//==============================================================================

/*!
  @brief Send arguments as a small formatted message to an output queue.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output queue. If the message is larger than
  PSI_MSG_MAX or cannot be encoded, it will not be sent.  
  @param[in] psiQ psiOutput_t structure that queue should be sent to.
  @param[in] ap va_list arguments to be formatted into a message using sprintf.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int vpsiSend(const psiOutput_t psiQ, va_list ap) {
  char buf[PSI_MSG_MAX];
  int ret = vsnprintf(buf, PSI_MSG_MAX, psiQ._fmt, ap);
  debug("vpsiSend(%s): vsnprintf returns %d", psiQ._name, ret);
  if (ret < 0) {
    psilog_error("vpsiSend(%s): vsnprintf encoding error", psiQ._name);
    return -1;
  } else if (ret > PSI_MSG_MAX) {
    psilog_error("vpsiSend(%s): encoded message too large. (PSI_MSG_MAX=%d, len=%d)",
		 psiQ._name, PSI_MSG_MAX, ret);
    return -1;
  }
  ret = psi_send(psiQ, buf, ret);
  debug("vpsiSend(%s): psi_send returns %d", psiQ._name, ret);
  return ret;
};

/*!
  @brief Assign arguments by receiving and parsing a message from an input queue.
  Receive a message smaller than PSI_MSG_MAX bytes from an input queue and parse
  it using the associated format string.
  @param[in] psiQ psiOutput_t structure that message should be sent to.
  @param[out] ap va_list arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed. -2 is
  returned if EOF is received.
 */
static inline
int vpsiRecv(const psiInput_t psiQ, va_list ap) {
  // Receive message
  char buf[PSI_MSG_MAX];
  int ret = psi_recv(psiQ, buf, PSI_MSG_MAX);
  if (ret < 0) {
    /* psilog_error("vpsiRecv(%s): Error receiving.", psiQ._name); */
    return ret;
  }
  debug("vpsiRecv(%s): psi_recv returns %d: %s", psiQ._name, ret, buf);
  if (is_eof(buf)) {
    debug("vpsiRecv(%s): EOF received.\n", psiQ._name);
    return -2;
  }
  // Simplify format
  char fmt[PSI_MSG_MAX];
  strcpy(fmt, psiQ._fmt);
  int sret = simplify_formats(fmt, PSI_MSG_MAX);
  if (sret < 0) {
    psilog_error("vpsiRecv(%s): simplify_formats returned %d",
		 psiQ._name, sret);
    return -1;
  }
  debug("vpsiRecv(%s): simplify_formats returns %d", psiQ._name, sret);
  // Interpret message
  sret = vsscanf(buf, fmt, ap);
  if (sret != psiQ._nfmt) {
    psilog_error("vpsiRecv(%s): vsscanf filled %d variables, but there are %d formats",
		 psiQ._name, sret, psiQ._nfmt);
    return -1;
  }
  debug("vpsiRecv(%s): vsscanf returns %d", psiQ._name, sret);
  return ret;
};

/*!
  @brief Send arguments as a small formatted message to an output queue.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output queue. If the message is larger than
  PSI_MSG_MAX or cannot be encoded, it will not be sent.  
  @param[in] psiQ psiOutput_t structure that queue should be sent to.
  @param[in] ... arguments to be formatted into a message using sprintf.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int psiSend(const psiOutput_t psiQ, ...){
  va_list ap;
  va_start(ap, psiQ);
  int ret = vpsiSend(psiQ, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Assign arguments by receiving and parsing a message from an input queue.
  Receive a message smaller than PSI_MSG_MAX bytes from an input queue and parse
  it using the associated format string.
  @param[in] psiQ psiOutput_t structure that message should be sent to.
  @param[out] ... arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed.
 */
static inline
int psiRecv(const psiInput_t psiQ, ...){
  va_list ap;
  va_start(ap, psiQ);
  int ret = vpsiRecv(psiQ, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Send arguments as a large formatted message to an output queue.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output queue. The message can be larger than
  PSI_MSG_MAX. If it cannot be encoded, it will not be sent.  
  @param[in] psiQ psiOutput_t structure that queue should be sent to.
  @param[in] ap va_list arguments to be formatted into a message using sprintf.
  @returns int 0 if formatting and send succesfull, -1 if formatting or send
  unsuccessful.
 */
static inline
int vpsiSend_nolimit(const psiOutput_t psiQ, va_list ap) {
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret = vsnprintf(buf, PSI_MSG_MAX, psiQ._fmt, ap);
  if (ret < 0) {
    psilog_error("vpsiSend_nolimit(%s): vsnprintf encoding error", psiQ._name);
    free(buf);
    return -1;
  } else if (ret > PSI_MSG_MAX) {
    buf = (char*)realloc(buf, ret+1);
    ret = vsnprintf(buf, ret, psiQ._fmt, ap);
  }
  debug("vpsiSend_nolimit(%s): vsnprintf returns %d", psiQ._name, ret);
  ret = psi_send_nolimit(psiQ, buf, ret);
  debug("vpsiSend_nolimit(%s): psi_send_nolimit returns %d", psiQ._name, ret);
  free(buf);
  return ret;
};

/*!
  @brief Assign arguments by receiving and parsing a message from an input queue.
  Receive a message larger than PSI_MSG_MAX bytes in chunks from an input queue
  and parse it using the associated format string.
  @param[in] psiQ psiOutput_t structure that message should be sent to.
  @param[out] ap va_list arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed. -2 is
  returned if EOF is received.
 */
static inline
int vpsiRecv_nolimit(const psiInput_t psiQ, va_list ap) {
  // Receive message
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret = psi_recv_nolimit(psiQ, &buf, PSI_MSG_MAX);
  if (ret < 0) {
    /* psilog_error("vpsiRecv_nolimit(%s): Error receiving.", psiQ._name); */
    free(buf);
    return ret;
  }
  debug("vpsiRecv_nolimit(%s): psi_recv returns %d", psiQ._name, ret);
  if (is_eof(buf)) {
    debug("vpsiRecv(%s): EOF received.\n", psiQ._name);
    free(buf);
    return -2;
  }
  // Simplify format
  char fmt[PSI_MSG_MAX];
  strcpy(fmt, psiQ._fmt);
  int sret = simplify_formats(fmt, PSI_MSG_MAX);
  if (sret < 0) {
    psilog_error("vpsiRecv_nolimit(%s): simplify_formats returned %d",
		 psiQ._name, sret);
    free(buf);
    return -1;
  }
  debug("vpsiRecv_nolimit(%s): simplify_formats returns %d", psiQ._name, sret);
  // Interpret message
  sret = vsscanf(buf, fmt, ap);
  if (sret != psiQ._nfmt) {
    psilog_error("vpsiRecv_nolimit(%s): vsscanf filled %d variables, but there are %d formats",
		 psiQ._name, sret, psiQ._nfmt);
    free(buf);
    return -1;
  }
  debug("vpsiRecv_nolimit(%s): vsscanf returns %d", psiQ._name, sret);
  free(buf);
  return ret;
};

/*!
  @brief Send arguments as a large formatted message to an output queue.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output queue. The message can be larger than
  PSI_MSG_MAX. If it cannot be encoded, it will not be sent.  
  @param[in] psiQ psiOutput_t structure that queue should be sent to.
  @param[in] ... arguments to be formatted into a message using sprintf.
  @returns int 0 if formatting and send succesfull, -1 if formatting or send
  unsuccessful.
 */
static inline
int psiSend_nolimit(const psiOutput_t psiQ, ...) {
  va_list ap;
  va_start(ap, psiQ);
  int ret = vpsiSend_nolimit(psiQ, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Assign arguments by receiving and parsing a message from an input queue.
  Receive a message larger than PSI_MSG_MAX bytes in chunks from an input queue
  and parse it using the associated format string.
  @param[in] psiQ psiInput_t structure that message should be sent to.
  @param[out] ... arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed.
 */
static inline
int psiRecv_nolimit(const psiInput_t psiQ, ...) {
  va_list ap;
  va_start(ap, psiQ);
  int ret = vpsiRecv_nolimit(psiQ, ap);
  va_end(ap);
  return ret;
};

 
//==============================================================================
/*!
  Remote Procedure Call (RPC) IO 

  Handle IO case of a server receiving input from clients, performing some
  calculation, and then sending a response back to the client.

  Server Usage:
      1. One-time: Create server channels with format specifiers for input and
         output.
            psiRpc_t srv = psiRpcServer("srv_name", "%d", "%d %d");
      2. Prepare: Allocate space for recovered variables from request.
            int a;
      3. Receive request:
            int ret = rpcRecv(srv, &a);
      4. Process: Do tasks the server should do with input to produce output.
            int b = 2*a;
	    int c = 3*a;
      2. Send response:
	    ret = rpcSend(srv, b, c);

  Client Usage:
      1. One-time: Create client channels to desired server with format
         specifiers for output and input (should be the same arguments as for
	 the server except for name).
	    psiRpc_t cli = psiRpcClient("cli_name", "%d", "%d %d"); 
      2. Prepare: Allocate space for recovered variables from response.
            int b, c;
      3. Call server:
            int ret = rpcCall(cli, 1, &b, &c);

   Clients can also send several requests at once before receiving any
   responses. This allows the server to be processing the next requests
   while the client handles the previous response, thereby increasing
   efficiency. The responses are assumed to be in the same order as the
   generating requests (i.e. first come, first served).

*/
//==============================================================================

/*!
  @brief Remote Procedure Call (RPC) structure.
  Contains information required to coordinate sending/receiving 
  response/requests from/to an RPC server/client.
 */
typedef struct psiRpc_t {
  psiInput_t _input; //!< Input queue structure.
  psiOutput_t _output; //!< Output queue structure.
} psiRpc_t;

/*!
  @brief Constructor for RPC structure.
  Creates an instance of psiRpc_t with provided information.
  @param[in] outName constant character pointer name of the output queue.
  @param[in] outFormat character pointer to format that should be used for
  formatting output.
  @param[in] inName constant character pointer to name of the input queue.
  @param[in] inFormat character pointer to format that should be used for
  parsing input.
  @return psiRpc_t structure with provided info.
 */
static inline 
psiRpc_t psiRpc(const char *outName, const char *outFormat,
		const char *inName, const char *inFormat){
  psiRpc_t rpc;
  rpc._input = psiInputFmt(inName, inFormat);
  rpc._output = psiOutputFmt(outName, outFormat);
  return rpc;
};

/*!
  @brief Constructor for client side RPC structure.
  Creates an instance of psiRpc_t with provided information.  
  @param[in] name constant character pointer to name for queues.
  @param[in] outFormat character pointer to format that should be used for
  formatting output.
  @param[in] inFormat character pointer to format that should be used for
  parsing input.
  @return psiRpc_t structure with provided info.
 */
static inline 
psiRpc_t psiRpcClient(const char *name, const char *outFormat, const char *inFormat){
  psiRpc_t rpc = psiRpc(name, outFormat, name, inFormat);
  return rpc;
};

/*!
  @brief Constructor for server side RPC structure.
  Creates an instance of psiRpc_t with provided information.  
  @param[in] name constant character pointer to name for queues.
  @param[in] inFormat character pointer to format that should be used for
  parsing input.
  @param[in] outFormat character pointer to format that should be used for
  formatting output.
  @return psiRpc_t structure with provided info.
 */
static inline 
psiRpc_t psiRpcServer(const char *name, const char *inFormat, const char *outFormat){
  psiRpc_t rpc = psiRpc(name, outFormat, name, inFormat);
  return rpc;
};

/*!
  @brief Format and send a message to an RPC output queue.
  Format provided arguments list using the output queue format string and
  then sends it to the output queue under the assumption that it is larger
  than the maximum message size.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[in] ap va_list variable list of arguments for formatting.
  @return integer specifying if the send was succesful. Values >= 0 indicate
  success.
 */
static inline
int vrpcSend(const psiRpc_t rpc, va_list ap) {
  int ret = vpsiSend_nolimit(rpc._output, ap);
  return ret;
};

/*!
  @brief Receive and parse a message from an RPC input queue.
  Receive a message from the input queue under the assumption that it is
  larger than the maximum message size. Then parse the message using the
  input queue format string to extract parameters and assign them to the
  arguments.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[out] ap va_list variable list of arguments that should be assigned
  parameters extracted using the format string. Since these will be assigned,
  they should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
*/
static inline
int vrpcRecv(const psiRpc_t rpc, va_list ap) {
  int ret = vpsiRecv_nolimit(rpc._input, ap);
  return ret;
};

/*!
  @brief Format and send a message to an RPC output queue.
  Format provided arguments using the output queue format string and
  then sends it to the output queue under the assumption that it is larger
  than the maximum message size.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[in] ... arguments for formatting.
  @return integer specifying if the send was succesful. Values >= 0 indicate
  success.
 */
static inline
int rpcSend(const psiRpc_t rpc, ...){
  va_list ap;
  va_start(ap, rpc);
  int ret = vrpcSend(rpc, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Receive and parse a message from an RPC input queue.
  Receive a message from the input queue under the assumption that it is
  larger than the maximum message size. Then parse the message using the
  input queue format string to extract parameters and assign them to the
  arguments.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[out] ... mixed arguments that should be assigned parameters extracted
  using the format string. Since these will be assigned, they should be
  pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
*/
static inline
int rpcRecv(const psiRpc_t rpc, ...){
  va_list ap;
  va_start(ap, rpc);
  int ret = vrpcRecv(rpc, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Send request to an RPC server from the client and wait for a response.
  Format arguments using the output queue format string, send the message to the
  output queue, receive a response from the input queue, and assign arguments
  from the message using the input queue format string to parse it.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[in,out] ap va_list mixed arguments that include those that should be
  formatted using the output format string, followed by those that should be
  assigned parameters extracted using the input format string. These that will
  be assigned should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
 */
static inline
int vrpcCall(const psiRpc_t rpc, va_list ap) {
  int ret;
  
  // pack the args and call
  ret = vpsiSend_nolimit(rpc._output, ap);
  if (ret < 0) {
    printf("vrpcCall: vpsiSend_nolimit error: ret %d: %s\n", ret, strerror(errno));
    return -1;
  }
  
  // unpack the messages into the remaining variable arguments
  va_list op;
  va_copy(op, ap);
  ret = vpsiRecv_nolimit(rpc._input, op);
  va_end(op);
  
  return ret;
};

/*!
  @brief Send request to an RPC server from the client and wait for a response.
  Format arguments using the output queue format string, send the message to the
  output queue, receive a response from the input queue, and assign arguments
  from the message using the input queue format string to parse it.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[in,out] ... mixed arguments that include those that should be
  formatted using the output format string, followed by those that should be
  assigned parameters extracted using the input format string. These that will
  be assigned should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
 */
static inline
int rpcCall(const psiRpc_t rpc,  ...){
  int ret;
  va_list ap;
  va_start(ap, rpc);
  ret = vrpcCall(rpc, ap);
  va_end(ap);
  return ret;
};


//==============================================================================
/*!
  File IO

  Handle I/O from/to a local or remote file line by line.

  Input Usage:
      1. One-time: Create file interface by providing either a channel name or
         a path to a local file.
	    psiAsciiFileInput_t fin = psiAsciiFileInput("file_channel", 1); // channel
	    psiAsciiFileInput_t fin = psiAsciiFileInput("/local/file.txt", 0); // local file
      2. Prepare: Allocate space for lines.
            char line[PSI_MSG_MAX];
      3. Receive each line, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = af_recv_line(fin, line, PSI_MSG_MAX);
	      // Do something with the line
	    }
      4. Cleanup. Call functions to deallocate structures and close files.
            cleanup_pafi(&fin);

  Output Usage:
      1. One-time: Create file interface by providing either a channel name or
         a path to a local file.
	    psiAsciiFileOutput_t fout = psiAsciiFileOutput("file_channel", 1); // channel
	    psiAsciiFileOutput_t fout = psiAsciiFileOutput("/local/file.txt", 0); // local file
      2. Send lines to the file. If return value is not 0, the send was not
          succesfull.
            int ret;
	    ret = af_send_line(fout, "Line 1\n");
	    ret = af_send_line(fout, "Line 2\n");
      3. Send EOF message when done to close the file.
            ret = af_send_eof(fout);
      4. Cleanup. Call functions to deallocate structures and close files.
            cleanup_pafo(&fout);

*/
//==============================================================================

/*!
  @brief Structure of information for output to a file line by line.
 */
typedef struct psiAsciiFileOutput_t {
  int _valid; //!< Indicates if the structure was succesfully initialized.
  const char *_name; //!< Path to local file or name of output channel.
  int _type; //!< 0 for local file, 1 for output channel.
  asciiFile_t _file; //!< Associated output handler for local files.
  psiOutput_t _psi; //!< Associated output handler for output channel.
} psiAsciiFileOutput_t;

/*!
  @brief Structure of information for input from a file line by line. 
 */
typedef struct psiAsciiFileInput_t {
  int _valid; //!< Indicates if the structure was succesfully initialized.
  const char *_name; //!< Path to local file or name of input channel. 
  int _type; //!< 0 for local file, 1 for input channel.
  asciiFile_t _file; //!< Associated input handler for local files.
  psiInput_t _psi; //!< Associated input handler for input channel. 
} psiAsciiFileInput_t;

/*!
  @brief Constructor for psiAsciiFileOutput_t.
  Based on the value of dst_type, either a local file will be opened for output
  (dst_type == 0), or a psiOutput_t connection will be made.
  @param[in] name constant character pointer to path of local file or name of
  an output queue.
  @param[in] dst_type int 0 if name refers to a local file, 1 if it is a queue.
  @returns psiAsciiFileOutput_t for line-by-line output to a file or channel.
 */
static inline
psiAsciiFileOutput_t psiAsciiFileOutput(const char *name, const int dst_type) {
  psiAsciiFileOutput_t out;
  int ret;
  out._name = name;
  out._type = dst_type;
  out._valid = 1;
  if (dst_type == 0) {
    out._file = asciiFile(name, "w", NULL, NULL);
    ret = af_open(&(out._file));
    if (ret != 0) {
      psilog_error("psiAsciiFileOutput: Could not open %s", name);
      out._valid = 0;
    }
  } else {
    out._psi = psiOutput(name);
    out._file = asciiFile(name, "0", NULL, NULL);
  }
  return out;
};

/*!
  @brief Constructor for psiAsciiFileInput_t.
  Based on the value of src_type, either a local file will be opened for input
  (src_type == 0), or a psiInput_t connection will be made.
  @param[in] name constant character pointer to path of local file or name of
  an input queue.
  @param[in] src_type int 0 if name refers to a local file, 1 if it is a queue.
  @returns psiAsciiFileInput_t for line-by-line input from a file or channel.
 */
static inline
psiAsciiFileInput_t psiAsciiFileInput(const char *name, const int src_type) {
  psiAsciiFileInput_t out;
  int ret;
  out._name = name;
  out._type = src_type;
  out._valid = 1;
  if (src_type == 0) { // Direct file interface
    out._file = asciiFile(name, "r", NULL, NULL);
    ret = af_open(&(out._file));
    if (ret != 0) {
      psilog_error("psiAsciiFileInput: Could not open %s", name);
      out._valid = 0;
    }
  } else {
    out._psi = psiInput(name);
    out._file = asciiFile(name, "0", NULL, NULL);
  }
  return out;
};

/*!
  @brief Send EOF message to output file, closing it.
  @param[in] t psiAsciiFileOutput_t output structure.
  @returns int 0 if send was succesfull. All other values indicate errors.
 */
static inline
int af_send_eof(const psiAsciiFileOutput_t t) {
  char buf[PSI_MSG_MAX] = PSI_MSG_EOF;
  int ret = psi_send(t._psi, buf, strlen(buf));
  return ret;
};

/*!
  @brief Receive a single line from an associated file or queue.
  @param[in] t psiAsciiFileInput_t input structure.
  @param[out] line character pointer to allocate memory where the received
  line should be stored.
  @param[in] n size_t Size of the allocated memory block in bytes.
  @returns int Number of bytes read/received. Negative values indicate that
  there was either an error or the EOF message was received.
 */
static inline
int af_recv_line(const psiAsciiFileInput_t t, char *line, size_t n) {
  int ret;
  if (t._type == 0) {
    ret = af_readline_full(t._file, &line, &n);
  } else {
    ret = psi_recv(t._psi, line, n);
    if (ret > 0) {
      if (is_eof(line))
	ret = -1;
    }
  }
  return ret;
};

/*!
  @brief Send a single line to a file or queue.
  @param[in] t psiAsciiFileOutput_t output structure.
  @param[in] line character pointer to line that should be sent.
  @returns int 0 if send was succesfull. Other values indicate errors.
 */
static inline
int af_send_line(const psiAsciiFileOutput_t t, const char *line) {
  int ret;
  if (t._type == 0) {
    ret = af_writeline_full(t._file, line);
  } else {
    ret = psi_send(t._psi, line, strlen(line));
  }
  return ret;
};

/*!
  @brief Deallocate and clean up psiAsciiFileInput_t structure.
  @param[in] t psiAsciiFileInput_t pointer.
 */
static inline
void cleanup_pafi(psiAsciiFileInput_t *t) {
  af_close(&((*t)._file));
};

/*!
  @brief Deallocate and clean up psiAsciiFileOutput_t structure.
  @param[in] t psiAsciiFileOutput_t pointer.
 */
static inline
void cleanup_pafo(psiAsciiFileOutput_t *t) {
  af_close(&((*t)._file));
};


//==============================================================================
/*!
  Table IO

  Handle I/O from/to a local or remote ASCII table either line-by-line or as
  an array.

  Row-by-Row
  ==========

  Input by Row Usage:
      1. One-time: Create file interface by providing either a channel name or
         a path to a local file.
	    psiAsciiTableInput_t fin = psiAsciiTableInput("file_channel", 1);    // channel
	    psiAsciiTableInput_t fin = psiAsciiTableInput("/local/file.txt", 0); // local table
      2. Prepare: Allocate space for variables in row (the format in this
         example is "%5s %d %f\n" like the output example below).
	    char a[5];
	    int b;
	    double c;
      3. Receive each row, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = at_recv_row(fin, &a, &b, &c);
	      // Do something with the row
	    }
      4. Cleanup. Call functions to deallocate structures and close files.
            cleanup_pati(&fin);

  Output by Row Usage:
      1. One-time: Create file interface by providing either a channel name or
         a path to a local file and a format string for rows.
	    psiAsciiTableOutput_t fout = psiAsciiTableOutput("file_channel",    // channel
                                                             "%5s %d %f\n", 1);
	    psiAsciiTableOutput_t fout = psiAsciiTableOutput("/local/file.txt", // local table
	                                                     "%5s %d %f\n", 0);
      2. Send rows to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    ret = at_send_row(fout, "one", 1, 1.0);
	    ret = at_send_row(fout, "two", 2, 2.0);
      3. Send EOF message when done to close the file.
            ret = at_send_eof(fout);
      4. Cleanup. Call functions to deallocate structures and close files.
            cleanup_pato(&fout);

  Array
  =====

  Input by Array Usage:
      1. One-time: Create file interface by providing either a channel name or
         a path to a local file.
	    psiAsciiTableInput_t fin = psiAsciiTableInput("file_channel", 1);    // channel
	    psiAsciiTableInput_t fin = psiAsciiTableInput("/local/file.txt", 0); // local table
      2. Prepare: Declare pointers for table columns (they will be allocated by
         the interface once the number of rows is known).
	    char *aCol;
	    int *bCol;
	    double *cCol;
      3. Receive entire table as columns. Return value will be the number of
         elements in each column (the number of table rows). Negative values
	 indicate errors.
            int ret = at_recv_array(fin, &a, &b, &c);
      4. Cleanup. Call functions to deallocate structures and close files.
            cleanup_pati(&fin);

  Output by Array Usage:
      1. One-time: Create file interface by providing either a channel name or
         a path to a local file and a format string for rows.
	    psiAsciiTableOutput_t fout = psiAsciiTableOutput("file_channel",    // channel
                                                             "%5s %d %f\n", 1);
	    psiAsciiTableOutput_t fout = psiAsciiTableOutput("/local/file.txt", // local table
	                                                     "%5s %d %f\n", 0);
      2. Send columns to the file by providing pointers (or arrays). Formatting
         is handled by the interface. If return value is not 0, the send was not
	 succesful.
	    char aCol[] = {"one  ", "two  ", "three"}; \\ Each str is of len 5
	    int bCol[3] = {1, 2, 3};
	    float cCol[3] = {1.0, 2.0, 3.0};
            int ret = at_send_array(fout, a, b, c);
      3. Cleanup. Call functions to deallocate structures and close files.
            cleanup_pato(&fout);

*/
//==============================================================================

/*!
  @brief Structure for handling output to an ASCII table.
 */
typedef struct psiAsciiTableOutput_t {
  int _valid; //!< Success or failure of initializing the structure
  const char *_name; //!< Path to local table or name of message queue
  int _type; //!< 0 if #_name is a local table, 1 if it is a message queue.
  asciiTable_t _table; //!< Associated output handler for local tables.
  psiOutput_t _psi; //!< Associated output handler for queues.
} psiAsciiTableOutput_t;

/*!
  @brief Structure for handling input from an ASCII table.
 */
typedef struct psiAsciiTableInput_t {
  int _valid; //!< Success or failure of initializing the structure
  const char *_name; //!< Path to local table or name of message queue
  int _type; //!< 0 if #_name is a local table, 1 if it is a message queue.
  asciiTable_t _table; //!< Associated input handler for local tables. 
  psiInput_t _psi; //!< Associated input handler for queues.
} psiAsciiTableInput_t;

/*!
  @brief Constructor for psiAsciiTableOutput_t.
  @param[in] name constant character pointer to local file path or message
  queue name.
  @param[in] format_str character pointer to format string that should be used
  to format rows into table lines.
  @param[in] dst_type int 0 if name is a local file path, 1 if it is the name
  of a message queue.
  @returns psiAsciiTableOutput_t output structure.
 */
static inline
psiAsciiTableOutput_t psiAsciiTableOutput(const char *name, const char *format_str,
					  const int dst_type) {
  psiAsciiTableOutput_t out;
  int ret;
  out._valid = 1;
  out._name = name;
  out._type = dst_type;
  if (dst_type == 0) {
    out._table = asciiTable(name, "w", format_str,
			    NULL, NULL, NULL);
    ret = at_open(&(out._table));
    if (ret != 0) {
      psilog_error("psiAsciiTableOutput: Could not open %s", name);
      out._valid = 0;
    } else {
      at_writeformat(out._table);
    }
  } else {
    out._psi = psiOutput(name);
    ret = psi_send(out._psi, format_str, strlen(format_str));
    if (ret != 0) {
      psilog_error("psiAsciiTableOutput: Failed to receive format string.");
      out._valid = 0;
    } else {
      out._table = asciiTable(name, "0", format_str,
			      NULL, NULL, NULL);
      strcpy(out._psi._fmt, format_str);
      out._psi._nfmt = count_formats(out._psi._fmt);
    }
  }
  return out;
};

/*!
  @brief Constructor for psiAsciiTableInput_t.
  @param[in] name constant character pointer to local file path or message
  queue name.
  @param[in] src_type int 0 if name is a local file path, 1 if it is the name
  of a message queue.
  @returns psiAsciiTableInput_t input structure.
 */
static inline
psiAsciiTableInput_t psiAsciiTableInput(const char *name, const int src_type) {
  psiAsciiTableInput_t out;
  int ret;
  out._valid = 1;
  out._name = name;
  out._type = src_type;
  if (src_type == 0) { // Direct file interface
    out._table = asciiTable(name, "r", NULL,
			    NULL, NULL, NULL);
    ret = at_open(&(out._table));
    if (ret != 0) {
      psilog_error("psiAsciiTableInput: Could not open %s", name);
      out._valid = 0;
    }
  } else {
    out._psi = psiInput(name);
    ret = psi_recv(out._psi, out._psi._fmt, PSI_MSG_MAX);
    if (ret < 0) {
      psilog_error("psiAsciiTableInput: Failed to receive format string.");
      out._valid = 0;
    } else {
      out._psi._nfmt = count_formats(out._psi._fmt);
      out._table = asciiTable(name, "0", out._psi._fmt,
			      NULL, NULL, NULL);
    }
  }
  return out;
};

/*!
  @brief Send a nolimit message to a table output queue.
  @param[in] t psiAsciiTableOutput_t output structure.
  @param[in] data character pointer to message that should be sent.
  @param[in] len int length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int at_psi_send(const psiAsciiTableOutput_t t, const char *data, const int len){
  return psi_send_nolimit(t._psi, data, len);
};
  
/*!
  @brief Recv a nolimit message from a table input queue.
  @param[in] t psiAsciiTableInput_t input structure.
  @param[in] data character pointer to pointer to memory where received message
  should be stored. It does not need to be allocated, only defined.
  @param[in] len int length of allocated buffer.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int at_psi_recv(const psiAsciiTableInput_t t, char **data, const int len){
  return psi_recv_nolimit(t._psi, data, len);
};

/*!
  @brief Send a nolimit EOF message to a table output queue.
  @param[in] t psiAsciiTableOutput_t output structure.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int at_send_eof(const psiAsciiTableOutput_t t) {
  char buf[PSI_MSG_MAX] = PSI_MSG_EOF;
  int ret = psi_send_nolimit(t._psi, buf, strlen(buf));
  return ret;
};

/*!
  @brief Format and send a row to the table file/queue.
  @param[in] t psiAsciiTableOutput_t output structure.
  @param[in] ap va_list Row elements that should be formatted.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int vsend_row(const psiAsciiTableOutput_t t, va_list ap) {
  int ret;
  if (t._type == 0) {
    ret = at_vwriteline(t._table, ap);
    if (ret > 0)
      ret = 0;
    else
      ret = -1;
  } else {
    ret = vpsiSend_nolimit(t._psi, ap);
  }
  return ret;
};

/*!
  @brief Recv and parse a row from the table file/queue.
  @param[in] t psiAsciiTableInput_t input structure.
  @param[in] ap va_list Pointers to memory where variables from the parsed
  should be stored.
  @returns int -1 if message could not be received or parsed, otherwise the 
  length of the received is returned.
 */
static inline
int vrecv_row(const psiAsciiTableInput_t t, va_list ap) {
  int ret;
  if (t._type == 0) {
    ret = at_vreadline(t._table, ap);
  } else {
    ret = vpsiRecv_nolimit(t._psi, ap);
  }
  return ret;
};

/*!
  @brief Format and send a row to the table file/queue.
  @param[in] t psiAsciiTableOutput_t output structure.
  @param[in] ... Row elements that should be formatted.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int at_send_row(const psiAsciiTableOutput_t t, ...) {
  int ret;
  va_list ap;
  va_start(ap, t);
  ret = vsend_row(t, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Recv and parse a row from the table file/queue.
  @param[in] t psiAsciiTableInput_t input structure.
  @param[in] ... Pointers to memory where variables from the parsed row
  should be stored.
  @returns int -1 if message could not be received or parsed, otherwise the 
  length of the received is returned.
 */
static inline
int at_recv_row(const psiAsciiTableInput_t t, ...) {
  int ret;
  va_list ap;
  va_start(ap, t);
  ret = vrecv_row(t, ap);
  va_end(ap);
  return ret;
};
 
/*!
  @brief Format and send table columns to the table file/queue.
  @param[in] t psiAsciiTableOutput_t output structure.
  @param[in] nrows int Number of rows in the columns.
  @param[in] ap va_list Pointers to memory containing table columns that
  should be formatted.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int vsend_array(const psiAsciiTableOutput_t t, const int nrows, va_list ap) {
  int ret;
  if (t._type == 0) {
    printf("Not currently implemented.\n");
    ret = -1;
  } else {
    char *data = NULL;
    ret = at_varray_to_bytes(t._table, &data, nrows, ap);
    /* printf("Sending %d: ", ret); */
    /* fwrite(data, ret, 1, stdout); */
    /* printf("\n"); */
    if (ret >= 0) {
      ret = psi_send_nolimit(t._psi, data, ret);
    } else {
      char buf[10] = "";
      psi_send(t._psi, buf, 0);
    }
    free(data);
  }
  return ret;
};

/*!
  @brief Recv and parse columns from a table file/queue.
  @param[in] t psiAsciiTableInput_t input structure.
  @param[in] ap va_list Pointers to pointers to memory where columns from the
  parsed table should be stored. They need not be allocated, only declared.
  @returns int Number of rows received. Negative values indicate errors.
 */
static inline
int vrecv_array(const psiAsciiTableInput_t t, va_list ap) {
  int ret;
  if (t._type == 0) {
    printf("Not currently implemented.\n");
    ret = -1;
  } else {
    int data_siz = 10*t._table.row_siz;
    char *data = (char*)malloc(data_siz);
    ret = psi_recv_nolimit(t._psi, &data, data_siz);
    /* printf("Received: "); */
    /* fwrite(data, ret, 1, stdout); */
    /* printf("\n"); */
    if (ret >= 0) {
      ret = at_vbytes_to_array(t._table, data, ret, ap);
    }
  }
  return ret;
};

/*!
  @brief Format and send table columns to the table file/queue.
  @param[in] t psiAsciiTableOutput_t output structure.
  @param[in] nrows int Number of rows in the columns.
  @param[in] ... Pointers to memory containing table columns that
  should be formatted.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int at_send_array(const psiAsciiTableOutput_t t, const int nrows, ...) {
  int ret;
  va_list ap;
  va_start(ap, nrows);
  ret = vsend_array(t, nrows, ap);
  va_end(ap);
  return ret;
};

/*!
  @brief Recv and parse columns from a table file/queue.
  @param[in] t psiAsciiTableInput_t input structure.
  @param[in] ... Pointers to pointers to memory where columns from the
  parsed table should be stored. They need not be allocated, only declared.
  @returns int Number of rows received. Negative values indicate errors.
 */
static inline
int at_recv_array(const psiAsciiTableInput_t t, ...) {
  int ret;
  va_list ap;
  va_start(ap, t);
  ret = vrecv_array(t, ap);
  va_end(ap);
  return ret;
};
 
/*!
  @brief Deallocate and clean up psiAsciiTableInput_t structure.
  @param[in] t psiAsciiTableInput_t pointer.
 */
static inline
void cleanup_pati(psiAsciiTableInput_t *t) {
  at_close(&((*t)._table));
  at_cleanup(&((*t)._table));
};

/*!
  @brief Deallocate and clean up psiAsciiTableOutput_t structure.
  @param[in] t psiAsciiTableOutput_t pointer.
 */
static inline
void cleanup_pato(psiAsciiTableOutput_t *t) {
  at_close(&((*t)._table));
  at_cleanup(&((*t)._table));
};

#endif /*PSIINTERFACE_H_*/
