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


class PsiInput {
  psiInput_t _pi;
public:
  
  PsiInput(const char *name) : _pi(psiInput(name)) {}
	
  int recv(char *data, int len) {
    return psi_recv(_pi, data, len);
  }

  int recv_nolimit(char **data, int len) {
    return psi_recv_nolimit(_pi, data, len);
  }
};


class PsiOutput {
public:
  psiOutput_t _pi;
  
  PsiOutput(const char *name) : _pi(psiOutput(name)) {}
  
  int send(char *data, int len) {
    return psi_send(_pi, data, len);
  }

  int send_nolimit(char *data, int len) {
    return psi_send_nolimit(_pi, data, len);
  }
};
	

class PsiRpc {
public:
  psiRpc_t _pi;

  PsiRpc(const char *outName, char *outFormat,
	 const char *inName, char *inFormat) :
    _pi(psiRpc(outName, outFormat, inName, inFormat)) {}

  // TODO: fix issue with fake_first, maybe macro
  int send(int fake_first = 0, ...) {
    va_list va;
    va_start(va, fake_first);
    int ret = vrpcSend(_pi, va);
    va_end(va);
    return ret;
  }

  int recv(int fake_first = 0, ...) {
    va_list va;
    va_start(va, fake_first);
    int ret = vrpcRecv(_pi, va);
    va_end(va);
    return ret;
  }
};


class PsiRpcServer : public PsiRpc {
public:
  psiRpc_t _pi;

  PsiRpcServer(const char *name, char *inFormat, char *outFormat) :
    PsiRpc(name, outFormat, name, inFormat) {}

};


class PsiRpcClient : public PsiRpc {
public:
  psiRpc_t _pi;

  PsiRpcClient(const char *name, char *outFormat, char *inFormat) :
    PsiRpc(name, outFormat, name, inFormat) {}
  
  int call(int fake_first = 0, ...) {
    va_list va;
    va_start(va, fake_first);
    int ret = vrpcCall(_pi, va);
    va_end(va);
    return ret;
  }
  
};


class PsiAsciiFileOutput {
public:
  psiAsciiFileOutput_t _pi;

  PsiAsciiFileOutput(const char *name, int dst_type = 1) :
    _pi(psiAsciiFileOutput(name, dst_type)) {}
  ~PsiAsciiFileOutput() { cleanup_pafo(&_pi); }

  int send_eof() { return af_send_eof(_pi); }
  int send_line(char *line) { return af_send_line(_pi, line); }
  
    
    

};


class PsiAsciiFileInput {
public:
  psiAsciiFileInput_t _pi;

  PsiAsciiFileInput(const char *name, int src_type = 1) :
    _pi(psiAsciiFileInput(name, src_type)) {}
  ~PsiAsciiFileInput() { cleanup_pafi(&_pi); }

  int recv_line(char *line, size_t n) { return af_recv_line(_pi, line, n); }
  
};


class PsiAsciiTableOutput {
public:
  psiAsciiTableOutput_t _pi;

  PsiAsciiTableOutput(const char *name, char *format_str, int dst_type = 1) :
    _pi(psiAsciiTableOutput(name, format_str, dst_type)) {}
  ~PsiAsciiTableOutput() { cleanup_pato(&_pi); }

  int send(char *data, int len) { return at_psi_send(_pi, data, len); }
  int send_eof() { return at_send_eof(_pi); }
  int send_row(int fake_first = 0, ...) {
    int ret;
    va_list ap;
    va_start(ap, fake_first);
    ret = vsend_row(_pi, ap);
    va_end(ap);
    return ret;
  }
  int send_array(int nrows, ...) {
    int ret;
    va_list ap;
    va_start(ap, nrows);
    ret = vsend_array(_pi, nrows, ap);
    va_end(ap);
    return ret;
  }

};


class PsiAsciiTableInput {
public:
  psiAsciiTableInput_t _pi;

  PsiAsciiTableInput(const char *name, int src_type = 1) :
    _pi(psiAsciiTableInput(name, src_type)) {
    // For input, remove precision from floats to avoid confusing vsscanf
    std::regex e("%(?:\\d+\\$)?[+-]?(?:[ 0]|'.{1})?-?\\d*(?:\\.\\d+)?(?:[lhjztL])*([eEfFgG])");
    std::string s(_pi._psi._fmt, strlen(_pi._psi._fmt));
    std::string result;
    std::regex_replace(std::back_inserter(result), s.begin(), s.end(), e, "%$1");
    strcpy(_pi._psi._fmt, result.c_str());
  }
  ~PsiAsciiTableInput() { cleanup_pati(&_pi); }

  int recv(char **data, int len) { return at_psi_recv(_pi, data, len); }
  int recv_row(int fake_first = 0, ...) {
    int ret;
    va_list ap;
    va_start(ap, fake_first);
    ret = vrecv_row(_pi, ap);
    va_end(ap);
    return ret;
  }
  int recv_array(int fake_first = 0, ...) {
    int ret;
    va_list ap;
    va_start(ap, fake_first);
    ret = vrecv_array(_pi, ap);
    va_end(ap);
    return ret;
  }
  
};
