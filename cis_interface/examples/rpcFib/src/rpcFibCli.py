from __future__ import print_function
import logging
import os
import sys
from cis_interface.interface.PsiInterface import (
    PsiRpc, PsiInput, PsiOutput)


def fibClient(args):
    
    iterations = int(args[0])
    print('Hello from Python rpcFibCli: iterations = %d ' % iterations)

    # Set up connections matching yaml
    ymlfile = PsiInput("yaml_in")
    rpc = PsiRpc("cli_fib", "%d", "cli_fib", "%d %d")
    log = PsiOutput("output_log")

    # Read entire contents of yaml
    flag, ycontent = ymlfile.recv()
    print('rpcFibCli: yaml has %d lines' % len('\n'.split(ycontent)))

    for i in range(1, iterations + 1):
        
        # Call the server and receive response
        print('rpcFibCli(P): fib(->%-2d) ::: ' % i, end='')
        idx, fib = rpc.rpcCall(i)
        if not idx:
            break

        # Log result by sending it to the log connection
        s = 'fib(%2d<-) = %-2d<-' % fib
        print(s)
        log.send(s + '\n')

    print('Goodbye from Python rpcFibCli')
    sys.exit(0)

    
if __name__ == '__main__':
    logLevel = logging.NOTSET
    if 'PSI_CLIENT_DEBUG' in os.environ:
        logLevel = getattr(logging, os.environ['PSI_CLIENT_DEBUG'])
    if 'RMQ_DEBUG' in os.environ:
        rmqLogLevel = getattr(logging, os.environ['RMQ_DEBUG'])
    logging.basicConfig(
        level=logLevel, stream=sys.stdout,
        format=sys.argv[0].split('/')[-1] + ': %(message)s')
    fibClient(sys.argv[1:])
