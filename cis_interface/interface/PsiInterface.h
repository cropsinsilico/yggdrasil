
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

typedef struct msgbuf_t {
  long mtype;       
  char data[PSI_MSG_MAX];
} msgbuf_t;




//
// basic IO and formatted IO support
//
// usage:
//      1. one-time: create input and output channels - holding in varibales
//      2. Prepare:  Output: Format data in buffer, input: allocat buffer
//      3. Call send/receive routines:  
//          ret = psi_send(output_channel, buf, length_of_buf)
//      or
//          ret = psi_recv(input_channel, buf*, length_of_buf)

// logging support: - this is compile-time:   if PSI_DEBUG changes recompile for the new level

static inline
void psiLog(const char* fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  fprintf(stdout, "%d:", getpid());   
  vfprintf(stdout, fmt, ap);
  fprintf(stdout, "\n");
  va_end(ap);
}
#ifdef PSI_DEBUG
  #if PSI_DEBUG == INFO
    #define info psiLog
    #define debug while (0) psiLog
  #elif PSI_DEBUG == DEBUG
    #define debug psiLog
    #define info psiLog
  #else
    #define debug while (0) psiLog
    #define info while (0) psiLog
  #endif
#else
  #define debug while (0) psiLog
  #define info while (0) psiLog
#endif

typedef struct PsiInput {
  int _handle;
  const char *_name;
  char *_fmt;
} PsiInput;

typedef struct PsiOutput {
  int _handle ;
  const char *_name;
  char *_fmt;
} PsiOutput;


// track 256 channels in use- fail if re-using
// max # channels 
#define _psiTrackChannels 256
static char * _psiChannelNames[_psiTrackChannels]; 
static unsigned _psiChannelsUsed = 0;

static inline
int psi_mq(char *name, const char *yamlName){
  // Look up registered name
  char *qid = getenv(name);
  // Fail if the driver did not declare the channel
  if (qid == NULL) {
    debug("psi_mq: Channel %s not registered, model/YAML mismatch\n", yamlName);
    fprintf(stderr, "psi_mq: Channel %s not registered, model/YAML mismatch\n", yamlName);
    // Check if opposite channel exists
    char nm_opp[512];
    strcpy(nm_opp, yamlName);
    if (strcmp(name+strlen(yamlName), "_IN") == 0)
      strcat(nm_opp, "_OUT");
    else
      strcat(nm_opp, "_IN");
    qid = getenv(nm_opp);
    if (qid != NULL) {
      debug("psi_mq: Directed channel %s exists, but requested channel %s does not\n",
	    nm_opp, name);
      fprintf(stderr, "psi_msg: Directed channel %s exists, but requested channel %s does not\n",
	      nm_opp, name);
    }
    return -1;
  }
  // Fail if trying to re-use the same channel twice
  for (unsigned i =0; i < _psiChannelsUsed; i++ ){
    if (0 == strcmp(_psiChannelNames[i], name)){
      debug("ERROR: Attempt to re-use channel %s", name);
      fprintf(stderr, "ERROR: Attempt to re-use channel %s", name);
      return -1;
    }
  }
  // Fail if > _psiTrackChannels channels used
  if (_psiChannelsUsed >= _psiTrackChannels) {
    debug("ERROR: too many channels in use, max: %d\n", _psiTrackChannels);
    fprintf(stderr, "ERROR: too many channels in use, max: %d\n", _psiTrackChannels);
    return -1;
  }
  _psiChannelNames[_psiChannelsUsed++] = qid;
  int qkey = atoi(qid);
  int fid = msgget(qkey, 0600);
  return fid;
};

static inline
PsiOutput psi_output(const char *name){
  char nm[512];
  strcpy(nm, name);
  strcat(nm, "_OUT");
  PsiOutput ret;
  ret._handle = psi_mq(nm, name);
  ret._name = name;
  ret._fmt = 0;
  return ret;
};

static inline
PsiOutput psiSender(const char *name, char*fmtString){
  PsiOutput ret = psi_output(name);
  ret._fmt = fmtString;
  return ret;
};

static inline
PsiInput psi_input(const char *name){
  char nm[512];
  strcpy(nm, name);
  strcat(nm, "_IN");
  PsiInput ret;
  ret._handle =  psi_mq(nm, name);
  ret._name = name;
  ret._fmt = 0;
  return ret;
};

// TODO: why does this return an output queue?
static inline
PsiOutput psiReceiver(const char *name, char*fmtString){
  PsiOutput ret = psi_output(name);
  ret._fmt = fmtString;
  return ret;
};

