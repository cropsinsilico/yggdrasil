extern "C" {
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <stdlib.h>
#include "PsiInterface.h"
};


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

  int call(int fake_first = 0, ...) {
    va_list va;
    va_start(va, fake_first);
    int ret = vrpcCall(_pi, va);
    va_end(va);
    return ret;
  }
};


class PsiRpcClient : public PsiRpc {
public:
  psiRpc_t _pi;

  PsiRpcClient(const char *name, char *outFormat, char *inFormat) :
    PsiRpc(name, outFormat, name, inFormat) {}
  
};
