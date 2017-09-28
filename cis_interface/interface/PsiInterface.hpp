extern "C" {
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <stdlib.h>
#include "PsiInterface.h"
};
#include <string>
#include <regex>

/*! @brief Flag for checking if PsiInterface.hpp has already been included.*/
#ifndef PSIINTERFACE_HPP_
#define PSIINTERFACE_HPP_

/*!
  @brief C++ interface to psiInput_t functionality.

  The PsiInput class is a basic wrapper around the C psiInput_t
  structure and associated functions from the PsiInterface.h header.
  It provides the user with C++ style access to basic input via
  an IPC queue.
 */
class PsiInput {
  psiInput_t _pi;
public:

  /*!
    @brief Constructor for PsiInput.
    @param[in] name constant character pointer to name of input queue. This
    should be the argument to an input driver in the yaml specification file.
   */
  PsiInput(const char *name) : _pi(psiInput(name)) {}

  /*!
    @brief Constructor for PsiInput with format.
    @param[in] name constant character pointer to name of input queue. This
    should be the argument to an input driver in the yaml specification file.
    @param[in] fmt character pointer to format string for parsing messages.
   */
  PsiInput(const char *name, const char *fmt) : _pi(psiInputFmt(name, fmt)) {}

  /*!
    @brief Receive a message shorter than PSI_MSG_MAX from the input queue.
    See psi_recv in PsiInterface.h for additional details.
    @param[out] data character pointer to allocated buffer where the message
    should be saved.
    @param[in] len int length of the allocated message buffer in bytes.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv(char *data, const int len) {
    return psi_recv(_pi, data, len);
  }

  /*!
    @brief Receive and parse a message shorter than PSI_MSG_MAX from the input
    queue. See psiRecv from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv(const int nargs, ...) {
    if (nargs != _pi._nfmt) {
      psilog_error("PsiInput(%s).recv: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, _pi._nfmt);
      return -1;
    }
    va_list va;
    va_start(va, nargs);
    int ret = vpsiRecv(_pi, va);
    va_end(va);
    return ret;
  }
  
  /*!
    @brief Receive a message larger than PSI_MSG_MAX from the input queue.
    See psi_recv_nolimit in PsiInterface.h for additional details.
    @param[out] data character pointer to allocated buffer where the message
    should be saved.
    @param[in] len int length of the allocated message buffer in bytes.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv_nolimit(char **data, const int len) {
    return psi_recv_nolimit(_pi, data, len);
  }
  
  /*!
    @brief Receive and parse a message larger than PSI_MSG_MAX from the input
    queue. See psiRecv_nolimit from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[out] ... mixed arguments that should be assigned parameters extracted
    using the format string. Since these will be assigned, they should be
    pointers to memory that has already been allocated.
    @return integer specifying if the receive was succesful. Values >= 0
    indicate success.
   */
  int recv_nolimit(const int nargs, ...) {
    if (nargs != _pi._nfmt) {
      psilog_error("PsiInput(%s).recv: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, _pi._nfmt);
      return -1;
    }
    va_list va;
    va_start(va, nargs);
    int ret = vpsiRecv_nolimit(_pi, va);
    va_end(va);
    return ret;
  }
  
};


/*!
  @brief C++ interface to psiOutput_t functionality.

  The PsiOutput class is a basic wrapper around the C psiOutput_t
  structure and associated functions from the PsiInterface.h header.
  It provides the user with C++ style access to basic output via
  an IPC queue.
 */
class PsiOutput {
  psiOutput_t _pi;
public:
  
  /*!
    @brief Constructor for PsiOutput.
    @param[in] name constant character pointer to name of output queue. This
    should be the argument to an output driver in the yaml specification file.
   */
  PsiOutput(const char *name) : _pi(psiOutput(name)) {}
  
