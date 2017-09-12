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
#include <../dataio/AsciiFile.h>
#include <../dataio/AsciiTable.h>


#define PSI_MSG_MAX 1024*2
#define PSI_MSG_EOF "EOF!!!"
// track 256 channels in use- fail if re-using
// max # channels 
#define _psiTrackChannels 256
static char * _psiChannelNames[_psiTrackChannels]; 
static unsigned _psiChannelsUsed = 0;


static inline
int count_formats(const char* fmt_str) {
  int c = 0;
  for (char* s = (char*)fmt_str; (s = strstr(s, "%")); s++) {
    if (strncmp(s, "%%", 2) == 0)
      s++;
    else
      c++;
  }
  return c;
};


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
  
#define error psiError
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
int psi_mq(char *name, const char *yamlName){
  // Look up registered name
  char *qid = getenv(name);
  // Fail if the driver did not declare the channel
  if (qid == NULL) {
    error("psi_mq: Channel %s not registered, model/YAML mismatch (yaml=%s)\n",
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
      error("psi_mq: Directed channel %s exists, but requested channel %s does not\n",
	    nm_opp, name);
    }
    return -1;
  }
  // Fail if trying to re-use the same channel twice
  for (unsigned i =0; i < _psiChannelsUsed; i++ ){
    if (0 == strcmp(_psiChannelNames[i], name)){
      error("Attempt to re-use channel %s", name);
      return -1;
    }
  }
  // Fail if > _psiTrackChannels channels used
  if (_psiChannelsUsed >= _psiTrackChannels) {
    error("Too many channels in use, max: %d\n", _psiTrackChannels);
    return -1;
  }
  _psiChannelNames[_psiChannelsUsed++] = qid;
  int qkey = atoi(qid);
  int fid = msgget(qkey, 0600);
  return fid;
};

/*!
  @brief Message buffer structure.
*/
typedef struct msgbuf_t {
  long mtype; //< Message buffer type
  char data[PSI_MSG_MAX]; //< Buffer for the message
} msgbuf_t;

/*!
  @brief Input queue structure.
  Contains information on an input queue.
 */
typedef struct psiInput_t {
  int _handle; //< Queue handle.
  const char *_name; //< Queue name.
  char *_fmt; //< Format for interpreting queue messages.
} psiInput_t;

/*!
  @brief Output queue structure.
  Contains information on an output queue.
 */
