/*! @brief Flag for checking if CisInterface.hpp has already been included.*/
#ifndef CISINTERFACE_HPP_
#define CISINTERFACE_HPP_

#include "CisInterface.h"


/*!
  @brief C++ interface to cisInput_t functionality.

  The CisInput class is a basic wrapper around the C cisInput_t
  structure and associated functions from the CisInterface.h header.
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
  CisInput(const char *name, const char *fmt) : _pi(cisInputFmt(name, fmt)) {}

  /*!
    @brief Alias to allow freeing of underlying C struct at the class level.
  */
  void _destroy_pi() { cis_free(&_pi); }
  
  /*!
    @brief Destructor for CisInput.
    See cis_free in CisInterface.h for details.
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
    See cis_recv in CisInterface.h for additional details.
    @param[out] data character pointer to allocated buffer where the message
    should be saved.
    @param[in] len size_t length of the allocated message buffer in bytes.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv(char *data, const size_t len) { return cis_recv(_pi, data, len); }

  /*!
    @brief Receive and parse a message shorter than CIS_MSG_MAX from the input
    queue. See cisRecv from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv(const int nargs, ...) {
    size_t nargs_copy = (size_t)nargs;
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vcommRecv(_pi, 0, nargs_copy, va);
    va_end(va.va);
    return ret;
  }

  /*!
    @brief Receive and parse a message from the input queue, allowing destination
    variables to be reallocated. The pointers passed must be on heap.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recvRealloc(const int nargs, ...) {
    size_t nargs_copy = (size_t)nargs;
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vcommRecv(_pi, 1, nargs_copy, va);
    va_end(va.va);
    return ret;
  }
  
  /*!
    @brief Receive a message larger than CIS_MSG_MAX from the input queue.
    See cis_recv_nolimit in CisInterface.h for additional details.
    @param[out] data character pointer to allocated buffer where the message
    should be saved.
    @param[in] len size_t length of the allocated message buffer in bytes.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv_nolimit(char **data, const size_t len) {
    return cis_recv_nolimit(_pi, data, len);
  }
  
  /*!
    @brief Receive and parse a message larger than CIS_MSG_MAX from the input
    queue. See cisRecv from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv_nolimit(const int nargs, ...) {
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vcisRecv(_pi, 0, nargs, va);
    va_end(va.va);
    return ret;
  }
  
};


/*!
  @brief C++ interface to cisOutput_t functionality.

  The CisOutput class is a basic wrapper around the C cisOutput_t
  structure and associated functions from the CisInterface.h header.
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
  CisOutput(const char *name, const char *fmt) : _pi(cisOutputFmt(name, fmt)) {}

  /*! @brief Empty constructor for inheritance. */
  CisOutput(cisOutput_t x) : _pi(x) {}
  
  /*!
    @brief Alias to allow freeing of underlying C struct at the class level.
  */
  void _destroy_pi() { cis_free(&_pi); }
  
  /*!
    @brief Destructor for CisOutput.
    See cis_free in CisInterface.h for details.
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
    See cis_send in CisInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len size_t length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
  */
  int send(const char *data, const size_t len) {
    return cis_send(_pi, data, len);
  }

  /*!
    @brief Format and send a message smaller than CIS_MSG_MAX to the output
    queue. See cisSend from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send(const int nargs, ...) {
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vcisSend(_pi, nargs, va);
    va_end(va.va);
    return ret;
  }

  /*!
    @brief Send a message larger than CIS_MSG_MAX to the output queue.
    See cis_send_nolimit in CisInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len size_t length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
  */
  int send_nolimit(const char *data, const size_t len) {
    return cis_send_nolimit(_pi, data, len);
  }
  
  /*!
    @brief Format and send a message larger than CIS_MSG_MAX to the output
    queue. See cisSend from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send_nolimit(const int nargs, ...) {
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vcisSend(_pi, nargs, va);
    va_end(va.va);
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
  structure and associated functions from the CisInterface.h header.
  It provides the user with C++ style access to basic RPC messaging via IPC
  queues.
 */
class CisRpc {
  cisRpc_t _pi;
public:

  /*! @brief Empty constructor for inheritance. */
  CisRpc(cisRpc_t x) : _pi(x) {}
  
  /*!
    @brief Alias to allow freeing of underlying C struct at the class level.
  */
  void _destroy_pi() { cis_free(&_pi); }
  
