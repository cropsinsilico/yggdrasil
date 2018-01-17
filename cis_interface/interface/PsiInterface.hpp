extern "C" {
#include "PsiInterface.h"
};

/*! @brief Flag for checking if PsiInterface.hpp has already been included.*/
#ifndef CISINTERFACE_HPP_
#define CISINTERFACE_HPP_

/*!
  @brief C++ interface to cisInput_t functionality.

  The CisInput class is a basic wrapper around the C cisInput_t
  structure and associated functions from the PsiInterface.h header.
  It provides the user with C++ style access to basic input via
  an IPC queue.
 */
class CisInput {
  cisInput_t _pi;
public:

  /*!
    @brief Constructor for CisInput.
    @param[in] name constant character pointer to name of input queue. This
    should be the argument to an input driver in the yaml specification file.
   */
  CisInput(const char *name) : _pi(cisInput(name)) {}

  /*! @brief Empty constructor for inheritance. */
  CisInput(cisInput_t x) : _pi(x) {}

  /*!
    @brief Constructor for CisInput with format.
    @param[in] name constant character pointer to name of input queue. This
    should be the argument to an input driver in the yaml specification file.
    @param[in] fmt character pointer to format string for parsing messages.
   */
  CisInput(const char *name, char *fmt) : _pi(cisInputFmt(name, fmt)) {}

  void _destroy_pi() { cis_free(&_pi); }
  
  /*!
    @brief Destructor for CisInput.
    See cis_free in PsiInterface.h for details.
  */
  ~CisInput() { _destroy_pi(); }
  
  /*!
    @brief Return the cisInput_t structure.
    @return cisInput_t structure underlying the class.
  */
  cisInput_t pi() {
    return _pi;
  };

  /*!
    @brief Receive a message shorter than CIS_MSG_MAX from the input queue.
    See cis_recv in PsiInterface.h for additional details.
    @param[out] data character pointer to allocated buffer where the message
    should be saved.
    @param[in] len int length of the allocated message buffer in bytes.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv(char *data, const int len) { return cis_recv(_pi, data, len); }

  /*!
    @brief Receive and parse a message shorter than CIS_MSG_MAX from the input
    queue. See cisRecv from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv(const int nargs, ...) {
    // if (nargs != _pi._nfmt) {
    //   cislog_error("CisInput(%s).recv: %d args provided, but format expects %d.\n",
    // 		   _pi._name, nargs, _pi._nfmt);
    //   return -1;
    // }
    va_list va;
    va_start(va, nargs);
    int ret = vcisRecv(_pi, va);
    va_end(va);
    return ret;
  }
  
  /*!
    @brief Receive a message larger than CIS_MSG_MAX from the input queue.
    See cis_recv_nolimit in PsiInterface.h for additional details.
    @param[out] data character pointer to allocated buffer where the message
    should be saved.
    @param[in] len int length of the allocated message buffer in bytes.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv_nolimit(char **data, const int len) {
    return cis_recv_nolimit(_pi, data, len);
  }
  
  /*!
    @brief Receive and parse a message larger than CIS_MSG_MAX from the input
    queue. See cisRecv_nolimit from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv_nolimit(const int nargs, ...) {
    // if (nargs != _pi._nfmt) {
    //   cislog_error("CisInput(%s).recv: %d args provided, but format expects %d.\n",
    // 		   _pi._name, nargs, _pi._nfmt);
    //   return -1;
    // }
    va_list va;
    va_start(va, nargs);
    int ret = vcisRecv_nolimit(_pi, va);
    va_end(va);
    return ret;
  }
  
};


/*!
  @brief C++ interface to cisOutput_t functionality.

  The CisOutput class is a basic wrapper around the C cisOutput_t
  structure and associated functions from the PsiInterface.h header.
  It provides the user with C++ style access to basic output via
  an IPC queue.
 */
class CisOutput {
  cisOutput_t _pi;
public:
  
  /*!
    @brief Constructor for CisOutput.
    @param[in] name constant character pointer to name of output queue. This
    should be the argument to an output driver in the yaml specification file.
   */
  CisOutput(const char *name) : _pi(cisOutput(name)) {}
  
  /*!
    @brief Constructor for CisOutput with format.
    @param[in] name constant character pointer to name of output queue. This
    should be the argument to an output driver in the yaml specification file.
    @param[in] fmt character pointer to format string for formatting variables.
   */
  CisOutput(const char *name, char *fmt) : _pi(cisOutputFmt(name, fmt)) {}