static inline
int psi_output_nmsg(PsiOutput psiQ) {
  int rc;
  struct msqid_ds buf;
  int num_messages;
  rc = msgctl(psiQ._handle, IPC_STAT, &buf);
  if (rc != 0)
    return -1;
  num_messages = buf.msg_qnum;
  return num_messages;
};

static inline
int psi_input_nmsg(PsiInput psiQ) {
  int rc;
  struct msqid_ds buf;
  int num_messages;
  rc = msgctl(psiQ._handle, IPC_STAT, &buf);
  if (rc != 0)
    return -1;
  num_messages = buf.msg_qnum;
  return num_messages;
};

static inline
int psi_send(PsiOutput psiQ, char *data, int len){
  debug("psi_send(%s): %d bytes", psiQ._name, len);
  msgbuf_t t;
  t.mtype=1;
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
      debug("psi_send:  msgsend(%d, %p, %d, IPC_NOWAIT) ret(%d), errno(%d): %s", psiQ._handle, &t, len, ret, errno, strerror(errno));
      return -1;
    }
  }
  debug("psi_send(%s): returning %d", psiQ._name, ret);   
  return ret;
};

static inline
int psi_recv(PsiInput psiQ, char *data, int len){
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
      debug("psi_recv(%s): received input: %d bytes, ret=%d", psiQ._name, strlen(t.data), ret);
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

static inline
int psi_send_nolimit(PsiOutput psiQ, char *data, int len){
  debug("psi_send_nolimit(%s): %d bytes", psiQ._name, len);
  int ret = -1;
  int msgsiz = 0;
  char msg[PSI_MSG_MAX];
  sprintf(msg, "%ld", (long)(len));
  ret = psi_send(psiQ, msg, strlen(msg));
  if (ret < 0) {
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
    if (ret < 0) {
      debug("psi_send_nolimit(%s): send interupted at %d of %d bytes.",
	    psiQ._name, prev, len);
      break;
    }
    prev += msgsiz;
    debug("psi_send_nolimit(%s): %d of %d bytes sent",
	  psiQ._name, prev, len);
  }
  if (ret >= 0)
    debug("psi_send_nolimit(%s): %d bytes completed", psiQ._name, len);
  return ret;
};

static inline
int psi_recv_nolimit(PsiInput psiQ, char **data, int len0){
  debug("psi_recv_nolimit(%s)", psiQ._name);
  long len = 0;
  int ret = -1;
  int msgsiz = 0;
  char msg[PSI_MSG_MAX];
  int prev = 0;
  ret = psi_recv(psiQ, msg, PSI_MSG_MAX);
  if (ret <= 0) {
    debug("psi_recv_nolimit(%s): failed to receive payload size.", psiQ._name);
    return ret;
  }
  ret = sscanf(msg, "%ld", &len);
  if (ret != 1) {
    debug("psi_recv_nolimit(%s): failed to parse payload size (%s)", psiQ._name, msg);
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
    if (ret <= 0) {
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
  }
  return prev;
};

static inline
int vpsiSend(PsiOutput psiQ, va_list ap) {
  char buf[PSI_MSG_MAX];
  int ret = vsnprintf(buf, PSI_MSG_MAX, psiQ._fmt, ap);
  debug("vpsiSend(%s): vsnprintf returns %d", psiQ._name, ret);
  /* Unsure why passing end of string charater... */
  /* ret = psi_send(psiQ, buf, strlen(buf)+1); */
  ret = psi_send(psiQ, buf, strlen(buf));
  debug("vpsiSend(%s): psi_send returns %d", psiQ._name, ret);
  return ret;
};

static inline
int vpsiRecv(PsiInput psiQ, va_list ap) {
  char buf[PSI_MSG_MAX];
  int ret = psi_recv(psiQ, buf, PSI_MSG_MAX);
  if (ret > 0) {
    debug("vpsiRecv(%s): psi_recv returns %d: %s", psiQ._name, ret, buf);
    ret = vsscanf(buf, psiQ._fmt, ap);
    debug("vpsiRecv(%s): vsscanf returns %d", psiQ._name, ret);
  } else {
    ret = -1;
  };
  return ret;
};

static inline
int vpsiSend_nolimit(PsiOutput psiQ, va_list ap) {
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret = vsnprintf(buf, PSI_MSG_MAX, psiQ._fmt, ap);
  if (ret > PSI_MSG_MAX) {
    buf = (char*)realloc(buf, ret+1);
    ret = vsnprintf(buf, ret, psiQ._fmt, ap);
  }
  debug("vpsiSend_nolimit(%s): vsnprintf returns %d", psiQ._name, ret);
  ret = psi_send_nolimit(psiQ, buf, ret);
  debug("vpsiSend_nolimit(%s): psi_send_nolimit returns %d", psiQ._name, ret);
  free(buf);
  return ret;
};

static inline
int vpsiRecv_nolimit(PsiInput psiQ, va_list ap) {
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret = psi_recv_nolimit(psiQ, &buf, PSI_MSG_MAX);
  if (ret > 0) {
    debug("vpsiRecv_nolimit(%s): psi_recv returns %d: %s", psiQ._name, ret, buf);
    ret = vsscanf(buf, psiQ._fmt, ap);
    debug("vpsiRecv_nolimit(%s): vsscanf returns %d", psiQ._name, ret);
  } else {
    ret = -1;
  }
  free(buf);
  return ret;
};

static inline
int psiSend(PsiOutput psiQ, ...){
  va_list ap;
  va_start(ap, psiQ._fmt);
  int ret = vpsiSend(psiQ, ap);
  va_end(ap);
  return ret;
};

static inline
int psiRecv(PsiInput psiQ, ...){
  va_list ap;
  va_start(ap, psiQ._fmt);
  int ret = vpsiRecv(psiQ, ap);
  va_end(ap);
  return ret;
};


//
// all-in-one send/recv/rpc using format strings like printf
//  creates channel on first call, reuses on subsequent calls
//  returns number of vars sent/received
// 
// Usage: 
//  ret = psi_sendVars(channel_name, format_string,  var1, var2, ...)
//  ret = psi_recvVars(channel_name, format_string, &var1, &var2, ...)
// Example:
//  ret - psi_send("myOutput", "%f %f %d", temp, percentComplete, iteration)
//  
// Usage: pass input and output channel names, a format string  of input and output formats separated by :,
// the output args to send, and the inputs to receive
// The first call initializes the static pseudo-globals
// Probably needs better error reporting to the caller
// See example below

typedef struct psiRpc_t {
  PsiInput _input;
  PsiOutput _output;
  char *_inFmt;
  char *_outFmt;
} psiRpc_t;

// args in order of use:   client - outputs, then inputs.   server: inputs then outputs
static inline 
psiRpc_t psiRpcClient(const char *outName, char *outFormat,
		      const char *inName, char *inFormat){
  psiRpc_t rpc;
  rpc._inFmt = inFormat;
  rpc._outFmt = outFormat;
  rpc._input = psi_input(inName);
  rpc._output = psi_output(outName);
  return rpc;
};

static inline 
psiRpc_t psiRpcServer(const char *inName, char *inFormat,
		      const char *outName, char *outFormat){
  psiRpc_t rpc;
  rpc._inFmt = inFormat;
  rpc._outFmt = outFormat;
  rpc._input = psi_input(inName);
  rpc._output = psi_output(outName);
  return rpc;
};

static inline 
psiRpc_t psiRpc(const char *outName, char *outFormat,
		const char *inName, char *inFormat){
  psiRpc_t rpc;
  rpc._inFmt = inFormat;
  rpc._outFmt = outFormat;
  rpc._input = psi_input(inName);
  rpc._output = psi_output(outName);
  return rpc;
};

static inline
int rpcRecv(psiRpc_t rpc, ...){
  debug("rpcRecv(%s)\n", rpc._input._name);
  char *buf = (char*)malloc(PSI_MSG_MAX);
  va_list ap;
  va_start(ap, rpc);
  int ret = psi_recv_nolimit(rpc._input, &buf, PSI_MSG_MAX);
  debug("rpcRecv(%s): psi_recv returned %d\n", rpc._input._name, ret);
  if (ret < 0) {
    debug("rpcRecv: receive error: %d\n", ret);
    free(buf);
    return -1;
  }
  
  // unpack the message
  ret = vsscanf(buf, rpc._inFmt, ap);
  debug("rpcRecv(%s): vsscanf returned %d\n", rpc._input._name, ret);
  va_end(ap);
  free(buf);
  return (0);
};

static inline
int rpcSend(psiRpc_t rpc, ...){
  char *buf = (char*)malloc(PSI_MSG_MAX);
  va_list ap;
  va_start(ap, rpc);
  int ret = vsnprintf(buf, PSI_MSG_MAX, rpc._outFmt, ap);
  debug("rpcSend(%s): vsnprintf returned %d\n", rpc._output._name, ret);
  ret = psi_send_nolimit(rpc._output, buf, strlen(buf));
  debug("rpcSend(%s): psi_send returned %d\n", rpc._output._name, ret);
  
  if (ret != 0){
    debug("rpcSend(%s): send error %d\n", rpc._output._name, ret);
    free(buf);
    return -1;
  }
  va_end(ap);
  free(buf);
  return (0);
};


static inline
int rpcCall(psiRpc_t rpc,  ...){
  // setup - static variables persist across calls
  char *buf = (char*)malloc(PSI_MSG_MAX);
  int ret; // always check return values
  
  // pack the args and call
  va_list ap;
  va_list op;
  va_start(ap, rpc);
  ret = vsnprintf(buf, PSI_MSG_MAX, rpc._outFmt, ap);
  va_copy(op, ap);
  ret = psi_send_nolimit(rpc._output, buf, strlen(buf));
  if (ret != 0){
    debug("rpcCall: psi_send error: %s\n", strerror(errno));
    free(buf);
    return -1;
  }
  
  // receive the message
  ret = psi_recv_nolimit(rpc._input, &buf, PSI_MSG_MAX);
  if (ret < 0) {
    printf("psi_recv error: ret %d: %s\n", ret, strerror(errno));
    free(buf);
    return -1;
  }
  
  // unpack the messages
  ret = vsscanf(buf, rpc._inFmt, op);
  debug("rpcCall: return_temporary_buffer %d\n", ret);
  va_end(ap);
  va_end(op);
  
  free(buf);
  return 0;
};

// Specialized functions for passing file rows back and forth
typedef struct PsiAsciiFileOutput {
  const char *_name;
  int _type;
  AsciiFile _file;
  PsiOutput _psi;
} PsiAsciiFileOutput;

typedef struct PsiAsciiFileInput {
  const char *_name;
  int _type;
  AsciiFile _file;
  PsiInput _psi;
} PsiAsciiFileInput;

static inline
PsiAsciiFileInput psi_ascii_file_input(const char *name, int src_type) {
  PsiAsciiFileInput out;
  int ret;
  out._name = name;
  out._type = src_type;
  if (src_type == 0) { // Direct file interface
    out._file = ascii_file(name, "r", NULL, NULL);
    ret = af_open(&(out._file));
  } else {
    out._psi = psi_input(name);
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
  if (dst_type == 0) {
    out._file = ascii_file(name, "w", NULL, NULL);
    ret = af_open(&(out._file));
  } else {
    out._psi = psi_output(name);
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


// Specialized functions for passing table rows back and forth
typedef struct PsiAsciiTableOutput {
  const char *_name;
  int _type;
  AsciiTable _table;
  PsiOutput _psi;
} PsiAsciiTableOutput;

typedef struct PsiAsciiTableInput {
  const char *_name;
  int _type;
  AsciiTable _table;
  PsiInput _psi;
} PsiAsciiTableInput;

static inline
PsiAsciiTableInput psi_ascii_table_input(const char *name, int src_type) {
  PsiAsciiTableInput out;
  int ret;
  out._name = name;
  out._type = src_type;
  if (src_type == 0) { // Direct file interface
    out._table = ascii_table(name, "r", NULL,
			     NULL, NULL, NULL);
    ret = at_open(&(out._table));
  } else {
    out._psi = psi_input(name);
    out._psi._fmt = (char*)malloc(PSI_MSG_MAX);
    ret = psi_recv(out._psi, out._psi._fmt, PSI_MSG_MAX);
    /* printf("%s\n", name); */
    /* printf("%s\n", out._psi._fmt); */
    out._table = ascii_table(name, "0", out._psi._fmt,
			     NULL, NULL, NULL);
  }
  return out;
};

static inline
PsiAsciiTableOutput psi_ascii_table_output(const char *name, int dst_type, char *format_str) {
  PsiAsciiTableOutput out;
  int ret;
  out._name = name;
  out._type = dst_type;
  if (dst_type == 0) {
    out._table = ascii_table(name, "w", format_str,
			     NULL, NULL, NULL);
    ret = at_open(&(out._table));
    at_writeformat(out._table);
  } else {
    out._psi = psi_output(name);
    ret = psi_send(out._psi, format_str, strlen(format_str));
    /* printf("%s\n", name); */
    out._table = ascii_table(name, "0", format_str,
			     NULL, NULL, NULL);
    out._psi._fmt = format_str;
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