  /*!
    @brief Destructor for CisRpc.
    See cis_free in CisInterface.h for details.
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
    See rpcSend from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send(const int nargs, ...) {
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vrpcSend(_pi, nargs, va);
    va_end(va.va);
    return ret;
  }

  /*!
    @brief Receive and parse a message from an RPC input queue. 
    See rpcRecv from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv(const int nargs, ...) {
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vrpcRecv(_pi, nargs, va);
    va_end(va.va);
    return ret;
  }

  /*!
    @brief Receive and parse a message from an RPC input queue, allowing
    destination memory to be reallocated as necessary.
    See rpcRecv from CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned and reallocated if
    they are not large enough, they should be references to pointer for heap
    memory that may or may not have already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recvRealloc(const int nargs, ...) {
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vrpcRecvRealloc(_pi, nargs, va);
    va_end(va.va);
    return ret;
  }
};


/*!
  @brief C++ interface to cisRpc_t server-side functionality.
  The CisRpcServer class is a basic wrapper around the C cisRpc_t
  structure and associated server-side functions from the CisInterface.h
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
  CisRpcServer(const char *name, const char *inFormat, const char *outFormat) :
    CisRpc(cisRpcServer(name, inFormat, outFormat)) {}

  /*!
    @brief Destructor for CisRpcServer.
    See cis_free in CisInterface.h for details.
  */
  ~CisRpcServer() { _destroy_pi(); }
  
};


/*!
  @brief C++ interface to cisRpc_t client-side functionality.
  The CisRpcClient class is a basic wrapper around the C cisRpc_t
  structure and associated client-side functions from the CisInterface.h
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
  CisRpcClient(const char *name, const char *outFormat, const char *inFormat) :
    CisRpc(cisRpcClient(name, outFormat, inFormat)) {}

  /*!
    @brief Destructor for CisRpcClient.
    See cis_free in CisInterface.h for details.
  */
  ~CisRpcClient() { _destroy_pi(); }
  
  /*!
    @brief Send request to an RPC server from the client and wait for a
    response, preserving the current sizes of memory at the provided output
    variable references.
    See rpcCall in CisInterface.h for details.
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
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vrpcCall(_cpi, nargs, va);
    va_end(va.va);
    return ret;
  }
  
  /*!
    @brief Send request to an RPC server from the client and wait for a
    response, allowing the memory pointed to by the pointers that the output
    variables reference to be reallocated.
    See rpcCall in CisInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in,out] ... mixed arguments that include those that should be
    formatted using the output format string, followed by those that should be
    assigned parameters extracted using the input format string. These that will
    be assigned should be references to pointers for heap memory that may or may
    not have already been allocated. These will be reallocated if they are not
    large enough to receive data from the incoming message.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
  */
  int callRealloc(const int nargs, ...) {
    cisRpc_t _cpi = pi();
    va_list_t va;
    va_start(va.va, nargs);
    int ret = vrpcCallRealloc(_cpi, nargs, va);
    va_end(va.va);
    return ret;
  }
  
};


/*!
  @brief C++ interface to cisAsciiFileOutput_t functionality.
  The CisAsciiFileOutput class is a basic wrapper around the C
  cisAsciiFileOutput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII file output operations.
 */
class CisAsciiFileOutput : public CisOutput {
public:

  /*!
    @brief Constructor for CisAsciiFileOutput.
    @param[in] name constant character pointer to the name of an output channel.
   */
  CisAsciiFileOutput(const char *name) :
    CisOutput(cisAsciiFileOutput(name)) {}
  
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
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII file input operations.
 */
class CisAsciiFileInput : public CisInput {
public:

  /*!
    @brief Constructor for CisAsciiFileInput.
    @param[in] name constant character pointer to the name of an input channel.
   */
  CisAsciiFileInput(const char *name) :
    CisInput(cisAsciiFileInput(name)) {}

  /*! @brief Empty constructor for inheritance. */
  CisAsciiFileInput(cisInput_t x) :
    CisInput(x) {}
  
  /*!
    @brief Receive a single line from an associated file or queue.
    See af_recv_line in CisInterface.h for details.
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
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII table output operations.
 */
class CisAsciiTableOutput : public CisAsciiFileOutput {
public:

  /*!
    @brief Constructor for CisAsciiTableOutput.
    @param[in] name constant character pointer to the name of an output channel.
    @param[in] format_str character pointer to format string that should be used
    to format rows into table lines.
   */
  CisAsciiTableOutput(const char *name, const char *format_str) :
    CisAsciiFileOutput(cisAsciiTableOutput(name, format_str)) {}

};


/*!
  @brief C++ interface to cisAsciiTableOutput_t functionality with arrays.

  The CisAsciiArrayOutput class is a basic wrapper around the C
  cisAsciiTableOutput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII table output operations.
 */
class CisAsciiArrayOutput : public CisAsciiFileOutput {
public:

