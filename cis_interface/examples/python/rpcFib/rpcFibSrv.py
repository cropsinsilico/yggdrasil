from __future__ import print_function
import os
import sys
import time
import logging
from logging import debug, info
from cis_interface.interface.PsiInterface import *
import socket


def fibServer(sleeptime):
    print('fibsrv(P): hello on system {} with sleep {}'.format(
        socket.gethostname(), sleeptime))

    rpc = PsiRpc("srv_fib", "%d %d", "srv_fib", "%d")

    while True:
        print('fibsrv(P): input<- ', end='')
        retval, rpc_in = rpc.rpcRecv()
        if not retval:
            print('rpcFibSrv: end of input')
            break

        #
        # compute fibonacci(input)
        #
        pprev = 0
        prev = 1
        result = 1
        fib_no = 1
        arg = rpc_in[0]
        while fib_no < arg:
            result = prev + pprev
            pprev = prev
            prev = result
            fib_no = fib_no+1
        print(' ::: ->(%2d %2d)' % (arg, result))

        time.sleep(float(sleeptime))
        rpc.rpcSend(arg, result)

    debug('fibsrv(P): bye')
    sys.exit(0)

if __name__ == '__main__':
    LOGLEVEL = logging.NOTSET
    if 'PSI_CLIENT_DEBUG' in os.environ:
        LOGLEVEL = getattr(logging, os.environ['PSI_CLIENT_DEBUG'])
    if 'RMQ_DrEBUG' in os.environ:
        RMQLOGLEVEL = getattr(logging, os.environ['RMQ_DEBUG'])
    logging.basicConfig(level=LOGLEVEL, stream=sys.stdout, \
	format=sys.argv[0].split('/')[-1]+': %(message)s')
    print('psirun', sys.argv)
    fibServer(sys.argv[1])