typedef struct psiOutput_t {
  int _handle; //< Queue handle. 
  const char *_name; //< Queue name.
  char *_fmt; //< Format for formatting queue messages.
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
  ret._handle = psi_mq(nm, name);
  ret._name = name;
  ret._fmt = 0;
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
  ret._fmt = 0;
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
psiOutput_t psiOutputFmt(const char *name, char *fmtString){
  psiOutput_t ret = psiOutput(name);
  ret._fmt = fmtString;
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
psiInput_t psiInputFmt(const char *name, char *fmtString){
  psiInput_t ret = psiInput(name);
  ret._fmt = fmtString;
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
int psi_output_nmsg(psiOutput_t psiQ) {
  int rc;
  struct msqid_ds buf;
  int num_messages;
  rc = msgctl(psiQ._handle, IPC_STAT, &buf);
  if (rc != 0) {
    error("psi_output_nmsg: Could not access queue.");
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
int psi_input_nmsg(psiInput_t psiQ) {
  int rc;
  struct msqid_ds buf;
  int num_messages;
  rc = msgctl(psiQ._handle, IPC_STAT, &buf);
  if (rc != 0) {
    error("psi_input_nmsg: Could not access queue.");
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
int psi_send(psiOutput_t psiQ, char *data, int len){
  debug("psi_send(%s): %d bytes", psiQ._name, len);
  if (len > PSI_MSG_MAX) {
    error("psi_send(%s): message too large for single packet (PSI_MSG_MAX=%d, len=%d)",
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
      error("psi_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s",
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
  @param[in] len int length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int psi_recv(psiInput_t psiQ, char *data, int len){
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
int psi_send_nolimit(psiOutput_t psiQ, char *data, int len){
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
int psi_recv_nolimit(psiInput_t psiQ, char **data, int len0){
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
int vpsiSend(psiOutput_t psiQ, va_list ap) {
  char buf[PSI_MSG_MAX];
  int ret = vsnprintf(buf, PSI_MSG_MAX, psiQ._fmt, ap);
  debug("vpsiSend(%s): vsnprintf returns %d", psiQ._name, ret);
  if (ret < 0) {
    error("vpsiSend(%s): vsnprintf encoding error", psiQ._name);
    return -1;
  } else if (ret > PSI_MSG_MAX) {
    error("vpsiSend(%s): encoded message too large. (PSI_MSG_MAX=%d, len=%d)",
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
  Length of the received message if message was received and parsed.
 */
static inline
int vpsiRecv(psiInput_t psiQ, va_list ap) {
  char buf[PSI_MSG_MAX];
  int ret = psi_recv(psiQ, buf, PSI_MSG_MAX);
  if (ret < 0) {
    error("vpsiRecv(%s): Error receiving.", psiQ._name);
    return -1;
  }
  debug("vpsiRecv(%s): psi_recv returns %d: %s", psiQ._name, ret, buf);
  int nexp = count_formats(psiQ._fmt);
  int sret = vsscanf(buf, psiQ._fmt, ap);
  if (sret != nexp) {
    error("vpsiRecv(%s): vsscanf filled %d variables, but there are %d formats",
          psiQ._name, sret, nexp);
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
int psiSend(psiOutput_t psiQ, ...){
  va_list ap;
  va_start(ap, psiQ._fmt);
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
int psiRecv(psiInput_t psiQ, ...){
  va_list ap;
  va_start(ap, psiQ._fmt);
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
int vpsiSend_nolimit(psiOutput_t psiQ, va_list ap) {
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret = vsnprintf(buf, PSI_MSG_MAX, psiQ._fmt, ap);
  if (ret < 0) {
    error("vpsiSend_nolimit(%s): vsnprintf encoding error", psiQ._name);
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
  Length of the received message if message was received and parsed.
 */
static inline
int vpsiRecv_nolimit(psiInput_t psiQ, va_list ap) {
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret = psi_recv_nolimit(psiQ, &buf, PSI_MSG_MAX);
  if (ret < 0) {
    error("vpsiRecv_nolimit(%s): Error receiving.", psiQ._name);
    free(buf);
    return -1;
  }
  debug("vpsiRecv_nolimit(%s): psi_recv returns %d: %s", psiQ._name, ret, buf);
  int nexp = count_formats(psiQ._fmt);
  int sret = vsscanf(buf, psiQ._fmt, ap);
  if (sret != nexp) {
    error("vpsiRecv_nolimit(%s): vsscanf filled %d variables, but there are %d formats",
          psiQ._name, sret, nexp);
    free(buf);
    return -1;
  }
  debug("vpsiRecv_nolimit(%s): vsscanf returns %d", psiQ._name, ret);
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
int psiSend_nolimit(psiOutput_t psiQ, ...) {
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
int psiRecv_nolimit(psiInput_t psiQ, ...) {
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
  psiInput_t _input; //< Input queue structure.
  psiOutput_t _output; //< Output queue structure.
  char *_inFmt; //< Format string used for input queue.
  char *_outFmt; //< Format string used for output queue
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
psiRpc_t psiRpc(const char *outName, char *outFormat,
		const char *inName, char *inFormat){
  psiRpc_t rpc;
  rpc._inFmt = inFormat;
  rpc._outFmt = outFormat;
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
psiRpc_t psiRpcClient(const char *name, char *outFormat, char *inFormat){
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
psiRpc_t psiRpcServer(const char *name, char *inFormat, char *outFormat){
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
int vrpcSend(psiRpc_t rpc, va_list ap) {
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
int vrpcRecv(psiRpc_t rpc, va_list ap) {
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
int rpcSend(psiRpc_t rpc, ...){
  va_list ap;
  va_start(ap, rpc);
  int ret = vrpcSend(rpc, ap);
  /* char *buf = (char*)malloc(PSI_MSG_MAX); */
  /* int ret = vsnprintf(buf, PSI_MSG_MAX, rpc._outFmt, ap); */
  /* debug("rpcSend(%s): vsnprintf returned %d\n", rpc._output._name, ret); */
  /* ret = psi_send_nolimit(rpc._output, buf, strlen(buf)); */
  /* debug("rpcSend(%s): psi_send returned %d\n", rpc._output._name, ret); */
  
  /* if (ret != 0){ */
  /*   debug("rpcSend(%s): send error %d\n", rpc._output._name, ret); */
  /*   free(buf); */
  /*   return -1; */
  /* } */
  /* free(buf); */
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
int rpcRecv(psiRpc_t rpc, ...){
  va_list ap;
  va_start(ap, rpc);
  int ret = vrpcRecv(rpc, ap);
  /* debug("rpcRecv(%s)\n", rpc._input._name); */
  /* char *buf = (char*)malloc(PSI_MSG_MAX); */
  /* int ret = psi_recv_nolimit(rpc._input, &buf, PSI_MSG_MAX); */
  /* debug("rpcRecv(%s): psi_recv returned %d\n", rpc._input._name, ret); */
  /* if (ret < 0) { */
  /*   debug("rpcRecv: receive error: %d\n", ret); */
  /*   free(buf); */
  /*   return -1; */
  /* } */
  
  /* // unpack the message */
  /* ret = vsscanf(buf, rpc._inFmt, ap); */
  /* debug("rpcRecv(%s): vsscanf returned %d\n", rpc._input._name, ret); */
  /* free(buf); */
  va_end(ap);
  return ret;
};

/*!
  @brief Send request to an RPC server from the client and wait for a response.
  Format arguments using the output queue format string, send the message to the
  output queue, receive a response from the input queue, and assign arguments
  from the message using the input queue format string to parse it.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[in/out] ... mixed arguments that include those that should be
  formatted using the output format string, followed by those that should be
  assigned parameters extracted using the input format string. These that will
  be assigned should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
 */
static inline
int vrpcCall(psiRpc_t rpc, va_list ap) {
  // setup - static variables persist across calls
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret; // always check return values
  
  // pack the args and call
  ret = vsnprintf(buf, PSI_MSG_MAX, rpc._output._fmt, ap);
  ret = psi_send_nolimit(rpc._output, buf, strlen(buf));
  if (ret != 0){
    debug("vrpcCall: psi_send error: %s\n", strerror(errno));
    free(buf);
    return -1;
  }
  
  // receive the message
  ret = psi_recv_nolimit(rpc._input, &buf, PSI_MSG_MAX);
  if (ret < 0) {
    printf("vrpcCall: psi_recv error: ret %d: %s\n", ret, strerror(errno));
    free(buf);
    return -1;
  }
  
  // unpack the messages into the remaining variable arguments
  va_list op;
  va_copy(op, ap);
  ret = vsscanf(buf, rpc._input._fmt, op);
  debug("vrpcCall: return_temporary_buffer %d\n", ret);
  va_end(op);
  
  free(buf);
  return 0;
};

/*!
  @brief Send request to an RPC server from the client and wait for a response.
  Format arguments using the output queue format string, send the message to the
  output queue, receive a response from the input queue, and assign arguments
  from the message using the input queue format string to parse it.
  @param[in] rpc psiRpc_t structure with RPC information.
  @param[in/out] ... mixed arguments that include those that should be
  formatted using the output format string, followed by those that should be
  assigned parameters extracted using the input format string. These that will
  be assigned should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
 */
static inline
int rpcCall(psiRpc_t rpc,  ...){
  // setup - static variables persist across calls
  /* char *buf = (char*)malloc(PSI_MSG_MAX); */
  int ret; // always check return values
  
  // pack the args and call
  va_list ap;
  /* va_list op; */
  va_start(ap, rpc);
  ret = vrpcCall(rpc, ap);
  /* ret = vsnprintf(buf, PSI_MSG_MAX, rpc._outFmt, ap); */
  /* va_copy(op, ap); */
  /* ret = psi_send_nolimit(rpc._output, buf, strlen(buf)); */
  /* if (ret != 0){ */
  /*   debug("rpcCall: psi_send error: %s\n", strerror(errno)); */
  /*   free(buf); */
  /*   return -1; */
  /* } */
  
  /* // receive the message */
  /* ret = psi_recv_nolimit(rpc._input, &buf, PSI_MSG_MAX); */
  /* if (ret < 0) { */
  /*   printf("psi_recv error: ret %d: %s\n", ret, strerror(errno)); */
  /*   free(buf); */
  /*   return -1; */
  /* } */
  
  /* // unpack the messages */
  /* ret = vsscanf(buf, rpc._inFmt, op); */
  /* debug("rpcCall: return_temporary_buffer %d\n", ret); */
  va_end(ap);
  /* va_end(op); */
  
  /* free(buf); */
  return ret;
};

/******************************************************************************/
/* File IO */
/******************************************************************************/
// Specialized methods for passing file rows back and forth

typedef struct PsiAsciiFileOutput {
  int _valid;
  const char *_name;
  int _type;
  AsciiFile _file;
  psiOutput_t _psi;
} PsiAsciiFileOutput;

typedef struct PsiAsciiFileInput {
  int _valid;
  const char *_name;
  int _type;
  AsciiFile _file;
  psiInput_t _psi;
} PsiAsciiFileInput;

static inline
PsiAsciiFileInput psi_ascii_file_input(const char *name, int src_type) {
  PsiAsciiFileInput out;
  int ret;
  out._name = name;
  out._type = src_type;
  out._valid = 1;
  if (src_type == 0) { // Direct file interface
    out._file = ascii_file(name, "r", NULL, NULL);
    ret = af_open(&(out._file));
    if (ret != 0) {
      error("psi_ascii_file_input: Could not open %s", name);
      out._valid = 0;
    }
  } else {
    out._psi = psiInput(name);
    out._file = ascii_file(name, "0", NULL, NULL);
  }
  return out;
};

static inline
PsiAsciiFileOutput psi_ascii_file_output(const char *name, int dst_type) {
  PsiAsciiFileOutput out;
  int ret;
  out._name = name;
  out._type = dst_type;
  out._valid = 1;
  if (dst_type == 0) {
    out._file = ascii_file(name, "w", NULL, NULL);
    ret = af_open(&(out._file));
    if (ret != 0) {
      error("psi_ascii_file_output: Could not open %s", name);
      out._valid = 0;
    }
  } else {
    out._psi = psiOutput(name);
    out._file = ascii_file(name, "0", NULL, NULL);
  }
  return out;
};

static inline
int is_eof(const char *buf) {
  if (strcmp(buf, PSI_MSG_EOF) == 0)
    return 1;
  else
    return 0;
};
  
static inline
int af_send_eof(PsiAsciiFileOutput t) {
  char buf[PSI_MSG_MAX] = PSI_MSG_EOF;
  int ret = psi_send(t._psi, buf, strlen(buf));
  return ret;
};

static inline
int recv_line(PsiAsciiFileInput t, char *line, size_t n) {
  int ret;
  if (t._type == 0) {
    ret = af_readline_full(t._file, &line, &n);
  } else {
    ret = psi_recv(t._psi, line, n);
    if (is_eof(line))
      ret = -1;
  }
  return ret;
};

static inline
int send_line(PsiAsciiFileOutput t, char *line) {
  int ret;
  if (t._type == 0) {
    ret = af_writeline_full(t._file, line);
  } else {
    ret = psi_send(t._psi, line, strlen(line));
  }
  return ret;
};

static inline
void cleanup_pafi(PsiAsciiFileInput *t) {
  af_close(&((*t)._file));
};

static inline
void cleanup_pafo(PsiAsciiFileOutput *t) {
  af_close(&((*t)._file));
};


/******************************************************************************/
/* Table IO */
/******************************************************************************/
// Specialized functions for passing table rows back and forth

typedef struct PsiAsciiTableOutput {
  int _valid;
  const char *_name;
  int _type;
  AsciiTable _table;
  psiOutput_t _psi;
} PsiAsciiTableOutput;

typedef struct PsiAsciiTableInput {
  int _valid;
  const char *_name;
  int _type;
  AsciiTable _table;
  psiInput_t _psi;
} PsiAsciiTableInput;

static inline
PsiAsciiTableInput psi_ascii_table_input(const char *name, int src_type) {
  PsiAsciiTableInput out;
  int ret;
  out._valid = 1;
  out._name = name;
  out._type = src_type;
  if (src_type == 0) { // Direct file interface
    out._table = ascii_table(name, "r", NULL,
			     NULL, NULL, NULL);
    ret = at_open(&(out._table));
    if (ret != 0) {
      error("psi_ascii_table_input: Could not open %s", name);
      out._valid = 0;
    }
  } else {
    out._psi = psiInput(name);
    out._psi._fmt = (char*)malloc(PSI_MSG_MAX);
    ret = psi_recv(out._psi, out._psi._fmt, PSI_MSG_MAX);
    if (ret < 0) {
      error("psi_ascii_table_input: Failed to receive format string.");
      out._valid = 0;
    } else {
      out._table = ascii_table(name, "0", out._psi._fmt,
                               NULL, NULL, NULL);
    }
  }
  return out;
};

static inline
PsiAsciiTableOutput psi_ascii_table_output(const char *name, int dst_type, char *format_str) {
  PsiAsciiTableOutput out;
  int ret;
  out._valid = 1;
  out._name = name;
  out._type = dst_type;
  if (dst_type == 0) {
    out._table = ascii_table(name, "w", format_str,
			     NULL, NULL, NULL);
    ret = at_open(&(out._table));
    if (ret != 0) {
      error("psi_ascii_table_output: Could not open %s", name);
      out._valid = 0;
    } else {
      at_writeformat(out._table);
    }
  } else {
    out._psi = psiOutput(name);
    ret = psi_send(out._psi, format_str, strlen(format_str));
    if (ret != 0) {
      error("psi_ascii_table_input: Failed to receive format string.");
      out._valid = 0;
    } else {
      out._table = ascii_table(name, "0", format_str,
                               NULL, NULL, NULL);
      out._psi._fmt = format_str;
    }
  }
  return out;
};

static inline
int at_psi_send(PsiAsciiTableOutput t, char *data, int len){
  return psi_send_nolimit(t._psi, data, len);
};
  
static inline
int at_psi_recv(PsiAsciiTableInput t, char **data, int len){
  return psi_recv_nolimit(t._psi, data, len);
};

static inline
int at_send_eof(PsiAsciiTableOutput t) {
  char buf[PSI_MSG_MAX] = PSI_MSG_EOF;
  int ret = psi_send_nolimit(t._psi, buf, strlen(buf));
  return ret;
};

static inline
int recv_row(PsiAsciiTableInput t, ...) {
  int ret;
  va_list ap;
  va_start(ap, t);
  if (t._type == 0) {
    ret = at_vreadline(t._table, ap);
    va_end(ap);
  } else {
    char *buf = (char*)malloc(PSI_MSG_MAX);
    ret = psi_recv_nolimit(t._psi, &buf, PSI_MSG_MAX);
    if (ret > 0) {
      debug("recv_row(%s): psi_recv returns %d: %s", t._psi._name, ret, buf);
      if (is_eof(buf)) {
	ret = -1;
      } else {
	ret = vsscanf(buf, t._psi._fmt, ap);
	debug("vpsiRecv_nolimit(%s): vsscanf returns %d", t._psi._name, ret);
      }
    } else {
      ret = -1;
    }
    free(buf);
  }
  return ret;
};

static inline
int send_row(PsiAsciiTableOutput t, ...) {
  int ret;
  va_list ap;
  va_start(ap, t);
  if (t._type == 0) {
    ret = at_vwriteline(t._table, ap);
    va_end(ap);
  } else {
    ret = vpsiSend_nolimit(t._psi, ap);
    va_end(ap);
  }
  return ret;
};

static inline
int recv_array(PsiAsciiTableInput t, ...) {
  int ret;
  va_list ap;
  va_start(ap, t);
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
  va_end(ap);
  return ret;
};

static inline
int send_array(PsiAsciiTableOutput t, int nrows, ...) {
  int ret;
  va_list ap;
  va_start(ap, nrows);
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
  va_end(ap);
  return ret;
};

static inline
void cleanup_pati(PsiAsciiTableInput *t) {
  if ((*t)._type != 0)
    free((*t)._psi._fmt);
  at_close(&((*t)._table));
  at_cleanup(&((*t)._table));
};

static inline
void cleanup_pato(PsiAsciiTableOutput *t) {
  at_close(&((*t)._table));
  at_cleanup(&((*t)._table));
};