  /*! @brief Empty constructor for inheritance. */
  CisOutput(cisOutput_t x) : _pi(x) {}
  
  void _destroy_pi() { cis_free(&_pi); }
  
  /*!
    @brief Destructor for CisOutput.
    See cis_free in PsiInterface.h for details.
  */
  ~CisOutput() { _destroy_pi(); }
  
  /*!
    @brief Return the cisOutput_t structure.
    @return cisOutput_t structure underlying the class.
  */
  cisOutput_t pi() {
    return _pi;
  };

  /*!
    @brief Send a message smaller than CIS_MSG_MAX to the output queue.
    If the message is larger than CIS_MSG_MAX an error code will be returned.
    See cis_send in PsiInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len int length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
  */
  int send(const char *data, const int len) {
    return cis_send(_pi, data, len);
  }

  /*!
    @brief Format and send a message smaller than CIS_MSG_MAX to the output
    queue. See cisSend from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send(const int nargs, ...) {
    // if (nargs != _pi._nfmt) {
    //   cislog_error("CisOutput(%s).send: %d args provided, but format expects %d.\n",
    // 		   _pi._name, nargs, _pi._nfmt);
    //   return -1;
    // }
    va_list va;
    va_start(va, nargs);
    int ret = vcisSend(_pi, va);
    va_end(va);
    return ret;
  }

  /*!
    @brief Send a message larger than CIS_MSG_MAX to the output queue.
    See cis_send_nolimit in PsiInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len int length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
  */
  int send_nolimit(const char *data, const int len) {
    return cis_send_nolimit(_pi, data, len);
  }
  
  /*!
    @brief Format and send a message larger than CIS_MSG_MAX to the output
    queue. See cisSend from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send_nolimit(const int nargs, ...) {
    // if (nargs != _pi._nfmt) {
    //   cislog_error("CisOutput(%s).send: %d args provided, but format expects %d.\n",
    // 		   _pi._name, nargs, _pi._nfmt);
    //   return -1;
    // }
    va_list va;
    va_start(va, nargs);
    int ret = vcisSend_nolimit(_pi, va);
    va_end(va);
    return ret;
  }

  /*!
    @brief Send EOF message to output file, closing it.
    @returns int 0 if send was succesfull. All other values indicate errors.
   */
  int send_eof() { return cis_send_eof(_pi); }
};
	

/*!
  @brief C++ interface to cisRpc_t functionality.

  The CisRpc class is a basic wrapper around the C cisRpc_t
  structure and associated functions from the PsiInterface.h header.
  It provides the user with C++ style access to basic RPC messaging via IPC
  queues.
 */
class CisRpc {
  cisRpc_t _pi;
public:

  /*!
    @brief Constructor for CisRpc.
    @param[in] outName constant character pointer name of the output queue.
    @param[in] outFormat character pointer to format that should be used for
    formatting output.
    @param[in] inName constant character pointer to name of the input queue.
    @param[in] inFormat character pointer to format that should be used for
    parsing input.
   */
  CisRpc(const char *name, char *outFormat, char *inFormat) :
    _pi(cisRpc(name, outFormat, inFormat)) {}

  /*! @brief Empty constructor for inheritance. */
  CisRpc(cisRpc_t x) : _pi(x) {}
  
  void _destroy_pi() { cis_free(&_pi); }
  
  /*!
    @brief Destructor for CisRpc.
    See cis_free in PsiInterface.h for details.
  */
  ~CisRpc() { _destroy_pi(); }
  
  /*!
    @brief Return the cisRpc_t structure.
    @return cisRpc_t structure underlying the class.
  */
  cisRpc_t pi() {
    return _pi;
  };

  /*!
    @brief Format and send a message to an RPC output queue.
    See rpcSend from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send(const int nargs, ...) {
    va_list va;
    va_start(va, nargs);
    int ret = vrpcSend(_pi, va);
    va_end(va);
    return ret;
  }

  /*!
    @brief Receive and parse a message from an RPC input queue. 
    See rpcRecv from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv(const int nargs, ...) {
    va_list va;
    va_start(va, nargs);
    int ret = vrpcRecv(_pi, va);
    va_end(va);
    return ret;
  }
};


/*!
  @brief C++ interface to cisRpc_t server-side functionality.
  The CisRpcServer class is a basic wrapper around the C cisRpc_t
  structure and associated server-side functions from the PsiInterface.h
  header. It provides the user with C++ style access to basic RPC server
  operations.
 */
class CisRpcServer : public CisRpc {
public:

  /*!
    @brief Constructor for CisRpcServer.
    @param[in] name constant character pointer name used for input and output
    queues.
    @param[in] inFormat character pointer to format that should be used for
    parsing input.
    @param[in] outFormat character pointer to format that should be used for
    formatting output.
   */
  CisRpcServer(const char *name, char *inFormat, char *outFormat) :
    CisRpc(cisRpcServer(name, inFormat, outFormat)) {}

  /*!
    @brief Destructor for CisRpcServer.
    See cis_free in PsiInterface.h for details.
  */
  ~CisRpcServer() { _destroy_pi(); }
  
};


/*!
  @brief C++ interface to cisRpc_t client-side functionality.
  The CisRpcClient class is a basic wrapper around the C cisRpc_t
  structure and associated client-side functions from the PsiInterface.h
  header. It provides the user with C++ style access to basic RPC client
  operations.
 */
class CisRpcClient : public CisRpc {
public:

  /*!
    @brief Constructor for CisRpcClient.
    @param[in] name constant character pointer name used for input and output
    queues.
    @param[in] outFormat character pointer to format that should be used for
    formatting output.
    @param[in] inFormat character pointer to format that should be used for
    parsing input.
   */
  CisRpcClient(const char *name, char *outFormat, char *inFormat) :
    CisRpc(cisRpcClient(name, outFormat, inFormat)) {}

  /*!
    @brief Destructor for CisRpcClient.
    See cis_free in PsiInterface.h for details.
  */
  ~CisRpcClient() { _destroy_pi(); }
  
  /*!
    @brief Send request to an RPC server from the client and wait for a
    response.
    See rpcCall in PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in,out] ... mixed arguments that include those that should be
    formatted using the output format string, followed by those that should be
    assigned parameters extracted using the input format string. These that will
    be assigned should be pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
  */
  int call(const int nargs, ...) {
    cisRpc_t _cpi = pi();
    va_list va;
    va_start(va, nargs);
    int ret = vrpcCall(_cpi, va);
    va_end(va);
    return ret;
  }
  
};


/*!
  @brief C++ interface to cisAsciiFileOutput_t functionality.
  The CisAsciiFileOutput class is a basic wrapper around the C
  cisAsciiFileOutput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII file output operations.
 */
class CisAsciiFileOutput : public CisOutput {
public:

  /*!
    @brief Constructor for CisAsciiFileOutput.
    @param[in] name constant character pointer to path of local file or name of
    an output queue.
    @param[in] dst_type int 0 if name refers to a local file, 1 if it is a
    queue.
   */
  CisAsciiFileOutput(const char *name, const int dst_type = 1) :
    CisOutput(cisAsciiFileOutput(name, dst_type)) {}
  
  /*! @brief Empty constructor for inheritance. */
  CisAsciiFileOutput(cisOutput_t x) :
    CisOutput(x) {}
  
  /*!
    @brief Send a single line to a file or queue.
    @param[in] line character pointer to line that should be sent.
    @returns int 0 if send was succesfull. All other values indicate errors.
   */
  int send_line(const char *line) { return send(line, strlen(line)); }

};


/*!
  @brief C++ interface to cisAsciiFileInput_t functionality.
  The CisAsciiFileInput class is a basic wrapper around the C
  cisAsciiFileInput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII file input operations.
 */
class CisAsciiFileInput : public CisInput {
public:

  /*!
    @brief Constructor for CisAsciiFileInput.
    @param[in] name constant character pointer to path of local file or name of
    an input queue.
    @param[in] src_type int 0 if name refers to a local file, 1 if it is a
    queue.
   */
  CisAsciiFileInput(const char *name, const int src_type = 1) :
    CisInput(cisAsciiFileInput(name, src_type)) {}

  /*! @brief Empty constructor for inheritance. */
  CisAsciiFileInput(cisInput_t x) :
    CisInput(x) {}
  
