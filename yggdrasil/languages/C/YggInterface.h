/*! @brief Flag for checking if YggInterface.h has already been included.*/
#ifndef YGGINTERFACE_H_
#define YGGINTERFACE_H_

#include "../tools.h"
#include "../datatypes/datatypes.h"
#include "../communication/communication.h"
#include "../dataio/AsciiFile.h"
#include "../dataio/AsciiTable.h"

#ifdef __cplusplus /* If this is a C++ compiler, use C linkage */
extern "C" {
#endif

/*! @brief Aliases to preserve names of original structures. */
#define yggOutput_t comm_t*
#define yggInput_t comm_t*
#define ygg_free free_comm
#define yggComm init_comm

//==============================================================================
/*!
  Basic IO 

  Output Usage:
      1. One-time: Create output channel (store in named variables)
            yggOutput_t output_channel = yggOutput("out_name");
      2. Prepare: Format data to a character array buffer.
            char buffer[YGG_MSG_BUF]; 
	    sprintf(buffer, "a=%d, b=%d", 1, 2);
      3. Send:
	    ret = ygg_send(output_channel, buffer, strlen(buffer));

  Input Usage:
      1. One-time: Create output channel (store in named variables)
            yggInput_t input_channel = yggInput("in_name");
      2. Prepare: Allocate a character array buffer.
            char buffer[YGG_MSG_BUF];
      3. Receive:
            int ret = ygg_recv(input_channel, buffer, YGG_MSG_BUF);
*/
//==============================================================================

/*!
  @brief Constructor for yggOutput_t structure with explicit data type.
  Create a yggOutput_t structure based on a provided name that is used to
  locate a particular comm address stored in the environment variable name
  and a structure definining the datatype of outgoing messages for the queue.
  @param[in] name constant character pointer to name of queue.
  @param[in] datatype Pointer to a dtype_t data structure containing type informaiton.
  @returns yggOutput_t output queue structure.
 */
static inline
yggOutput_t yggOutputType(const char *name, dtype_t *datatype) {
  return init_comm(name, "send", _default_comm, datatype);
};

/*!
  @brief Constructor for yggInput_t structure with explicit data type.
  Create a yggInput_t structure based on a provided name that is used to
  locate a particular comm address stored in the environment variable name and
  a structure defining the expected datatype of received messages.
  @param[in] name constant character pointer to name of queue.
  @param[in] datatype Pointer to a dtype_t data structure containing type informaiton.
  @returns yggInput_t input queue structure.
 */
static inline
yggInput_t yggInputType(const char *name, dtype_t *datatype) {
  return init_comm(name, "recv", _default_comm, datatype);
};
  
/*!
  @brief Constructor for yggOutput_t structure with format.
  Create a yggOutput_t structure based on a provided name that is used to
  locate a particular comm address stored in the environment variable name
  and a format string that can be used to format arguments into outgoing 
  messages for the queue.   
  @param[in] name constant character pointer to name of queue.
  @param[in] fmtString character pointer to format string.
  @returns yggOutput_t output queue structure.
 */
static inline
yggOutput_t yggOutputFmt(const char *name, const char *fmtString){
  return init_comm_format(name, "send", _default_comm, fmtString, 0);
};

/*!
  @brief Constructor for yggInput_t structure with format.
  Create a yggInput_t structure based on a provided name that is used to
  locate a particular comm address stored in the environment variable name and
  a format stirng that can be used to extract arguments from received messages.
  @param[in] name constant character pointer to name of queue.
  @param[in] fmtString character pointer to format string.
  @returns yggInput_t input queue structure.
 */
static inline
yggInput_t yggInputFmt(const char *name, const char *fmtString){
  return init_comm_format(name, "recv", _default_comm, fmtString, 0);
};

/*!
  @brief Constructor for yggOutput_t output structure.
  Create a yggOutput_t structure based on a provided name that is used to
  locate a particular comm address stored in the environment variable name.
  @param[in] name constant character pointer to name of queue.
  @returns yggOutput_t output queue structure.
 */
static inline
yggOutput_t yggOutput(const char *name) {
  yggOutput_t ret = yggOutputFmt(name, NULL);
  return ret;
};

/*!
  @brief Constructor for yggInput_t structure.
  Create a yggInput_t structure based on a provided name that is used to
  locate a particular comm address stored in the environment variable name.
  @param[in] name constant character pointer to name of queue.
  @returns yggInput_t input queue structure.
 */
static inline
yggInput_t yggInput(const char *name){
  yggInput_t ret = yggInputFmt(name, NULL);
  return ret;
};

/*!
  @brief Send a message to an output queue.
  Send a message smaller than YGG_MSG_MAX bytes to an output queue. If the
  message is larger, it will not be sent.
  @param[in] yggQ yggOutput_t structure that queue should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int ygg_send(const yggOutput_t yggQ, const char *data, const size_t len) {
  int nargs_exp = 2;
  int nargs_used = commSend(yggQ, data, len);
  if (nargs_used == nargs_exp) {
    return 0;
  } else {
    ygglog_error("ygg_send(%s): %d arguments expected, but %d used.",
		 nargs_exp, nargs_used);
    return -1;
  }
};

/*!
  @brief Send EOF message to the output queue.
  @param[in] yggQ yggOutput_t structure that message should be sent to.
  @returns int 0 if send successfull, -1 if unsuccessful.
*/
static inline
int ygg_send_eof(const yggOutput_t yggQ) {
  return comm_send_eof(yggQ);
};

/*!
  @brief Receive a message from an input queue.
  Receive a message smaller than YGG_MSG_MAX bytes from an input queue.
  @param[in] yggQ yggOutput_t structure that message should be sent to.
  @param[out] data character pointer to allocated buffer where the message
  should be saved.
  @param[in] len const size_t length of the allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int ygg_recv(yggInput_t yggQ, char *data, const size_t len){
  char* temp = NULL;
  int ret = -1;
  size_t len_used = len;
  int nargs_exp = 2;
  int nargs_used = commRecv(yggQ, data, &len_used);
  if (nargs_used == nargs_exp) {
    ret = (int)len_used;
  } else if (nargs_used >= 0) {
    ygglog_error("ygg_recv: nargs_used = %d, nargs_exp = %d", nargs_used, nargs_exp);
    ret = -1;
  } else {
    ret = nargs_used;
  }
  if (temp != NULL)
    free(temp);
  return ret;
};

/*!
  @brief Send a large message to an output queue.
  Send a message larger than YGG_MSG_MAX bytes to an output queue by breaking
  it up between several smaller messages and sending initial message with the
  size of the message that should be expected. Must be partnered with
  ygg_recv_nolimit for communication to make sense.
  @param[in] yggQ yggOutput_t structure that message should be sent to.
  @param[in] data character pointer to message that should be sent.
  @param[in] len size_t length of message to be sent.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
static inline
int ygg_send_nolimit(const yggOutput_t yggQ, const char *data, const size_t len){
  return ygg_send(yggQ, data, len);
};

/*!
  @brief Send EOF message to the output queue.
  @param[in] yggQ yggOutput_t structure that message should be sent to.
  @returns int 0 if send successfull, -1 if unsuccessful.
*/
static inline
int ygg_send_nolimit_eof(const yggOutput_t yggQ) {
  return comm_send_nolimit_eof(yggQ);
};

/*!
  @brief Receive a large message from an input queue.
  Receive a message larger than YGG_MSG_MAX bytes from an input queue by
  receiving it in parts. This expects the first message to be the size of
  the total message.
  @param[in] yggQ yggOutput_t structure that message should be sent to.
  @param[out] data character pointer to pointer for allocated buffer where the
  message should be stored. A pointer to a pointer is used so that the buffer
  may be reallocated as necessary for the incoming message.
  @param[in] len size_t length of the initial allocated message buffer in bytes.
  @returns int -1 if message could not be received. Length of the received
  message if message was received.
 */
static inline
int ygg_recv_nolimit(yggInput_t yggQ, char **data, const size_t len){
  UNUSED(len);
  int ret = -1;
  size_t len_used = 0; // Send 0 to indicate data can be realloced
  int nargs_used = commRecvRealloc(yggQ, data, &len_used);
  int nargs_exp = 2;
  if (nargs_used == nargs_exp) {
    ret = (int)len_used;
  } else if (nargs_used >= 0) {
    ygglog_error("ygg_recv_nolimit: nargs_used = %d, nargs_exp = %d", nargs_used, nargs_exp);
    ret = -1;
  } else {
    ret = nargs_used;
  }
  return ret;
};


//==============================================================================
/*!
  Formatted IO 

  Output Usage:
      1. One-time: Create output channel with format specifier.
            yggOutput_t output_channel = yggOutputFmt("out_name", "a=%d, b=%d");
      2. Send:
	    ret = yggSend(output_channel, 1, 2);
      3. Free:
            ygg_free(&output_channel);

  Input Usage:
      1. One-time: Create output channel with format specifier.
            yggInput_t input_channel = yggInput("in_name", "a=%d, b=%d");
      2. Prepare: Allocate space for recovered variables.
            int a, b;
      3. Receive:
            int ret = yggRecv(input_channel, &a, &b);
*/
//==============================================================================

/*!
  @brief Send arguments as a small formatted message to an output queue.
  Use the format string to create a message from the input arguments that
  is then sent to the specified output queue. If the message is larger than
  YGG_MSG_MAX or cannot be encoded, it will not be sent.  
  @param[in] yggQ yggOutput_t structure that queue should be sent to.
  @param[in] ... arguments to be formatted into a message using sprintf.
  @returns int 0 if send succesfull, -1 if send unsuccessful.
 */
#define yggSend commSend

/*!
  @brief Assign arguments by receiving and parsing a message from an input queue.
  Receive a message smaller than YGG_MSG_MAX bytes from an input queue and parse
  it using the associated format string.
  @param[in] yggQ yggOutput_t structure that message should be sent to.
  @param[out] ... arguments that should be assigned by parsing the
  received message using sscanf. As these are being assigned, they should be
  pointers to memory that has already been allocated.
  @returns int -1 if message could not be received or could not be parsed.
  Length of the received message if message was received and parsed.
 */
#define yggRecv commRecv
#define yggRecvRealloc commRecvRealloc


/*! @brief Definitions for symmetry, but there is no difference. */
#define vyggSend vcommSend
#define vyggRecv vcommRecv
#define vyggSend_nolimit vcommSend
#define vyggRecv_nolimit vcommRecv
#define yggSend_nolimit commSend
#define yggRecv_nolimit commRecv

 
//==============================================================================
/*!
  Remote Procedure Call (RPC) IO 

  Handle IO case of a server receiving input from clients, performing some
  calculation, and then sending a response back to the client.

  Server Usage:
      1. One-time: Create server channels with format specifiers for input and
         output.
            yggRpc_t srv = yggRpcServer("srv_name", "%d", "%d %d");
      2. Prepare: Allocate space for recovered variables from request.
            int a;
      3. Receive request:
            int ret = rpcRecv(srv, &a);
      4. Process: Do tasks the server should do with input to produce output.
            int b = 2*a;
	    int c = 3*a;
      5. Send response:
	    ret = rpcSend(srv, b, c);

  Client Usage:
      1. One-time: Create client channels to desired server with format
         specifiers for output and input (should be the same arguments as for
	 the server except for name).
	    yggRpc_t cli = yggRpcClient("cli_name", "%d", "%d %d"); 
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
#define yggRpc_t comm_t*

/*!
  @brief Constructor for client side RPC structure.
  Creates an instance of yggRpc_t with provided information.  
  @param[in] name constant character pointer to name for queues.
  @param[in] outFormat character pointer to format that should be used for
  formatting output.
  @param[in] inFormat character pointer to format that should be used for
  parsing input.
  @return yggRpc_t structure with provided info.
 */
static inline
comm_t* yggRpcClient(const char *name, const char *outFormat, const char *inFormat){
  return init_comm_format(name, outFormat, CLIENT_COMM, inFormat, 0);
};

/*!
  @brief Constructor for server side RPC structure.
  Creates an instance of yggRpc_t with provided information.  
  @param[in] name constant character pointer to name for queues.
  @param[in] inFormat character pointer to format that should be used for
  parsing input.
  @param[in] outFormat character pointer to format that should be used for
  formatting output.
  @return yggRpc_t structure with provided info.
 */
static inline
comm_t* yggRpcServer(const char *name, const char *inFormat, const char *outFormat){
  return init_comm_format(name, inFormat, SERVER_COMM, outFormat, 0);
};

/*!
  @brief Format and send a message to an RPC output queue.
  Format provided arguments list using the output queue format string and
  then sends it to the output queue under the assumption that it is larger
  than the maximum message size.
  @param[in] rpc yggRpc_t structure with RPC information.
  @param[in] ap va_list variable list of arguments for formatting.
  @return integer specifying if the send was succesful. Values >= 0 indicate
  success.
 */
#define vrpcSend vcommSend

/*!
  @brief Receive and parse a message from an RPC input queue.
  Receive a message from the input queue under the assumption that it is
  larger than the maximum message size. Then parse the message using the
  input queue format string to extract parameters and assign them to the
  arguments.
  @param[in] rpc yggRpc_t structure with RPC information.
  @param[in] nargs int Number of arguments contained in ap.
  @param[out] ap va_list variable list of arguments that should be assigned
  parameters extracted using the format string. Since these will be assigned,
  they should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
*/
#define vrpcRecv(rpc, nargs, ap) vcommRecv(rpc, 0, nargs, ap)
#define vrpcRecvRealloc(rpc, nargs, ap) vcommRecv(rpc, 1, nargs, ap)

/*!
  @brief Format and send a message to an RPC output queue.
  Format provided arguments using the output queue format string and
  then sends it to the output queue under the assumption that it is larger
  than the maximum message size.
  @param[in] rpc yggRpc_t structure with RPC information.
  @param[in] ... arguments for formatting.
  @return integer specifying if the send was succesful. Values >= 0 indicate
  success.
 */
#define rpcSend commSend

/*!
  @brief Receive and parse a message from an RPC input queue.
  Receive a message from the input queue under the assumption that it is
  larger than the maximum message size. Then parse the message using the
  input queue format string to extract parameters and assign them to the
  arguments.
  @param[in] rpc yggRpc_t structure with RPC information.
  @param[out] ... mixed arguments that should be assigned parameters extracted
  using the format string. Since these will be assigned, they should be
  pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
*/
#define rpcRecv commRecv
#define rpcRecvRealloc commRecvRealloc

/*!
  @brief Send request to an RPC server from the client and wait for a response.
  Format arguments using the output queue format string, send the message to the
  output queue, receive a response from the input queue, and assign arguments
  from the message using the input queue format string to parse it.
  @param[in] rpc yggRpc_t structure with RPC information.
  @param[in] allow_realloc int If 1, output arguments are assumed to be pointers
  to pointers such that they can be reallocated as necessary to receive incoming
  data. If 0, output arguments are assumed to be preallocated.
  @param[in] nargs size_t Number of arguments contained in ap including both
  input and output arguments.
  @param[in,out] ap va_list mixed arguments that include those that should be
  formatted using the output format string, followed by those that should be
  assigned parameters extracted using the input format string. These that will
  be assigned should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
 */
static inline
int vrpcCallBase(yggRpc_t rpc, const int allow_realloc,
		 size_t nargs, va_list_t ap) {
  int sret, rret;
  rret = 0;

  // Create copy for receiving
  va_list_t op;
  va_copy(op.va, ap.va);
  
  // pack the args and call
  comm_t *send_comm = (comm_t*)(rpc->handle);
  size_t send_nargs = nargs_exp_dtype(send_comm->datatype);
  sret = vcommSend(rpc, send_nargs, ap);
  if (sret < 0) {
    ygglog_error("vrpcCall: vcommSend error: ret %d: %s", sret, strerror(errno));
    return -1;
  }

  // Advance through sent arguments
  ygglog_debug("vrpcCall: Used %d arguments in send", sret);
  int i;
  for (i = 0; i < sret; i++) {
    va_arg(op.va, void*);
  }
  nargs = nargs - sret;

  // unpack the messages into the remaining variable arguments
  // va_list_t op;
  // va_copy(op.va, ap.va);
  rret = vcommRecv(rpc, allow_realloc, nargs, op);
  va_end(op.va);
  
  return rret;
};
#define vrpcCall(rpc, nargs, ap) vrpcCallBase(rpc, 0, nargs, ap)
#define vrpcCallRealloc(rpc, nargs, ap) vrpcCallBase(rpc, 1, nargs, ap)

/*!
  @brief Send request to an RPC server from the client and wait for a response.
  Format arguments using the output queue format string, send the message to the
  output queue, receive a response from the input queue, and assign arguments
  from the message using the input queue format string to parse it.
  @param[in] rpc yggRpc_t structure with RPC information.
  @param[in] allow_realloc int If 1, output arguments are assumed to be pointers
  to pointers such that they can be reallocated as necessary to receive incoming
  data. If 0, output arguments are assumed to be preallocated.
  @param[in] nargs size_t Number of arguments contained in ap including both
  input and output arguments.
  @param[in,out] ... mixed arguments that include those that should be
  formatted using the output format string, followed by those that should be
  assigned parameters extracted using the input format string. These that will
  be assigned should be pointers to memory that has already been allocated.
  @return integer specifying if the receive was succesful. Values >= 0 indicate
  success.
 */
static inline
int nrpcCallBase(yggRpc_t rpc, const int allow_realloc, size_t nargs, ...){
  int ret;
  va_list_t ap;
  va_start(ap.va, nargs);
  ret = vrpcCallBase(rpc, allow_realloc, nargs, ap);
  va_end(ap.va);
  return ret;
};
#define rpcCall(rpc, ...) nrpcCallBase(rpc, 0, COUNT_VARARGS(__VA_ARGS__), __VA_ARGS__)
#define rpcCallRealloc(rpc, ...) nrpcCallBase(rpc, 1, COUNT_VARARGS(__VA_ARGS__), __VA_ARGS__)


//==============================================================================
/*!
  File IO

  Handle I/O from/to a file line by line.

  Input Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fin = yggAsciiFileInput("file_channel");
      2. Prepare: Get pointer for line.
            char *line;
      3. Receive each line, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &line); // line will be realloced to fit message
	      // Do something with the line
	    }
      4. Cleanup. Call functions to deallocate structures.
            free(line);

  Output Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggAsciiFileOutput("file_channel");
      2. Send lines to the file. If return value is not 0, the send was not
          succesfull.
            int ret;
	    ret = yggSend(fin, "Line 1\n");
	    ret = yggSend(fout, "Line 1\n");
	    ret = yggSend(fout, "Line 2\n");

*/
//==============================================================================

/*! @brief Definitions for file sturctures. */
#define yggAsciiFileInput_t comm_t*
#define yggAsciiFileOutput_t comm_t*

/*!
  @brief Constructor for AsciiFile output comm to channel.
  @param[in] name constant character pointer to name of an output channel.
  @returns comm_t* for line-by-line output to a file or channel.
 */
static inline
comm_t* yggAsciiFileOutput(const char *name) {
  comm_t* out = init_comm(name, "send", _default_comm, NULL);
  return out;
};

/*!
  @brief Constructor for AsciiFile input comm from channel.
  @param[in] name constant character pointer to name of an input channel.
  @returns comm_t* for line-by-line input from a file or channel.
 */
static inline
comm_t* yggAsciiFileInput(const char *name) {
  comm_t* out = init_comm(name, "recv", _default_comm, NULL);
  return out;
};


//==============================================================================
/*!
  Table IO

  Handle I/O from/to an ASCII table either line-by-line or as an array.

  Row-by-Row
  ==========

  Input by Row Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fin = yggAsciiTableInput("file_channel");
      2. Prepare: Allocate space for variables in row (the format in this
         example is "%5s %d %f\n" like the output example below).
	    char a[5];
	    int b;
	    double c;
      3. Receive each row, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &a, &b, &c);
	      // Do something with the row
	    }

  Output by Row Usage:
      1. One-time: Create file interface by providing a channel name and a
         format string for rows.
	    comm_t* fout = yggAsciiTableOutput("file_channel", "%5s %d %f\n");
      2. Send rows to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    ret = yggSend(fout, "one", 1, 1.0);
	    ret = yggSend(fout, "two", 2, 2.0);

  Array
  =====

  Input by Array Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fin = yggAsciiArrayInput("file_channel");
      2. Prepare: Declare pointers for table columns (they will be allocated by
         the interface once the number of rows is known).
	    char *aCol;
	    int *bCol;
	    double *cCol;
      3. Receive entire table as columns. Return value will be the number of
         elements in each column (the number of table rows). Negative values
	 indicate errors.
            int ret = yggRecv(fin, &a, &b, &c);
      4. Cleanup. Call functions to deallocate structures.
            free(a);
            free(b);
            free(c);

  Output by Array Usage:
      1. One-time: Create file interface by providing a channel name and a
         format string for rows.
	    comm_t* fout = yggAsciiArrayOutput("file_channel", "%5s %d %f\n");
      2. Send columns to the file by providing pointers (or arrays). Formatting
         is handled by the interface. If return value is not 0, the send was not
	 succesful.
	    char aCol[] = {"one  ", "two  ", "three"}; \\ Each str is of len 5
	    int bCol[3] = {1, 2, 3};
	    float cCol[3] = {1.0, 2.0, 3.0};
            int ret = yggSend(fout, a, b, c);

*/
//==============================================================================

/*! @brief Definitions for table sturctures. */
#define yggAsciiTableInput_t comm_t*
#define yggAsciiTableOutput_t comm_t*
#define yggAsciiArrayInput_t comm_t*
#define yggAsciiArrayOutput_t comm_t*

/*!
  @brief Constructor for table output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @param[in] format_str character pointer to format string that should be used
  to format rows into table lines.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggAsciiTableOutput(const char *name, const char *format_str) {
  return init_comm_format(name, "send", _default_comm, format_str, 0);
};

/*!
  @brief Constructor for AsciiTable input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggAsciiTableInput(const char *name) {
  return init_comm(name, "recv", _default_comm, NULL);
};

/*!
  @brief Constructor for table output comm with array output.
  @param[in] name constant character pointer to an output channel name.
  @param[in] format_str character pointer to format string that should be used
  to format rows into table lines.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggAsciiArrayOutput(const char *name, const char *format_str) {
  return init_comm_format(name, "send", _default_comm, format_str, 1);
};

/*!
  @brief Constructor for AsciiTable input comm with array input.
  @param[in] name constant character pointer to an input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggAsciiArrayInput(const char *name) {
  return yggAsciiTableInput(name);
};


//==============================================================================
/*!
  Ply IO

  Handle I/O from/to a Ply file.

  Input Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fin = yggPlyInput("file_channel");  // channel
      2. Prepare: Allocate ply structure.
            ply_t p;
      3. Receive each structure, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &p);
	      // Do something with the ply structure
	    }

  Output by Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggPlyOutput("file_channel");  // channel
      2. Send structure to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    ply_t p;
	    // Populate the structure
	    ret = yggSend(fout, p);
	    ret = yggSend(fout, p);

*/
//==============================================================================

/*! @brief Definitions for ply structures. */
#define yggPlyInput_t comm_t*
#define yggPlyOutput_t comm_t*

/*!
  @brief Constructor for ply output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggPlyOutput(const char *name) {
  comm_t* out = init_comm(name, "send", _default_comm, create_dtype_ply(false));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

/*!
  @brief Constructor for ply input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggPlyInput(const char *name) {
  return init_comm(name, "recv", _default_comm, NULL);
};


//==============================================================================
/*!
  Obj IO

  Handle I/O from/to a Obj file.

  Input Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fin = yggObjInput("file_channel");  // channel
      2. Prepare: Allocate obj structure.
            obj_t p;
      3. Receive each structure, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &p);
	      // Do something with the obj structure
	    }

  Output by Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggObjOutput("file_channel");  // channel
      2. Send structure to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    obj_t p;
	    // Populate the structure
	    ret = yggSend(fout, p);
	    ret = yggSend(fout, p);

*/
//==============================================================================

/*! @brief Definitions for obj structures. */
#define yggObjInput_t comm_t*
#define yggObjOutput_t comm_t*

/*!
  @brief Constructor for obj output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggObjOutput(const char *name) {
  comm_t* out = init_comm(name, "send", _default_comm, create_dtype_obj(false));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

/*!
  @brief Constructor for obj input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggObjInput(const char *name) {
  return init_comm(name, "recv", _default_comm, NULL);
};


//==============================================================================
/*!
  Generic object I/O.

  Handle I/O from/to a generic object.

  Input Usage:
      1. One-time: Create interface by providing a channel name.
	    comm_t* fin = yggGenericInput("file_channel");  // channel
      2. Prepare: Allocate generic structure.
            generic_t p;
      3. Receive each structure, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &p);
	      // Do something with the generic structure
	    }

  Output by Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggGenericOutput("file_channel");  // channel
      2. Send structure to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    generic_t p;
	    // Populate the structure
	    ret = yggSend(fout, p);

*/
//==============================================================================

/*!
  @brief Constructor for generic output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggGenericOutput(const char *name) {
  return init_comm(name, "send", _default_comm, create_dtype_empty(true));
};

/*!
  @brief Constructor for generic input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggGenericInput(const char *name) {
  return init_comm(name, "recv", _default_comm, create_dtype_empty(true));
};

  
//==============================================================================
/*!
  Generic object I/O of any type.

  Handle I/O from/to a generic object of any type.

  Input Usage:
      1. One-time: Create interface by providing a channel name.
	    comm_t* fin = yggAnyInput("file_channel");  // channel
      2. Prepare: Allocate generic structure.
            generic_t p;
      3. Receive each structure, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &p);
	      // Do something with the generic structure
	    }

  Output by Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggAnyOutput("file_channel");  // channel
      2. Send structure to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    generic_t p;
	    // Populate the structure
	    ret = yggSend(fout, p);

*/
//==============================================================================

/*!
  @brief Constructor for generic output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggAnyOutput(const char *name) {
  comm_t* out = init_comm(name, "send", _default_comm, create_dtype_any(true));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

/*!
  @brief Constructor for generic input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggAnyInput(const char *name) {
  comm_t* out = init_comm(name, "recv", _default_comm, create_dtype_any(true));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

  
//==============================================================================
/*!
  JSON array IO

  Handle I/O from/to a JSON array.

  Input Usage:
      1. One-time: Create interface by providing a channel name.
	    comm_t* fin = yggJSONArrayInput("file_channel");  // channel
      2. Prepare: Allocate vector structure.
            json_array_t p;
      3. Receive each structure, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &p);
	      // Do something with the vector structure
	    }

  Output by Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggJSONArrayOutput("file_channel");  // channel
      2. Send structure to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    json_array_t p;
	    // Populate the structure
	    ret = yggSend(fout, p);

*/
//==============================================================================

/*!
  @brief Constructor for vector output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggJSONArrayOutput(const char *name) {
  comm_t* out = init_comm(name, "send", _default_comm, create_dtype_json_array(0, NULL, true));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

/*!
  @brief Constructor for vector input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggJSONArrayInput(const char *name) {
  comm_t* out = init_comm(name, "recv", _default_comm, create_dtype_json_array(0, NULL, true));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

#define yggVectorOutput yggJSONArrayOutput
#define yggVectorInput yggJSONArrayInput
  

//==============================================================================
/*!
  JSON object IO

  Handle I/O from/to a JSON object.

  Input Usage:
      1. One-time: Create interface by providing a channel name.
	    comm_t* fin = yggJSONObjectInput("file_channel");  // channel
      2. Prepare: Allocate map structure.
            json_object_t p;
      3. Receive each structure, terminating when receive returns -1 (EOF or channel
         closed).
	    int ret = 1;
	    while (ret > 0) {
	      ret = yggRecv(fin, &p);
	      // Do something with the map structure
	    }

  Output by Usage:
      1. One-time: Create file interface by providing a channel name.
	    comm_t* fout = yggJSONObjectOutput("file_channel");  // channel
      2. Send structure to the file by providing entries. Formatting is handled by
         the interface. If return value is not 0, the send was not succesful.
            int ret;
	    json_object_t p;
	    // Populate the structure
	    ret = yggSend(fout, p);

*/
//==============================================================================

/*!
  @brief Constructor for map output comm to an output channel.
  @param[in] name constant character pointer to output channel name.
  @returns comm_t* output structure.
 */
static inline
comm_t* yggJSONObjectOutput(const char *name) {
  comm_t* out = init_comm(name, "send", _default_comm, create_dtype_json_object(0, NULL, NULL, true));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

/*!
  @brief Constructor for map input comm from an input channel.
  @param[in] name constant character pointer to input channel name.
  @returns comm_t* input structure.
 */
static inline
comm_t* yggJSONObjectInput(const char *name) {
  comm_t* out = init_comm(name, "recv", _default_comm, create_dtype_json_object(0, NULL, NULL, true));
  if ((out->valid) && (out->datatype->obj == NULL)) {
    out->valid = 0;
  }
  return out;
};

#define yggMapOutput yggJSONObjectOutput
#define yggMapInput yggJSONObjectInput


#ifdef __cplusplus /* If this is a C++ compiler, end C linkage */
}
#endif

#endif /*YGGINTERFACE_H_*/
