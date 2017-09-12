from __future__ import print_function
import logging
import os
import sys
from cis_interface.interface.PsiInterface import PsiRpc


def fibClient(args):
    
    iterations = int(args[0])
    print('Hello from Python rpcFibCliPar: iterations = %d ' % iterations)

    # Create RPC connection with serover
    rpc = PsiRpc("cli_par_fib", "%d", "cli_par_fib", "%d %d")

    # Send all of the requests to the server
    for i in range(1, iterations + 1):
        print('Pfibcli(P): fib(->%-2d) ::: ' % i)
        ret = rpc.rpcSend(i)
        if not ret:
            print('SEND FAILED')
            sys.exit(-1)
    print('')

    # Receive responses for all requests that were sent
    for i in range(1, iterations + 1):
        retval, results = rpc.rpcRecv()
        if not retval:
            break
        print('Pfibcli(P):  fib(%2d<-) = %-2d<-' % (results))

    print('Goodbye from Python rpcFibCliPar')
    sys.exit(0)

    
if __name__ == '__main__':
    logLevel = logging.NOTSET
    if 'PSI_CLIENT_DEBUG' in os.environ:
        logLevel = getattr(logging, os.environ['PSI_CLIENT_DEBUG'])
    if 'RMQ_DEBUG' in os.environ:
        rmqLogLevel = getattr(logging, os.environ['RMQ_DEBUG'])
    logging.basicConfig(level=logLevel, stream=sys.stdout,
                        format=sys.argv[0].split('/')[-1] + ': %(message)s')
    fibClient(sys.argv[1:])