  /*!
    @brief Receive a single line from an associated file or queue.
    See af_recv_line in PsiInterface.h for details.
    @param[out] line character pointer to allocate memory where the received
    line should be stored.
    @param[in] n size_t Size of the allocated memory block in bytes.
    @returns int Number of bytes read/received. Negative values indicate that
    there was either an error or the EOF message was received.
   */
  int recv_line(char *line, const size_t n) { return recv(line, n); }
  
};


/*!
  @brief C++ interface to cisAsciiTableOutput_t functionality.

  The CisAsciiTableOutput class is a basic wrapper around the C
  cisAsciiTableOutput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII table output operations.
 */
class CisAsciiTableOutput : public CisAsciiFileOutput {
public:

  /*!
    @brief Constructor for CisAsciiTableOutput.
    @param[in] name constant character pointer to path of local table or name of
    an output queue.
    @param[in] format_str character pointer to format string that should be used
    to format rows into table lines.
    @param[in] as_array int 0 if send with variable arguments should send
    send elements from a single row, 1 if send with variable arguments should
    send columns from the entire table.
    @param[in] dst_type int 0 if name refers to a local table, 1 if it is a
    queue.
   */
  CisAsciiTableOutput(const char *name, const char *format_str,
		      const int as_array = 0, const int dst_type = 1) :
    CisAsciiFileOutput(cisAsciiTableOutput(name, format_str, as_array, dst_type)) {}

};


/*!
  @brief C++ interface to cisAsciiTableInput_t functionality.

  The CisAsciiTableInput class is a basic wrapper around the C
  cisAsciiTableInput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII table input operations.
 */
class CisAsciiTableInput : public CisAsciiFileInput {
public:

  /*!
    @brief Constructor for CisAsciiTableInput.
    Due to issues with the C++ version of vsscanf, flags and precision
    indicators for floating point format specifiers (e.g. %e, %f), must be
    removed so that table input can be properly parsed.
    @param[in] name constant character pointer to path of local table or name of
    an input queue.
    @param[in] as_array int 0 if recv with variable arguments should receive
    receive elements from a single row, 1 if recv with variable arguments should
    receive columns from the entire table.
    @param[in] src_type int 0 if name refers to a local table, 1 if it is a
    queue.
   */
  CisAsciiTableInput(const char *name, const int as_array = 0,
		     const int src_type = 1) :
    CisAsciiFileInput(cisAsciiTableInput(name, as_array, src_type)) {
    char *fmt = ((asciiTable_t*)(pi().serializer.info))->format_str;
    // For input, remove precision from floats to avoid confusing vsscanf
    // C version
    // int ret = simplify_formats(fmt, CIS_MSG_MAX);
    const char re[CIS_MSG_MAX] = "%([[:digit:]]+\\$)?[+-]?([ 0]|'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?([lhjztL])*([eEfFgG])";
    int ret = regex_replace_sub(fmt, CIS_MSG_MAX,
    				re, "%$4$5", 0);
    if (ret < 0)
      printf("CisAsciiTableInput(%s): could not fix format\n", name);

    // // C++ version, not consitent between libraries
    // std::regex e("%(?:\\d+\\$)?[+-]?(?:[ 0]|'.{1})?-?\\d*(?:\\.\\d+)?(?:[lhjztL])*([eEfFgG])");
    // std::string s(fmt, strlen(fmt));
    // std::string result;
    // std::string replace("%$1");
    // std::regex_replace(std::back_inserter(result), s.begin(), s.end(), e,
    // 		       replace);
    // strcpy(fmt, result.c_str());
  }

  // /*!
  //   @brief Recv a nolimit message from a table input queue.
  //   @param[in] data character pointer to pointer to memory where received
  //   message should be stored. It does not need to be allocated, only defined.
  //   @param[in] len int length of allocated buffer.
  //   @returns int -1 if message could not be received. Length of the received
  //   message if message was received.
  //  */
  // int recv(char **data, const int len) {
  //   return cis_recv_nolimit(_pi, data, len);
  // }
  
};

// Definitions for old style names
#define PsiInput CisInput
#define PsiOutput CisOutput
#define PsiRpc CisRpc
#define PsiRpcServer CisRpcServer
#define PsiRpcClient CisRpcClient
#define PsiAsciiFileInput CisAsciiFileInput
#define PsiAsciiFileOutput CisAsciiFileOutput
#define PsiAsciiTableInput CisAsciiTableInput
#define PsiAsciiTableOutput CisAsciiTableOutput

#endif /*CISINTERFACE_HPP_*/