  /*!
    @brief Constructor for PsiOutput with format.
    @param[in] name constant character pointer to name of output queue. This
    should be the argument to an output driver in the yaml specification file.
    @param[in] fmt character pointer to format string for formatting variables.
   */
  PsiOutput(const char *name, const char *fmt) : _pi(psiOutputFmt(name, fmt)) {}

  /*!
    @brief Send a message smaller than PSI_MSG_MAX to the output queue.
    If the message is larger than PSI_MSG_MAX an error code will be returned.
    See psi_send in PsiInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len int length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
  */
  int send(const char *data, const int len) {
    return psi_send(_pi, data, len);
  }

  /*!
    @brief Format and send a message smaller than PSI_MSG_MAX to the output
    queue. See psiSend from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send(const int nargs, ...) {
    if (nargs != _pi._nfmt) {
      psilog_error("PsiOutput(%s).send: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, _pi._nfmt);
      return -1;
    }
    va_list va;
    va_start(va, nargs);
    int ret = vpsiSend(_pi, va);
    va_end(va);
    return ret;
  }

  /*!
    @brief Send a message larger than PSI_MSG_MAX to the output queue.
    See psi_send_nolimit in PsiInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len int length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
  */
  int send_nolimit(const char *data, const int len) {
    return psi_send_nolimit(_pi, data, len);
  }
  
  /*!
    @brief Format and send a message larger than PSI_MSG_MAX to the output
    queue. See psiSend from PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... arguments for formatting.  
    @return integer specifying if the send was succesful. Values >= 0 indicate
    success.
  */
  int send_nolimit(const int nargs, ...) {
    if (nargs != _pi._nfmt) {
      psilog_error("PsiOutput(%s).send: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, _pi._nfmt);
      return -1;
    }
    va_list va;
    va_start(va, nargs);
    int ret = vpsiSend_nolimit(_pi, va);
    va_end(va);
    return ret;
  }

};
	

/*!
  @brief C++ interface to psiRpc_t functionality.

  The PsiRpc class is a basic wrapper around the C psiRpc_t
  structure and associated functions from the PsiInterface.h header.
  It provides the user with C++ style access to basic RPC messaging via IPC
  queues.
 */
class PsiRpc {
  psiRpc_t _pi;
public:

  /*!
    @brief Constructor for PsiRpc.
    @param[in] outName constant character pointer name of the output queue.
    @param[in] outFormat character pointer to format that should be used for
    formatting output.
    @param[in] inName constant character pointer to name of the input queue.
    @param[in] inFormat character pointer to format that should be used for
    parsing input.
   */
  PsiRpc(const char *outName, const char *outFormat,
	 const char *inName, const char *inFormat) :
    _pi(psiRpc(outName, outFormat, inName, inFormat)) {}

  /*!
    @brief Return the psiRpc_t structure.
    @return psiRpc_t structure underlying the class.
  */
  psiRpc_t pi() {
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
    if (nargs != _pi._output._nfmt) {
      psilog_error("PsiRpc(%s).send: %d args provided, but format expects %d.\n",
		   _pi._output._name, nargs, _pi._output._nfmt);
      return -1;
    }
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
    if (nargs != _pi._input._nfmt) {
      psilog_error("PsiRpc(%s).recv: %d args provided, but format expects %d.\n",
		   _pi._input._name, nargs, _pi._input._nfmt);
      return -1;
    }
    va_list va;
    va_start(va, nargs);
    int ret = vrpcRecv(_pi, va);
    va_end(va);
    return ret;
  }
};


/*!
  @brief C++ interface to psiRpc_t server-side functionality.

  The PsiRpcServer class is a basic wrapper around the C psiRpc_t
  structure and associated server-side functions from the PsiInterface.h
  header. It provides the user with C++ style access to basic RPC server
  operations.
 */
class PsiRpcServer : public PsiRpc {
public:

  /*!
    @brief Constructor for PsiRpcServer.
    @param[in] name constant character pointer name used for input and output
    queues.
    @param[in] inFormat character pointer to format that should be used for
    parsing input.
    @param[in] outFormat character pointer to format that should be used for
    formatting output.
   */
  PsiRpcServer(const char *name, const char *inFormat, const char *outFormat) :
    PsiRpc(name, outFormat, name, inFormat) {}

};


/*!
  @brief C++ interface to psiRpc_t client-side functionality.

  The PsiRpcClient class is a basic wrapper around the C psiRpc_t
  structure and associated client-side functions from the PsiInterface.h
  header. It provides the user with C++ style access to basic RPC client
  operations.
 */
class PsiRpcClient : public PsiRpc {
public:

  /*!
    @brief Constructor for PsiRpcClient.
    @param[in] name constant character pointer name used for input and output
    queues.
    @param[in] outFormat character pointer to format that should be used for
    formatting output.
    @param[in] inFormat character pointer to format that should be used for
    parsing input.
   */
  PsiRpcClient(const char *name, const char *outFormat, const char *inFormat) :
    PsiRpc(name, outFormat, name, inFormat) {
  }

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
    psiRpc_t _cpi = pi();
    int nfmt_tot = _cpi._output._nfmt + _cpi._input._nfmt;
    if (nargs != nfmt_tot) {
      psilog_error("PsiRpcClient(%s).call: %d args provided, but format expects %d.\n",
		   _cpi._output._name, nargs, nfmt_tot);
      return -1;
    }
    va_list va;
    va_start(va, nargs);
    int ret = vrpcCall(_cpi, va);
    va_end(va);
    return ret;
  }
  
};


/*!
  @brief C++ interface to psiAsciiFileOutput_t functionality.

  The PsiAsciiFileOutput class is a basic wrapper around the C
  psiAsciiFileOutput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII file output operations.
 */
class PsiAsciiFileOutput {
  psiAsciiFileOutput_t _pi;
public:

  /*!
    @brief Constructor for PsiAsciiFileOutput.
    @param[in] name constant character pointer to path of local file or name of
    an output queue.
    @param[in] dst_type int 0 if name refers to a local file, 1 if it is a
    queue.
   */
  PsiAsciiFileOutput(const char *name, const int dst_type = 1) :
    _pi(psiAsciiFileOutput(name, dst_type)) {}
  /*!
    @brief Destructor for PsiAsciiFileOutput.
    See cleanup_pafo in PsiInterface.h for details.
  */
  ~PsiAsciiFileOutput() { cleanup_pafo(&_pi); }

  /*!
    @brief Send EOF message to output file, closing it.
    See af_send_eof in PsiInterface.h for details.
    @returns int 0 if send was succesfull. All other values indicate errors.
   */
  int send_eof() { return af_send_eof(_pi); }
  /*!
    @brief Send a single line to a file or queue.
    See af_send_line in PsiInterface.h for details.
    @param[in] line character pointer to line that should be sent.
    @returns int 0 if send was succesfull. All other values indicate errors.
   */
  int send_line(const char *line) { return af_send_line(_pi, line); }

};


/*!
  @brief C++ interface to psiAsciiFileInput_t functionality.

  The PsiAsciiFileInput class is a basic wrapper around the C
  psiAsciiFileInput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII file input operations.
 */
class PsiAsciiFileInput {
  psiAsciiFileInput_t _pi;
public:

  /*!
    @brief Constructor for PsiAsciiFileInput.
    @param[in] name constant character pointer to path of local file or name of
    an input queue.
    @param[in] src_type int 0 if name refers to a local file, 1 if it is a
    queue.
   */
  PsiAsciiFileInput(const char *name, const int src_type = 1) :
    _pi(psiAsciiFileInput(name, src_type)) {}
  /*!
    @brief Destructor for PsiAsciiFileInput.
    See cleanup_pafi in PsiInterface.h for details.
  */
  ~PsiAsciiFileInput() { cleanup_pafi(&_pi); }