  /*!
    @brief Constructor for CisAsciiArrayOutput.
    @param[in] name constant character pointer to the name of an output channel.
    @param[in] format_str character pointer to format string that should be used
    to format arrays into a table.
   */
  CisAsciiArrayOutput(const char *name, const char *format_str) :
    CisAsciiFileOutput(cisAsciiArrayOutput(name, format_str)) {}

};


/*!
  @brief C++ interface to cisAsciiTableInput_t functionality.

  The CisAsciiTableInput class is a basic wrapper around the C
  cisAsciiTableInput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII table input operations.
 */
class CisAsciiTableInput : public CisAsciiFileInput {
public:

  /*!
    @brief Constructor for CisAsciiTableInput.
    Due to issues with the C++ version of vsscanf, flags and precision
    indicators for floating point format specifiers (e.g. %e, %f), must be
    removed so that table input can be properly parsed.
    @param[in] name constant character pointer to the name of an input channel.
   */
  CisAsciiTableInput(const char *name) :
    CisAsciiFileInput(cisAsciiTableInput(name)) {}

};

/*!
  @brief C++ interface to cisAsciiTableInput_t functionality for arrays.

  The CisAsciiArrayInput class is a basic wrapper around the C
  cisAsciiTableInput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII table input operations.
 */
class CisAsciiArrayInput : public CisAsciiFileInput {
public:

  /*!
    @brief Constructor for CisAsciiArrayInput.
    Due to issues with the C++ version of vsscanf, flags and precision
    indicators for floating point format specifiers (e.g. %e, %f), must be
    removed so that table input can be properly parsed.
    @param[in] name constant character pointer to the name of an input channel.
   */
  CisAsciiArrayInput(const char *name) :
    CisAsciiFileInput(cisAsciiArrayInput(name)) {}

};


/*!
  @brief C++ interface to cisPlyOutput_t functionality.
  The CisPlyOutput class is a basic wrapper around the C
  cisPlyOutput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII file output operations.
 */
class CisPlyOutput : public CisOutput {
public:

  /*!
    @brief Constructor for CisPlyOutput.
    @param[in] name constant character pointer to the name of an output channel.
   */
  CisPlyOutput(const char *name) :
    CisOutput(cisPlyOutput(name)) {}
  
  /*! @brief Empty constructor for inheritance. */
  CisPlyOutput(cisOutput_t x) :
    CisOutput(x) {}
  
};


/*!
  @brief C++ interface to cisPlyInput_t functionality.
  The CisPlyInput class is a basic wrapper around the C
  cisPlyInput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII file input operations.
 */
class CisPlyInput : public CisInput {
public:

  /*!
    @brief Constructor for CisPlyInput.
    @param[in] name constant character pointer to the name of an input channel.
   */
  CisPlyInput(const char *name) :
    CisInput(cisPlyInput(name)) {}

  /*! @brief Empty constructor for inheritance. */
  CisPlyInput(cisInput_t x) :
    CisInput(x) {}
  
};


/*!
  @brief C++ interface to cisObjOutput_t functionality.
  The CisObjOutput class is a basic wrapper around the C
  cisObjOutput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII file output operations.
 */
class CisObjOutput : public CisOutput {
public:

  /*!
    @brief Constructor for CisObjOutput.
    @param[in] name constant character pointer to the name of an output channel.
   */
  CisObjOutput(const char *name) :
    CisOutput(cisObjOutput(name)) {}
  
  /*! @brief Empty constructor for inheritance. */
  CisObjOutput(cisOutput_t x) :
    CisOutput(x) {}
  
};


/*!
  @brief C++ interface to cisObjInput_t functionality.
  The CisObjInput class is a basic wrapper around the C
  cisObjInput_t structure and associated functions from the
  CisInterface.h header. It provides the user with C++ style access to basic
  ASCII file input operations.
 */
class CisObjInput : public CisInput {
public:

  /*!
    @brief Constructor for CisObjInput.
    @param[in] name constant character pointer to the name of an input channel.
   */
  CisObjInput(const char *name) :
    CisInput(cisObjInput(name)) {}

  /*! @brief Empty constructor for inheritance. */
  CisObjInput(cisInput_t x) :
    CisInput(x) {}
  
};


#endif /*CISINTERFACE_HPP_*/
