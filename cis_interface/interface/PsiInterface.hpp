extern "C" {
#include <sys/stat.h>        /* For mode constants */
#include <sys/msg.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <stdlib.h>
#include "PsiInterface.h"
};

class PSi_Input {
	PsiInput _pi;
    public:

    PSi_Input(char * name) : _pi(psi_input(name)) {}
	
    int recv(char *data, int len){
	return psi_recv(_pi, data, len);
  	}
};

class PSi_Output {
	PsiOutput _pi;
    public:

    PSi_Output(char * name) : _pi(psi_output(name)) {}

    int send(char *data, int len){
	return psi_send(_pi, data, len);
  	}
};
	