  /*!
    @brief Receive a single line from an associated file or queue.
    See af_recv_line in PsiInterface.h for details.
    @param[out] line character pointer to allocate memory where the received
    line should be stored.
    @param[in] n size_t Size of the allocated memory block in bytes.
    @returns int Number of bytes read/received. Negative values indicate that
    there was either an error or the EOF message was received.
   */
  int recv_line(char *line, size_t n) { return af_recv_line(_pi, line, n); }
  
};


/*!
  @brief C++ interface to psiAsciiTableOutput_t functionality.

  The PsiAsciiTableOutput class is a basic wrapper around the C
  psiAsciiTableOutput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII table output operations.
 */
class PsiAsciiTableOutput {
  psiAsciiTableOutput_t _pi;
public:

  /*!
    @brief Constructor for PsiAsciiTableOutput.
    @param[in] name constant character pointer to path of local table or name of
    an output queue.
    @param[in] format_str character pointer to format string that should be used
    to format rows into table lines.
    @param[in] dst_type int 0 if name refers to a local table, 1 if it is a
    queue.
   */
  PsiAsciiTableOutput(const char *name, const char *format_str, const int dst_type = 1) :
    _pi(psiAsciiTableOutput(name, format_str, dst_type)) {}
  /*!
    @brief Destructor for PsiAsciiTableOutput.
    See cleanup_pato in PsiInterface.h for details.
  */
  ~PsiAsciiTableOutput() { cleanup_pato(&_pi); }

  /*!
    @brief Send a nolimit message to a table output queue.
    See at_psi_send in PsiInterface.h for details.
    @param[in] data character pointer to message that should be sent.
    @param[in] len int length of message to be sent.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
   */
  int send(const char *data, const int len) { return at_psi_send(_pi, data, len); }

  /*!
    @brief Send a nolimit EOF message to a table output queue.
    See at_send_eof in PsiInterface for details.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
   */
  int send_eof() { return at_send_eof(_pi); }

  /*!
    @brief Format and send a row to the table file/queue.
    See at_send_row in PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... Row elements that should be formatted.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
   */
  int send_row(const int nargs, ...) {
    int nfmt;
    if (_pi._type == 0)
      nfmt = count_formats(_pi._table.format_str);
    else
      nfmt = _pi._psi._nfmt;
    if (nargs != nfmt) {
      psilog_error("PsiAsciiTableOutput(%s).send_row: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, nfmt);
      return -1;
    }
    int ret;
    va_list ap;
    va_start(ap, nargs);
    ret = vsend_row(_pi, ap);
    va_end(ap);
    return ret;
  }

  /*!
    @brief Format and send table columns to the table file/queue.
    See at_send_array in PsiInterface.h for details. 
    @param[in] nargs int Number of arguments being passed.
    @param[in] nrows int Number of rows in the columns.
    @param[in] ... Pointers to memory containing table columns that
    should be formatted.
    @returns int 0 if send succesfull, -1 if send unsuccessful.
   */
  int send_array(const int nargs, const int nrows, ...) {
    int nfmt;
    if (_pi._type == 0)
      nfmt = count_formats(_pi._table.format_str);
    else
      nfmt = _pi._psi._nfmt;
    if (nargs != nfmt) {
      psilog_error("PsiAsciiTableOutput(%s).send_array: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, nfmt);
      return -1;
    }
    int ret;
    va_list ap;
    va_start(ap, nrows);
    ret = vsend_array(_pi, nrows, ap);
    va_end(ap);
    return ret;
  }

};


/*!
  @brief C++ interface to psiAsciiTableInput_t functionality.

  The PsiAsciiTableInput class is a basic wrapper around the C
  psiAsciiTableInput_t structure and associated functions from the
  PsiInterface.h header. It provides the user with C++ style access to basic
  ASCII table input operations.
 */
class PsiAsciiTableInput {
  psiAsciiTableInput_t _pi;
public:

  /*!
    @brief Constructor for PsiAsciiTableInput.
    Due to issues with the C++ version of vsscanf, flags and precision
    indicators for floating point format specifiers (e.g. %e, %f), must be
    removed so that table input can be properly parsed.
    @param[in] name constant character pointer to path of local table or name of
    an input queue.
    @param[in] src_type int 0 if name refers to a local table, 1 if it is a
    queue.
   */
  PsiAsciiTableInput(const char *name, const int src_type = 1) :
    _pi(psiAsciiTableInput(name, src_type)) {
    // For input, remove precision from floats to avoid confusing vsscanf
    // C version
    // int ret = simplify_formats(_pi._psi._fmt, PSI_MSG_MAX);
    const char re[PSI_MSG_MAX] = "%([[:digit:]]+\\$)?[+-]?([ 0]|'.{1})?-?[[:digit:]]*(\\.[[:digit:]]+)?([lhjztL])*([eEfFgG])";
    int ret = regex_replace_sub(_pi._psi._fmt, PSI_MSG_MAX,
    				re, "%$4$5", 0);
    if (ret < 0)
      printf("PsiAsciiTableInput(%s): could not fix format\n", name);

    // // C++ version, not consitent between libraries
    // std::regex e("%(?:\\d+\\$)?[+-]?(?:[ 0]|'.{1})?-?\\d*(?:\\.\\d+)?(?:[lhjztL])*([eEfFgG])");
    // std::string s(_pi._psi._fmt, strlen(_pi._psi._fmt));
    // std::string result;
    // std::string replace("%$1");
    // std::regex_replace(std::back_inserter(result), s.begin(), s.end(), e,
    // 		       replace);
    // strcpy(_pi._psi._fmt, result.c_str());
  }
  /*!
    @brief Destructor for PsiAsciiTableInput.
    See cleanup_pati in PsiInterface.h for details.
  */
  ~PsiAsciiTableInput() { cleanup_pati(&_pi); }

  /*!
    @brief Recv a nolimit message from a table input queue.
    See at_psi_recv in PsiInterface.h for details.
    @param[in] data character pointer to pointer to memory where received
    message should be stored. It does not need to be allocated, only defined.
    @param[in] len int length of allocated buffer.
    @returns int -1 if message could not be received. Length of the received
    message if message was received.
   */
  int recv(char **data, const int len) { return at_psi_recv(_pi, data, len); }

  /*!
    @brief Recv and parse a row from the table file/queue.
    See at_recv_row in PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... Pointers to memory where variables from the parsed row
    should be stored.
    @returns int -1 if message could not be received or parsed, otherwise the
    length of the received is returned.
   */
  int recv_row(const int nargs, ...) {
    int nfmt;
    if (_pi._type == 0)
      nfmt = count_formats(_pi._table.format_str);
    else
      nfmt = _pi._psi._nfmt;
    if (nargs != nfmt) {
      psilog_error("PsiAsciiTableInput(%s).recv_row: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, nfmt);
      return -1;
    }
    int ret;
    va_list ap;
    va_start(ap, nargs);
    ret = vrecv_row(_pi, ap);
    va_end(ap);
    return ret;
  }

  /*!
    @brief Recv and parse columns from a table file/queue.
    See at_recv_array in PsiInterface.h for details.
    @param[in] nargs int Number of arguments being passed.
    @param[in] ... Pointers to pointers to memory where columns from the
    parsed table should be stored. They need not be allocated, only declared.
    @returns int Number of rows received. Negative values indicate errors. 
   */
  int recv_array(const int nargs, ...) {
    int nfmt;
    if (_pi._type == 0)
      nfmt = count_formats(_pi._table.format_str);
    else
      nfmt = _pi._psi._nfmt;
    if (nargs != nfmt) {
      psilog_error("PsiAsciiTableInput(%s).recv_array: %d args provided, but format expects %d.\n",
		   _pi._name, nargs, nfmt);
      return -1;
    }
    int ret;
    va_list ap;
    va_start(ap, nargs);
    ret = vrecv_array(_pi, ap);
    va_end(ap);
    return ret;
  }
  
};

#endif /*PSIINTERFACE_HPP_*/
